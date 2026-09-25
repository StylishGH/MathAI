"""
Cliente e gerenciador de autenticação para a API do Google Gemini.
Suporta chave via variável de ambiente, arquivo .env ou st.session_state no Streamlit.
"""

import os
from pathlib import Path
from google import genai


def obter_chave_api() -> str | None:
    """
    Tenta localizar a chave de API do Gemini em três lugares:
    1. No session_state do Streamlit (se digitado pelo usuário na barra lateral)
    2. Nas variáveis de ambiente do sistema operacional (os.environ)
    3. Em um arquivo .env na raiz do projeto
    """
    # 1. Verifica no Streamlit (st.session_state do usuário ou st.secrets na nuvem)
    try:
        import streamlit as st
        chave_sessao = st.session_state.get("gemini_api_key", "").strip()
        if chave_sessao:
            return chave_sessao
        if "GEMINI_API_KEY" in st.secrets:
            chave_sec = str(st.secrets["GEMINI_API_KEY"]).strip()
            if chave_sec:
                return chave_sec
    except Exception:
        pass

    # 2. Verifica nas variáveis de ambiente
    chave_env = os.environ.get("GEMINI_API_KEY", "").strip()
    if chave_env:
        return chave_env

    # 3. Verifica em arquivo .env na raiz
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                chave = line.split("=", 1)[1].strip().strip('"').strip("'")
                if chave:
                    return chave

    return None


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
