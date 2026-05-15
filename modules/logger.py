"""
modules/logger.py
Sistema de logs, relatórios CSV e dashboard no terminal
Autor: Alex Pel — github.com/alexpel
"""

import csv
import os
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

console = Console()

LOG_DIR  = Path("logs")
DATA_DIR = Path("data")
LOG_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

CSV_FILE = DATA_DIR / "applied_jobs.csv"
LOG_FILE = LOG_DIR / f"session_{datetime.now().strftime('%Y-%m-%d')}.log"

CSV_HEADERS = ["data", "hora", "plataforma", "titulo", "empresa", "local", "status", "url"]


def _init_csv():
    if not CSV_FILE.exists():
        with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADERS)


def banner():
    console.print(Panel.fit(
        "[bold green]🤖 JOB APPLY BOT[/bold green]\n"
        "[cyan]DeepSeek R1 + Playwright[/cyan]\n"
        "[dim]by Alex Pel — github.com/alexpel[/dim]",
        border_style="green"
    ))


def log(msg: str, level: str = "info"):
    now = datetime.now().strftime("%H:%M:%S")
    icons = {"info": "📋", "success": "✅", "error": "❌", "warn": "⚠️", "ai": "🧠", "search": "🔍"}
    colors = {"info": "white", "success": "green", "error": "red", "warn": "yellow", "ai": "cyan", "search": "blue"}
    icon  = icons.get(level, "•")
    color = colors.get(level, "white")

    console.print(f"[dim][{now}][/dim] {icon} [{color}]{msg}[/{color}]")

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().isoformat()}] [{level.upper()}] {msg}\n")


def salvar_candidatura(plataforma: str, vaga: dict, status: str = "enviada"):
    _init_csv()
    now = datetime.now()
    with open(CSV_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            plataforma,
            vaga.get("titulo", ""),
            vaga.get("empresa", ""),
            vaga.get("local", ""),
            status,
            vaga.get("url", ""),
        ])


def relatorio_final(stats: dict):
    console.print("\n")
    table = Table(title="📊 Relatório Final", border_style="green", show_header=True)
    table.add_column("Plataforma", style="cyan", width=15)
    table.add_column("Enviadas",   style="green", justify="center")
    table.add_column("Erros",      style="red",   justify="center")
    table.add_column("Ignoradas",  style="yellow",justify="center")

    total_enviadas = 0
    for plataforma, data in stats.items():
        table.add_row(
            plataforma.capitalize(),
            str(data.get("enviadas", 0)),
            str(data.get("erros", 0)),
            str(data.get("ignoradas", 0)),
        )
        total_enviadas += data.get("enviadas", 0)

    console.print(table)
    console.print(f"\n[bold green]Total: {total_enviadas} candidaturas enviadas[/bold green]")
    console.print(f"[dim]Relatório salvo em: {CSV_FILE}[/dim]")
    console.print(f"[dim]Log completo em: {LOG_FILE}[/dim]\n")


def mostrar_relatorio_csv():
    """Lê o CSV e mostra um resumo bonito."""
    if not CSV_FILE.exists():
        console.print("[yellow]Nenhuma candidatura registrada ainda.[/yellow]")
        return

    import pandas as pd
    df = pd.read_csv(CSV_FILE)
    if df.empty:
        console.print("[yellow]CSV vazio.[/yellow]")
        return

    console.print(f"\n[bold]Total de candidaturas:[/bold] {len(df)}")
    console.print(f"[bold]Por plataforma:[/bold]")
    for plat, count in df["plataforma"].value_counts().items():
        console.print(f"  • {plat}: {count}")

    console.print(f"\n[bold]Últimas 5 candidaturas:[/bold]")
    table = Table(border_style="dim")
    for col in ["data", "empresa", "titulo", "plataforma", "status"]:
        table.add_column(col.capitalize())
    for _, row in df.tail(5).iterrows():
        table.add_row(str(row["data"]), row["empresa"], row["titulo"], row["plataforma"], row["status"])
    console.print(table)


def spinner(mensagem: str):
    return Progress(SpinnerColumn(), TextColumn(mensagem), transient=True)
