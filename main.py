"""
main.py — Job Apply Bot
Orquestrador principal: LinkedIn + Glassdoor + Infojobs com DeepSeek R1
Autor: Alex Pel — github.com/alexpel
"""

import asyncio
import argparse
import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv

from modules.ai_provider import testar_conexao, _modelo_ativo
from modules.logger import banner, log, relatorio_final, mostrar_relatorio_csv
from modules.linkedin_bot  import rodar_linkedin
from modules.glassdoor_bot import rodar_glassdoor
from modules.infojobs_bot  import rodar_infojobs

load_dotenv()


def carregar_yaml(path: str) -> dict:
    p = Path(path)
    if not p.exists():
        log(f"Arquivo não encontrado: {path}", "error")
        sys.exit(1)
    with open(p, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def parse_args():
    parser = argparse.ArgumentParser(
        description="🤖 Job Apply Bot — Auto candidaturas com DeepSeek R1"
    )
    parser.add_argument(
        "--platform", "-p",
        choices=["linkedin", "glassdoor", "infojobs", "all"],
        default="all",
    )
    parser.add_argument("--dry-run", "-d", action="store_true")
    parser.add_argument("--report",  "-r", action="store_true")
    parser.add_argument("--profile",   default="config/profile.yaml")
    parser.add_argument("--settings",  default="config/settings.yaml")
    return parser.parse_args()


async def main():
    args = parse_args()
    banner()

    if args.report:
        mostrar_relatorio_csv()
        return

    perfil   = carregar_yaml(args.profile)
    settings = carregar_yaml(args.settings)

    if args.dry_run:
        log("MODO DRY-RUN — nenhuma candidatura será enviada", "warn")
        settings["bot"]["dry_run"] = True

    # Testa conexão com fallback automático
    log("Testando conexão com OpenRouter (DeepSeek R1)...", "info")
    if not testar_conexao():
        log("Nenhum modelo disponível. Verifique OPENROUTER_API_KEY no .env", "error")
        sys.exit(1)

    import modules.ai_provider as ai
    log(f"Modelo ativo: {ai._modelo_ativo}", "success")

    plataformas = settings.get("platforms", {})
    rodar = args.platform
    stats_total = {}

    if rodar in ("all", "linkedin") and plataformas.get("linkedin", True):
        log("━━━ LinkedIn ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        stats = await rodar_linkedin(perfil, settings)
        stats_total["LinkedIn"] = stats

    if rodar in ("all", "glassdoor") and plataformas.get("glassdoor", True):
        log("━━━ Glassdoor ━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        stats = await rodar_glassdoor(perfil, settings)
        stats_total["Glassdoor"] = stats

    if rodar in ("all", "infojobs") and plataformas.get("infojobs", True):
        log("━━━ Infojobs ━━━━━━━━━━━━━━━━━━━━━━━━━━━━", "info")
        stats = await rodar_infojobs(perfil, settings)
        stats_total["Infojobs"] = stats

    relatorio_final(stats_total)


if __name__ == "__main__":
    asyncio.run(main())
