"""
modules/ai_provider.py
DeepSeek R1 via OpenRouter — modelos confirmados em Mai/2026
Autor: Alex Pel — github.com/alexpel
"""

import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    default_headers={
        "HTTP-Referer": "https://github.com/alexpel/job-apply-bot",
        "X-Title": "Job Apply Bot by Alex Pel",
    }
)

# Modelos confirmados grátis em Mai/2026
# Ordem = prioridade de fallback
MODELOS_FREE = [
    "deepseek/deepseek-r1:free",                  # R1 — melhor raciocínio
    "deepseek/deepseek-chat-v3.1:free",           # V3.1 — rápido
    "deepseek/deepseek-v4-flash:free",            # V4 Flash — mais novo
    "nvidia/nemotron-3-super-120b-a12b:free",     # NVIDIA — ótimo backup
    "meta-llama/llama-4-maverick:free",           # Llama 4 — fallback
    "openrouter/owl-alpha",                        # Owl — último recurso
]

_modelo_ativo = None  # cache do modelo que funcionou


def _chamar_api(prompt: str, system: str = "", modelo: str = None) -> str:
    """Chama a API tentando modelos em sequência até um funcionar."""
    global _modelo_ativo

    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    # Se já temos um modelo ativo, tenta ele primeiro
    fila = []
    if _modelo_ativo:
        fila = [_modelo_ativo] + [m for m in MODELOS_FREE if m != _modelo_ativo]
    elif modelo:
        fila = [modelo] + [m for m in MODELOS_FREE if m != modelo]
    else:
        fila = MODELOS_FREE

    for m in fila:
        try:
            r = client.chat.completions.create(
                model=m,
                messages=msgs,
                max_tokens=700,
                temperature=0.7,
            )
            _modelo_ativo = m  # salva o que funcionou
            return r.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if "404" in err or "No endpoints" in err or "not found" in err.lower():
                continue  # tenta o próximo
            raise  # erro diferente (auth, rate limit) — não tenta outros

    return ""  # todos falharam


def testar_conexao() -> bool:
    """Testa a conexão tentando todos os modelos até um funcionar."""
    global _modelo_ativo
    for modelo in MODELOS_FREE:
        try:
            r = client.chat.completions.create(
                model=modelo,
                messages=[{"role": "user", "content": "Responda apenas: OK"}],
                max_tokens=10,
            )
            texto = r.choices[0].message.content.strip()
            _modelo_ativo = modelo
            print(f"   ✅ Modelo ativo: {modelo}")
            return True
        except Exception as e:
            err = str(e)
            if "404" in err or "No endpoints" in err:
                print(f"   ⚠️  {modelo} indisponível, tentando próximo...")
                continue
            if "401" in err or "403" in err:
                print(f"   ❌ Chave inválida: {err}")
                return False
            continue
    print("   ❌ Nenhum modelo disponível no momento.")
    return False


def gerar_carta(vaga: dict, perfil: dict, modelo: str = None) -> str:
    """Gera carta de apresentação personalizada com DeepSeek R1."""
    system = """Você é especialista em RH e redação de cartas de apresentação.
Escreva cartas profissionais, objetivas e personalizadas em português brasileiro.
Máximo 250 palavras. Tom: profissional mas humano.
Não use clichês como 'venho por meio desta' ou 'prezado recrutador'.
Comece direto com sua proposta de valor."""

    skills = (
        perfil.get("skills", {}).get("languages", []) +
        perfil.get("skills", {}).get("backend", [])
    )

    prompt = f"""Escreva carta de apresentação para esta vaga:

VAGA:
- Título: {vaga.get('titulo', 'N/A')}
- Empresa: {vaga.get('empresa', 'N/A')}
- Local: {vaga.get('local', 'Remoto')}
- Descrição: {vaga.get('descricao', '')[:400]}

CANDIDATO:
- Nome: {perfil['personal']['name']}
- Resumo: {perfil.get('summary', '')[:300]}
- Skills: {', '.join(skills[:8])}
- GitHub: {perfil['personal'].get('github', '')}

Personalize para essa vaga e empresa específicas."""

    resultado = _chamar_api(prompt, system)
    if not resultado:
        nome  = perfil['personal']['name']
        title = vaga.get('titulo', 'a vaga')
        emp   = vaga.get('empresa', 'a empresa')
        sk    = ', '.join(skills[:4]) if skills else 'Python e desenvolvimento web'
        return (f"Olá! Sou {nome}, desenvolvedor com experiência em {sk}. "
                f"Tenho grande interesse na vaga de {title} na {emp} e "
                f"acredito que minhas habilidades agregam valor real ao time.")
    return resultado


def responder_pergunta(pergunta: str, perfil: dict) -> str:
    """Responde perguntas adicionais dos formulários."""
    skills = perfil.get("skills", {}).get("languages", [])
    prompt = f"""Responda essa pergunta de candidatura (máximo 2 frases, português):
Pergunta: {pergunta}
Candidato: {perfil['personal']['name']}, dev com skills em {', '.join(skills[:4])}"""

    resultado = _chamar_api(prompt)
    return resultado or "Tenho grande interesse nessa oportunidade e acredito que minha experiência agrega valor à equipe."
