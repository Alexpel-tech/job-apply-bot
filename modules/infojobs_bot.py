"""
modules/infojobs_bot.py — Login Manual + Auto Apply
Autor: Alex Pel — github.com/alexpel
"""

import asyncio, random, os, json
from pathlib import Path
from playwright.async_api import async_playwright
from modules.ai_provider import gerar_carta, responder_pergunta
from modules.logger import log, salvar_candidatura

SESSION_DIR = Path("data/sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)
IJ_SESSION  = SESSION_DIR / "infojobs_session.json"

async def _delay(base=2, extra=3):
    await asyncio.sleep(base + random.uniform(0, extra))

async def _salvar_sessao(context, path):
    cookies = await context.cookies()
    path.write_text(json.dumps(cookies, ensure_ascii=False, indent=2))

async def _carregar_sessao(context, path):
    if not path.exists(): return False
    try:
        await context.add_cookies(json.loads(path.read_text()))
        return True
    except Exception:
        return False

async def _verificar_logado(page):
    try:
        await page.goto("https://www.infojobs.com.br/minha-conta",
                        wait_until="domcontentloaded", timeout=30000)
        await _delay(2, 1)
        return "login" not in page.url and "minha-conta" in page.url
    except Exception:
        return False

async def _login_manual(context, page):
    log("🔐 Abrindo Infojobs para login manual...", "warn")
    await page.goto("https://www.infojobs.com.br/login",
                    wait_until="domcontentloaded", timeout=60000)

    print("\n" + "="*50)
    print("  Faça login no Infojobs no browser aberto.")
    print("  Depois pressione ENTER aqui para continuar.")
    print("="*50 + "\n")
    input(">>> Pressione ENTER após fazer login: ")

    await _salvar_sessao(context, IJ_SESSION)
    log("Login Infojobs OK — sessão salva", "success")
    return True

async def _buscar_vagas(page, keyword, filters):
    vagas = []
    try:
        slug = keyword.lower().replace(" ","-")
        await page.goto(
            f"https://www.infojobs.com.br/empregos/{slug}",
            wait_until="domcontentloaded", timeout=60000
        )
        await _delay(3, 2)

        for _ in range(3):
            await page.keyboard.press("End")
            await _delay(1, 1)

        cards = await page.query_selector_all(
            ".ij-OfferCard, .offer-card, article[data-testid='offer-card'], [class*='OfferCard']"
        )
        log(f"{len(cards)} vagas Infojobs para '{keyword}'", "search")

        for card in cards[:filters.get("max_applications", 20)]:
            try:
                titulo  = await card.query_selector("h2, h3, [class*='title']")
                empresa = await card.query_selector("[class*='subtitle'],[class*='company'],[class*='employer']")
                local   = await card.query_selector("[class*='location'],[class*='local']")
                link    = await card.query_selector("a[href*='vaga'],a[href*='oferta'],a")
                href = ""
                if link:
                    href = await link.get_attribute("href") or ""
                    if href and not href.startswith("http"):
                        href = "https://www.infojobs.com.br" + href
                vagas.append({
                    "titulo":  (await titulo.inner_text()).strip()  if titulo  else "N/A",
                    "empresa": (await empresa.inner_text()).strip() if empresa else "N/A",
                    "local":   (await local.inner_text()).strip()   if local   else "N/A",
                    "url": href, "descricao": "",
                })
            except Exception: continue
    except Exception as e:
        log(f"Erro busca Infojobs: {e}", "error")
    return vagas

async def _aplicar_vaga(page, vaga, perfil, settings):
    dry_run = settings.get("bot",{}).get("dry_run", False)
    try:
        if not vaga.get("url"): return False
        await page.goto(vaga["url"], wait_until="domcontentloaded", timeout=60000)
        await _delay(2, 2)

        btn = None
        for sel in [
            'button:has-text("Candidatar")',
            'a:has-text("Candidatar")',
            'button:has-text("Me candidatar")',
            'button:has-text("Quero me candidatar")',
            '[data-testid="apply-button"]',
        ]:
            btn = await page.query_selector(sel)
            if btn: break

        if not btn:
            log(f"Botão não encontrado: {vaga['titulo']}", "warn")
            return False

        if dry_run:
            log(f"[DRY-RUN] {vaga['titulo']} — {vaga['empresa']}", "info")
            return True

        await btn.click()
        await _delay(2, 2)

        carta = gerar_carta(vaga, perfil)

        for sel in ['textarea[name*="cover"]','textarea[placeholder*="carta"]','textarea[placeholder*="apresent"]']:
            campo = await page.query_selector(sel)
            if campo:
                await campo.fill(carta)
                break

        inputs = await page.query_selector_all('input[type="text"][required],textarea[required]')
        for inp in inputs:
            if await inp.input_value(): continue
            lid = await inp.get_attribute("id") or ""
            lel = await page.query_selector(f'label[for="{lid}"]')
            if lel:
                ltxt = await lel.inner_text()
                if len(ltxt) > 5:
                    await inp.fill(responder_pergunta(ltxt, perfil))
                    await _delay(0.3, 0)

        for sel in [
            'button[type="submit"]',
            'button:has-text("Enviar candidatura")',
            'button:has-text("Confirmar")',
            'button:has-text("Finalizar")',
        ]:
            submit = await page.query_selector(sel)
            if submit:
                await submit.click()
                await _delay(2, 1)
                log(f"✅ Enviada Infojobs: {vaga['titulo']} — {vaga['empresa']}", "success")
                return True
        return False
    except Exception as e:
        log(f"Erro Infojobs: {e}", "error")
        return False

async def rodar_infojobs(perfil, settings):
    stats = {"enviadas":0,"erros":0,"ignoradas":0}
    blacklist = [e.lower() for e in settings.get("blacklist_companies",[])]
    max_apps  = settings["search"].get("max_applications", 20)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, slow_mo=200,
            args=["--no-sandbox","--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
            viewport={"width":1280,"height":800},
        )
        context.set_default_timeout(60000)
        page = await context.new_page()

        log("Iniciando Infojobs...", "info")

        logado = False
        if await _carregar_sessao(context, IJ_SESSION):
            logado = await _verificar_logado(page)
            if logado:
                log("Sessão Infojobs restaurada!", "success")

        if not logado:
            logado = await _login_manual(context, page)

        if not logado:
            await browser.close()
            return stats

        vistas = set()
        for keyword in settings["search"]["keywords"]:
            if stats["enviadas"] >= max_apps: break
            vagas = await _buscar_vagas(page, keyword, settings["search"])
            for vaga in vagas:
                if stats["enviadas"] >= max_apps: break
                chave = f"{vaga['empresa']}|{vaga['titulo']}"
                if chave in vistas: continue
                vistas.add(chave)
                if vaga["empresa"].lower() in blacklist:
                    stats["ignoradas"] += 1
                    continue
                ok = await _aplicar_vaga(page, vaga, perfil, settings)
                if ok:
                    stats["enviadas"] += 1
                    salvar_candidatura("infojobs", vaga, "enviada")
                else:
                    stats["erros"] += 1
                    salvar_candidatura("infojobs", vaga, "erro")
                await _delay(
                    settings.get("bot",{}).get("delay_between_apps",8),
                    settings.get("bot",{}).get("delay_random_extra",4),
                )

        await _salvar_sessao(context, IJ_SESSION)
        await browser.close()
    return stats
