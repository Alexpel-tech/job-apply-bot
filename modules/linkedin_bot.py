"""
modules/linkedin_bot.py — Login Manual + Auto Apply
Autor: Alex Pel — github.com/alexpel
"""

import asyncio, random, os, json
from pathlib import Path
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from modules.ai_provider import gerar_carta, responder_pergunta
from modules.logger import log, salvar_candidatura

SESSION_DIR = Path("data/sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)
LI_SESSION  = SESSION_DIR / "linkedin_session.json"

async def _delay(base=2, extra=3):
    await asyncio.sleep(base + random.uniform(0, extra))

async def _salvar_sessao(context, path):
    cookies = await context.cookies()
    path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))
    log(f"Sessão salva: {path}", "info")

async def _carregar_sessao(context, path):
    if not path.exists():
        return False
    try:
        cookies = json.loads(path.read_text())
        await context.add_cookies(cookies)
        return True
    except Exception:
        return False

async def _verificar_logado(page):
    """Verifica se já está logado no LinkedIn."""
    try:
        await page.goto("https://www.linkedin.com/feed/",
                        wait_until="domcontentloaded", timeout=30000)
        await _delay(2, 1)
        url = page.url
        return "feed" in url or "mynetwork" in url
    except Exception:
        return False

async def _login_manual(context, page):
    """Abre o browser para o usuário fazer login manualmente."""
    log("🔐 Abrindo LinkedIn para login manual...", "warn")
    log("   Faça login no browser que abriu e depois volte aqui.", "warn")

    await page.goto("https://www.linkedin.com/login",
                    wait_until="domcontentloaded", timeout=60000)

    print("\n" + "="*50)
    print("  Faça login no LinkedIn no browser aberto.")
    print("  Depois pressione ENTER aqui para continuar.")
    print("="*50 + "\n")
    input(">>> Pressione ENTER após fazer login: ")

    await _delay(2, 1)
    await _salvar_sessao(context, LI_SESSION)
    log("Login LinkedIn OK — sessão salva para próximas vezes", "success")
    return True

async def _buscar_vagas(page, keyword, location, filters):
    vagas = []
    try:
        date_map = {"day":"r86400","week":"r604800","month":"r2592000"}
        dp = date_map.get(filters.get("date_posted","month"), "r2592000")
        url = (
            f"https://www.linkedin.com/jobs/search/"
            f"?keywords={keyword.replace(' ','%20')}"
            f"&location={location.replace(' ','%20')}"
            f"&f_TPR={dp}&f_LF=f_AL"
        )
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await _delay(3, 2)

        for _ in range(3):
            await page.keyboard.press("End")
            await _delay(1, 1)

        cards = await page.query_selector_all(
            ".job-card-container, .jobs-search-results__list-item"
        )
        log(f"{len(cards)} vagas para '{keyword}'", "search")

        for card in cards[:filters.get("max_applications", 30)]:
            try:
                titulo  = await card.query_selector(".job-card-list__title, .job-card-container__link")
                empresa = await card.query_selector(".job-card-container__primary-description, .job-card-container__company-name")
                local   = await card.query_selector(".job-card-container__metadata-item")
                link    = await card.query_selector("a[href*='/jobs/view/']")
                href = ""
                if link:
                    href = (await link.get_attribute("href") or "").split("?")[0]
                vagas.append({
                    "titulo":  (await titulo.inner_text()).strip()  if titulo  else "N/A",
                    "empresa": (await empresa.inner_text()).strip() if empresa else "N/A",
                    "local":   (await local.inner_text()).strip()   if local   else "N/A",
                    "url": href, "descricao": "",
                })
            except Exception:
                continue
    except Exception as e:
        log(f"Erro busca: {e}", "error")
    return vagas

async def _aplicar_vaga(page, vaga, perfil, settings):
    dry_run = settings.get("bot", {}).get("dry_run", False)
    try:
        if vaga.get("url"):
            url = vaga["url"]
            if not url.startswith("http"):
                url = "https://www.linkedin.com" + url
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await _delay(2, 2)

        for sel in [".job-description",".jobs-description",".jobs-box__html-content"]:
            el = await page.query_selector(sel)
            if el:
                vaga["descricao"] = (await el.inner_text())[:600]
                break

        btn = None
        for sel in [
            'button.jobs-apply-button',
            'button[aria-label*="Easy Apply"]',
            'button[aria-label*="Candidatura simplificada"]',
            'button:has-text("Easy Apply")',
            'button:has-text("Candidatura simplificada")',
        ]:
            btn = await page.query_selector(sel)
            if btn: break

        if not btn:
            log(f"Sem Easy Apply: {vaga['titulo']}", "warn")
            return False

        if dry_run:
            log(f"[DRY-RUN] {vaga['titulo']} — {vaga['empresa']}", "info")
            return True

        await btn.click()
        await _delay(1, 1)

        log(f"🧠 Gerando carta: {vaga['titulo']}", "ai")
        carta = gerar_carta(vaga, perfil)

        for step in range(8):
            await _delay(0.5, 0.5)
            for sel in ['textarea[id*="cover"]','textarea[name*="cover"]','textarea[placeholder*="carta"]']:
                campo = await page.query_selector(sel)
                if campo and not await campo.input_value():
                    await campo.fill(carta)

            submit = await page.query_selector('button[aria-label="Submit application"]')
            review = await page.query_selector('button[aria-label="Review your application"]')
            nxt    = await page.query_selector('button[aria-label="Continue to next step"]')

            if submit:
                await submit.click()
                await _delay(1, 1)
                log(f"✅ Enviada: {vaga['titulo']} — {vaga['empresa']}", "success")
                return True
            elif review: await review.click()
            elif nxt:    await nxt.click()
            else: break

        return False
    except Exception as e:
        log(f"Erro: {e}", "error")
        return False

async def rodar_linkedin(perfil, settings):
    stats = {"enviadas":0,"erros":0,"ignoradas":0}
    blacklist = [e.lower() for e in settings.get("blacklist_companies",[])]
    max_apps  = settings["search"].get("max_applications", 30)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,  # sempre visível para login manual
            slow_mo=200,
            args=["--no-sandbox","--disable-dev-shm-usage","--start-maximized"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            viewport={"width":1280,"height":800},
        )
        context.set_default_timeout(60000)
        page = await context.new_page()

        log("Iniciando LinkedIn...", "info")

        # Tenta sessão salva primeiro
        logado = False
        if await _carregar_sessao(context, LI_SESSION):
            log("Sessão salva encontrada, verificando...", "info")
            logado = await _verificar_logado(page)
            if logado:
                log("Sessão LinkedIn restaurada — sem precisar de login!", "success")

        # Se não logou pela sessão, faz login manual
        if not logado:
            logado = await _login_manual(context, page)

        if not logado:
            await browser.close()
            return stats

        vistas = set()
        for keyword in settings["search"]["keywords"]:
            for location in settings["search"]["locations"]:
                if stats["enviadas"] >= max_apps: break
                vagas = await _buscar_vagas(page, keyword, location, settings["search"])
                for vaga in vagas:
                    if stats["enviadas"] >= max_apps: break
                    chave = f"{vaga['empresa']}|{vaga['titulo']}"
                    if chave in vistas:
                        stats["ignoradas"] += 1
                        continue
                    vistas.add(chave)
                    if vaga["empresa"].lower() in blacklist:
                        stats["ignoradas"] += 1
                        continue

                    log(f"[{stats['enviadas']+1}/{max_apps}] {vaga['titulo']} — {vaga['empresa']}", "info")
                    ok = await _aplicar_vaga(page, vaga, perfil, settings)
                    if ok:
                        stats["enviadas"] += 1
                        salvar_candidatura("linkedin", vaga, "enviada")
                    else:
                        stats["erros"] += 1
                        salvar_candidatura("linkedin", vaga, "erro")

                    await _delay(
                        settings.get("bot",{}).get("delay_between_apps",8),
                        settings.get("bot",{}).get("delay_random_extra",4),
                    )

        # Salva sessão atualizada
        await _salvar_sessao(context, LI_SESSION)
        await browser.close()

    log(f"LinkedIn: {stats['enviadas']} enviadas", "success")
    return stats
