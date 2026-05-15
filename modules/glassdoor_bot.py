"""
modules/glassdoor_bot.py — Login Manual + Auto Apply
Autor: Alex Pel — github.com/alexpel
"""

import asyncio, random, os, json
from pathlib import Path
from playwright.async_api import async_playwright
from modules.ai_provider import gerar_carta
from modules.logger import log, salvar_candidatura

SESSION_DIR = Path("data/sessions")
SESSION_DIR.mkdir(parents=True, exist_ok=True)
GD_SESSION  = SESSION_DIR / "glassdoor_session.json"

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
        await page.goto("https://www.glassdoor.com.br/member/home/index.htm",
                        wait_until="domcontentloaded", timeout=30000)
        await _delay(2, 1)
        return "login" not in page.url
    except Exception:
        return False

async def _login_manual(context, page):
    log("🔐 Abrindo Glassdoor para login manual...", "warn")
    await page.goto("https://www.glassdoor.com.br/profile/login_input.htm",
                    wait_until="domcontentloaded", timeout=60000)

    print("\n" + "="*50)
    print("  Faça login no Glassdoor no browser aberto.")
    print("  Depois pressione ENTER aqui para continuar.")
    print("="*50 + "\n")
    input(">>> Pressione ENTER após fazer login: ")

    await _salvar_sessao(context, GD_SESSION)
    log("Login Glassdoor OK — sessão salva", "success")
    return True

async def _buscar_vagas(page, keyword, filters):
    vagas = []
    try:
        url = f"https://www.glassdoor.com.br/Vagas/vagas.htm?sc.keyword={keyword.replace(' ','+')}"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await _delay(3, 2)

        # Fecha popup
        for sel in ['[alt="Close"]','button[data-test="modal-close"]','button[aria-label="Close"]']:
            try:
                btn = await page.query_selector(sel)
                if btn: await btn.click()
            except Exception: pass

        for _ in range(2):
            await page.keyboard.press("End")
            await _delay(1, 1)

        cards = await page.query_selector_all(
            '[data-test="jobListing"], .react-job-listing, [id^="job-listing"]'
        )
        log(f"{len(cards)} vagas Glassdoor para '{keyword}'", "search")

        for card in cards[:filters.get("max_applications", 25)]:
            try:
                titulo  = await card.query_selector('[data-test="job-title"], h2')
                empresa = await card.query_selector('[data-test="employer-name"]')
                local   = await card.query_selector('[data-test="emp-location"]')
                link    = await card.query_selector('a')
                href = ""
                if link:
                    href = await link.get_attribute("href") or ""
                    if href and not href.startswith("http"):
                        href = "https://www.glassdoor.com.br" + href
                vagas.append({
                    "titulo":  (await titulo.inner_text()).strip()  if titulo  else "N/A",
                    "empresa": (await empresa.inner_text()).strip() if empresa else "N/A",
                    "local":   (await local.inner_text()).strip()   if local   else "N/A",
                    "url": href, "descricao": "",
                })
            except Exception: continue
    except Exception as e:
        log(f"Erro busca Glassdoor: {e}", "error")
    return vagas

async def _aplicar_vaga(page, vaga, perfil, settings):
    dry_run = settings.get("bot",{}).get("dry_run", False)
    try:
        if vaga.get("url"):
            await page.goto(vaga["url"], wait_until="domcontentloaded", timeout=60000)
            await _delay(2, 2)

        btn = None
        for sel in [
            'button[data-test="easyApply"]',
            'button:has-text("Candidatura simplificada")',
            'button:has-text("Easy Apply")',
            'button:has-text("Candidatar")',
        ]:
            btn = await page.query_selector(sel)
            if btn: break

        if not btn:
            log(f"Sem Easy Apply Glassdoor: {vaga['titulo']}", "warn")
            return False

        if dry_run:
            log(f"[DRY-RUN] {vaga['titulo']} — {vaga['empresa']}", "info")
            return True

        await btn.click()
        await _delay(1, 1)

        carta = gerar_carta(vaga, perfil)

        for sel in ['textarea[name*="cover"]','textarea[placeholder*="carta"]']:
            campo = await page.query_selector(sel)
            if campo:
                await campo.fill(carta)
                break

        for _ in range(6):
            await _delay(0.8, 0.5)
            submit = await page.query_selector('button[data-test="submit-btn"]')
            nxt    = await page.query_selector('button[data-test="next-btn"]')
            if submit:
                await submit.click()
                await _delay(1, 1)
                log(f"✅ Enviada Glassdoor: {vaga['titulo']} — {vaga['empresa']}", "success")
                return True
            elif nxt: await nxt.click()
            else: break
        return False
    except Exception as e:
        log(f"Erro Glassdoor: {e}", "error")
        return False

async def rodar_glassdoor(perfil, settings):
    stats = {"enviadas":0,"erros":0,"ignoradas":0}
    blacklist = [e.lower() for e in settings.get("blacklist_companies",[])]
    max_apps  = settings["search"].get("max_applications", 25)

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

        log("Iniciando Glassdoor...", "info")

        logado = False
        if await _carregar_sessao(context, GD_SESSION):
            logado = await _verificar_logado(page)
            if logado:
                log("Sessão Glassdoor restaurada!", "success")

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
                    salvar_candidatura("glassdoor", vaga, "enviada")
                else:
                    stats["erros"] += 1
                    salvar_candidatura("glassdoor", vaga, "erro")
                await _delay(
                    settings.get("bot",{}).get("delay_between_apps",8),
                    settings.get("bot",{}).get("delay_random_extra",4),
                )

        await _salvar_sessao(context, GD_SESSION)
        await browser.close()
    return stats
