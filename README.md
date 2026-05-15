# 🤖 Job Apply Bot — Auto Candidaturas com DeepSeek R1

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Playwright](https://img.shields.io/badge/Playwright-Automation-2EAD33?style=for-the-badge&logo=playwright&logoColor=white)
![DeepSeek](https://img.shields.io/badge/DeepSeek-R1-FF6B6B?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**Bot de candidaturas automáticas com IA para LinkedIn, Glassdoor e Infojobs**  
*Gera cartas de apresentação personalizadas com DeepSeek R1 — 100% grátis*

</div>

---

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Como Usar](#-como-usar)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Plataformas Suportadas](#-plataformas-suportadas)
- [FAQ](#-faq)
- [Autor](#-autor)

---

## 🎯 Visão Geral

O **Job Apply Bot** automatiza o processo de candidatura em múltiplas plataformas de emprego usando Playwright para navegação e DeepSeek R1 via OpenRouter para geração de cartas de apresentação personalizadas por vaga.

```
Você configura uma vez → o bot aplica em centenas de vagas automaticamente
```

---

## ✨ Funcionalidades

- ✅ **Auto-login** no LinkedIn, Glassdoor e Infojobs
- ✅ **Busca por palavras-chave** e filtros configuráveis
- ✅ **Carta de apresentação única por vaga** gerada com DeepSeek R1
- ✅ **Preenchimento automático** de formulários
- ✅ **Blacklist de empresas** para evitar candidaturas indesejadas
- ✅ **Log completo** de todas as candidaturas realizadas
- ✅ **Rate limiting inteligente** para evitar detecção de bot
- ✅ **Dashboard em terminal** com progresso em tempo real
- ✅ **Relatório CSV** ao final de cada sessão
- ✅ **100% gratuito** — DeepSeek R1 via OpenRouter free tier

---

## 🏗️ Arquitetura

```
job-apply-bot/
├── main.py                  # Ponto de entrada — orquestra tudo
├── config/
│   ├── settings.yaml        # Configurações gerais
│   └── profile.yaml         # Seu perfil profissional
├── modules/
│   ├── ai_provider.py       # DeepSeek R1 via OpenRouter
│   ├── linkedin_bot.py      # Automação LinkedIn Easy Apply
│   ├── glassdoor_bot.py     # Automação Glassdoor Easy Apply
│   ├── infojobs_bot.py      # Automação Infojobs
│   └── logger.py            # Sistema de logs e relatórios
├── data/
│   ├── applied_jobs.csv     # Histórico de candidaturas
│   └── blacklist.txt        # Empresas a ignorar
├── logs/
│   └── session_YYYY-MM-DD.log
├── .env                     # Chaves de API (nunca commitar!)
├── .env.example             # Template das variáveis
├── requirements.txt
└── README.md
```

---

## 🚀 Instalação

### Pré-requisitos
- Python 3.10+
- Google Chrome instalado
- Conta no [OpenRouter](https://openrouter.ai) (grátis, sem cartão)

### Passo a passo

```bash
# 1. Clone o repositório
git clone https://github.com/alexpel/job-apply-bot
cd job-apply-bot

# 2. Crie o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 3. Instale as dependências
pip install -r requirements.txt

# 4. Instale o Chromium do Playwright
playwright install chromium

# 5. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas chaves e credenciais
```

---

## ⚙️ Configuração

### 1. Variáveis de Ambiente (`.env`)

```env
# ── DeepSeek R1 via OpenRouter (grátis) ──
OPENROUTER_API_KEY=sk-or-xxxxxxxxxxxxxxxxxxxx

# ── LinkedIn ──
LINKEDIN_EMAIL=seu@email.com
LINKEDIN_PASSWORD=sua_senha

# ── Glassdoor ──
GLASSDOOR_EMAIL=seu@email.com
GLASSDOOR_PASSWORD=sua_senha

# ── Infojobs ──
INFOJOBS_EMAIL=seu@email.com
INFOJOBS_PASSWORD=sua_senha
```

> 🔑 Chave OpenRouter grátis em: **openrouter.ai** → Create Account → API Keys

### 2. Seu Perfil (`config/profile.yaml`)

```yaml
personal:
  name: "Seu Nome"
  email: "seuemail@email.com"
  phone: "21XXXXXXXXX"
  city: "Sua Cidade"
  state: "Seu Estado"
  linkedin: "linkedin.com/in/"
  github: "github.com/alexpel"

summary: >
  Desenvolvedor Full Stack com experiência em Python, FastAPI, React e Node.js.
  Especialista em automação, integração de APIs e desenvolvimento de sistemas SaaS.
  Apaixonado por resolver problemas reais com tecnologia.

experience:
  - title: "Desenvolvedor Full Stack"
    company: "Autônomo / Freelancer"
    period: "2023 - atual"
    description: >
      Desenvolvimento de sistemas CRM (AtendIA Pro), bots de automação,
      integração com APIs Meta (WhatsApp/Instagram), e plataformas SaaS white-label.

skills:
  languages: ["Python", "JavaScript", "TypeScript"]
  backend: ["FastAPI", "Node.js", "Express"]
  frontend: ["React", "HTML", "CSS", "Tailwind"]
  databases: ["PostgreSQL", "SQLite", "MongoDB"]
  tools: ["Docker", "Git", "Playwright", "Selenium"]
  ai: ["DeepSeek R1", "Gemini", "OpenAI API", "LangChain"]

education:
  - degree: "Análise e Desenvolvimento de Sistemas"
    institution: "Estácio de Sá"
    status: "Em andamento"

languages:
  - language: "Português"
    level: "Nativo"
  - language: "Inglês"
    level: "Intermediário"
```

### 3. Configurações de Busca (`config/settings.yaml`)

```yaml
search:
  keywords:
    - "Desenvolvedor Python"
    - "Python Developer"
    - "Full Stack Developer"
    - "Backend Developer"
    - "FastAPI Developer"
  locations:
    - "Brasil"
    - "Remote"
    - "Remoto"
  remote_only: false
  experience_levels:
    - "entry"
    - "mid"
  job_types:
    - "full_time"
    - "contract"
  date_posted: "month"       # day | week | month
  max_applications: 50       # por sessão por plataforma

blacklist_companies:
  - "Empresa Ruim Ltda"
  - "MLM Corp"

blacklist_keywords:
  - "comissão"
  - "vendas externas"
  - "porta a porta"

ai:
  model: "deepseek/deepseek-r1:free"
  cover_letter_language: "pt-BR"
  max_letter_words: 250

bot:
  headless: false            # true = roda sem abrir janela
  slow_mo: 500               # ms entre ações (evita detecção)
  delay_between_apps: 8      # segundos entre candidaturas
  delay_random_extra: 5      # segundos aleatórios extras

platforms:
  linkedin: true
  glassdoor: true
  infojobs: true
```

---

## 🎮 Como Usar

```bash
# Rodar em todas as plataformas
python main.py

# Só LinkedIn
python main.py --platform linkedin

# Só Glassdoor
python main.py --platform glassdoor

# Só Infojobs
python main.py --platform infojobs

# Modo teste (não aplica de verdade, só simula)
python main.py --dry-run

# Ver relatório do dia
python main.py --report
```

### Output esperado no terminal:

```
╔══════════════════════════════════════════╗
║     🤖 JOB APPLY BOT — by Alex Pel      ║
║         DeepSeek R1 + Playwright         ║
╚══════════════════════════════════════════╝

[14:23:01] 🔐 Fazendo login no LinkedIn...
[14:23:05] ✅ Login OK — Alex Pel
[14:23:06] 🔍 Buscando: "Desenvolvedor Python" em "Brasil"
[14:23:09] 📋 47 vagas encontradas

[14:23:12] 📝 Vaga 1/47: Python Developer — Nubank (São Paulo)
[14:23:12] 🧠 Gerando carta com DeepSeek R1...
[14:23:15] ✅ Candidatura enviada!

[14:23:23] 📝 Vaga 2/47: Backend Dev — iFood (Remoto)
[14:23:23] 🧠 Gerando carta com DeepSeek R1...
[14:23:27] ✅ Candidatura enviada!

...

[15:45:00] 📊 RELATÓRIO FINAL
           LinkedIn:  38 candidaturas ✅
           Glassdoor: 22 candidaturas ✅
           Infojobs:  15 candidaturas ✅
           Total:     75 candidaturas em 1h22min
           Salvo em:  data/applied_jobs.csv
```

---

## 🌐 Plataformas Suportadas

| Plataforma | Login | Busca | Easy Apply | Carta IA | Status |
|---|---|---|---|---|---|
| LinkedIn | ✅ | ✅ | ✅ | ✅ | **Estável** |
| Glassdoor | ✅ | ✅ | ✅ | ✅ | **Estável** |
| Infojobs | ✅ | ✅ | ✅ | ✅ | **Beta** |

---

## ❓ FAQ

**Q: O bot pode banir minha conta?**  
A: O bot usa delays aleatórios e simula comportamento humano. Recomendamos no máximo 50 candidaturas/dia por plataforma.

**Q: Precisa pagar algo?**  
A: Não. DeepSeek R1 via OpenRouter tem um free tier generoso. Playwright e Python são grátis.

**Q: Funciona no Windows?**  
A: Sim, testado no Windows 10/11 e Ubuntu 22.

**Q: As senhas ficam salvas onde?**  
A: Apenas no arquivo `.env` local, que nunca é commitado no Git.

---

## 📄 Licença

MIT License — livre para usar, modificar e distribuir.

---

## 👤 Autor

<div align="center">

**Alex Pel**  
Desenvolvedor Full Stack & Empreendedor  
Duque de Caxias, Rio de Janeiro 🇧🇷

[![GitHub](https://img.shields.io/badge/GitHub-alexpel-181717?style=for-the-badge&logo=github)](https://github.com/alexpel)
[![Threads](https://img.shields.io/badge/Threads-@alexpel__-000000?style=for-the-badge&logo=threads)](https://threads.net/@alexpel_)

*Construído com 🤖 DeepSeek R1 + ☕ muito café*

</div>
