"""
Cliente e gerenciador de autenticação para a API do Google Gemini.
Suporta chave via perfil do usuário (Banco de Dados), st.session_state, .env ou st.secrets.
"""

import os
import time
from pathlib import Path
from google import genai


def obter_chave_api() -> str | None:
    """
    Tenta localizar a chave de API do Gemini seguindo a seguinte ordem de prioridade:
    1. Chave explícita na sessão ativa do Streamlit (st.session_state['gemini_api_key'])
    2. Chave vinculada ao perfil do usuário no Banco de Dados (usuario_logado['gemini_api_key'])
    3. Variáveis de ambiente do sistema operacional (os.environ['GEMINI_API_KEY'])
    4. Arquivo .env na raiz do projeto (desenvolvimento local)
    5. st.secrets do Streamlit Community Cloud (servidor de deploy)
    """
    # 1. Verifica na sessão Streamlit
    try:
        import streamlit as st
        chave_sessao = st.session_state.get("gemini_api_key", "").strip()
        if chave_sessao:
            return chave_sessao

        # 2. Verifica no perfil do usuário logado (persistido no banco de dados)
        user = st.session_state.get("usuario_logado")
        if isinstance(user, dict):
            chave_user = (user.get("gemini_api_key") or "").strip()
            if chave_user:
                return chave_user
    except Exception:
        pass

    # 3. Verifica nas variáveis de ambiente
    chave_env = os.environ.get("GEMINI_API_KEY", "").strip()
    if chave_env:
        return chave_env

    # 4. Verifica em arquivo .env na raiz do projeto
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                chave = line.split("=", 1)[1].strip().strip('"').strip("'")
                if chave:
                    return chave

    # 5. Verifica no st.secrets (Streamlit Community Cloud)
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            chave_sec = str(st.secrets["GEMINI_API_KEY"]).strip()
            if chave_sec:
                return chave_sec
    except Exception:
        pass

    return None


def obter_info_chave() -> dict:
    """
    Retorna metadados descritivos sobre a chave de API em uso e sua origem.
    Útil para auditoria e exibição transparente na interface do usuário.
    """
    chave = None
    origem = "nenhuma"

    try:
        import streamlit as st
        if st.session_state.get("gemini_api_key", "").strip():
            chave = st.session_state.get("gemini_api_key", "").strip()
            origem = "Sessão Atual (Personalizada)"
        elif isinstance(st.session_state.get("usuario_logado"), dict) and (st.session_state.get("usuario_logado").get("gemini_api_key") or "").strip():
            chave = st.session_state.get("usuario_logado").get("gemini_api_key").strip()
            origem = "Perfil do Usuário (Banco de Dados)"
    except Exception:
        pass

    if not chave:
        chave_env = os.environ.get("GEMINI_API_KEY", "").strip()
        if chave_env:
            chave = chave_env
            origem = "Variável de Ambiente (OS)"

    if not chave:
        env_path = Path(__file__).resolve().parent.parent.parent / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("GEMINI_API_KEY="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    if val:
                        chave = val
                        origem = "Arquivo Local (.env)"
                        break

    if not chave:
        try:
            import streamlit as st
            if "GEMINI_API_KEY" in st.secrets:
                val = str(st.secrets["GEMINI_API_KEY"]).strip()
                if val:
                    chave = val
                    origem = "Streamlit Secrets (Nuvem)"
        except Exception:
            pass

    mascarada = "Não configurada"
    if chave:
        if len(chave) > 12:
            mascarada = f"{chave[:6]}...{chave[-4:]}"
        else:
            mascarada = f"{chave[:3]}..."

    return {
        "chave": chave,
        "origem": origem,
        "mascarada": mascarada,
        "presente": bool(chave)
    }


def tem_chave_configurada() -> bool:
    """Retorna True se uma chave válida foi encontrada."""
    return obter_chave_api() is not None


def criar_cliente_gemini() -> genai.Client | None:
    """
    Cria e retorna a instância oficial do Client da SDK google-genai.
    Retorna None se nenhuma chave estiver configurada.
    """
    chave = obter_chave_api()
    if not chave:
        return None
    return genai.Client(api_key=chave)


def testar_chave_api(chave: str | None = None) -> dict:
    """
    Testa a conectividade da chave contra o modelo gemini-flash-lite-latest.
    Retorna diagnóstico detalhado em caso de falha (402, 429, 503, etc.).
    """
    chave_final = chave.strip() if (chave and chave.strip()) else obter_chave_api()
    if not chave_final:
        return {
            "ok": False,
            "codigo": 401,
            "erro": "Nenhuma chave de API foi fornecida ou configurada."
        }

    try:
        t0 = time.time()
        c = genai.Client(api_key=chave_final)
        resp = c.models.generate_content(
            model="gemini-flash-lite-latest",
            contents="Diga OK em uma palavra"
        )
        tempo_ms = int((time.time() - t0) * 1000)
        return {
            "ok": True,
            "modelo": "gemini-flash-lite-latest",
            "tempo_ms": tempo_ms,
            "resposta": (resp.text or "").strip()
        }
    except Exception as e:
        erro_str = str(e)
        codigo = None
        if "402" in erro_str or "prepayment credits are depleted" in erro_str.lower():
            codigo = 402
            msg = (
                "⚠️ **Créditos Esgotados (Erro 402)**: Esta chave pertence a um projeto do Google Cloud com faturamento ativado (Pay-as-you-go) "
                "cujo saldo pré-pago está zerado ($0.00). O Google bloqueia o Free Tier nesse projeto. "
                "Para resolver sem gastar nada: crie uma chave em um projeto novo sem faturamento em ai.studio/apikey (Free Tier)."
            )
        elif "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str:
            codigo = 429
            msg = "⏳ **Cota Temporária (Erro 429)**: Limite de requisições por minuto atingido. Aguarde 30 a 60 segundos."
        elif "404" in erro_str:
            codigo = 404
            msg = "❌ **Não Encontrado (Erro 404)**: Chave de API inválida ou sem permissão de acesso aos modelos Gemini."
        elif "503" in erro_str:
            codigo = 503
            msg = "⚙️ **Servidores Sobrecarregados (Erro 503)**: Os servidores do Google estão temporariamente com pico de demanda."
        else:
            msg = f"Falha na comunicação: {erro_str}"

        return {
            "ok": False,
            "codigo": codigo,
            "erro": msg
        }
