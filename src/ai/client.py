"""
Cliente e gerenciador de autenticação para a API do Google Gemini.
Carrega a chave central da plataforma a partir dos Secrets do Streamlit Cloud,
variáveis de ambiente do sistema operacional ou arquivo .env local.
"""

import os
from pathlib import Path
from google import genai


def obter_chave_api() -> str | None:
    """
    Localiza a chave de API central da plataforma na seguinte ordem:
    1. st.secrets do Streamlit Community Cloud (servidor de produção na nuvem)
    2. Variáveis de ambiente (os.environ['GEMINI_API_KEY'])
    3. Arquivo .env na raiz do projeto (ambiente de desenvolvimento local)
    4. Tabela configuracoes_sistema no banco de dados (fallback compartilhado)
    """
    # 1. Verifica no st.secrets (Streamlit Community Cloud)
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            chave_sec = str(st.secrets["GEMINI_API_KEY"]).strip().strip('"').strip("'")
            if chave_sec:
                return chave_sec
    except Exception:
        pass

    # 2. Verifica nas variáveis de ambiente
    chave_env = os.environ.get("GEMINI_API_KEY", "").strip()
    if chave_env:
        return chave_env

    # 3. Verifica em arquivo .env na raiz do projeto
    env_path = Path(__file__).resolve().parent.parent.parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("GEMINI_API_KEY="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return val

    # 4. Fallback: Banco de Dados Turso (configurações globais centrais)
    try:
        from src.database.db import obter_configuracao_sistema
        chave_db = (obter_configuracao_sistema("GEMINI_API_KEY") or "").strip()
        if chave_db:
            return chave_db
    except Exception:
        pass

    return None


def tem_chave_configurada() -> bool:
    """Retorna True se uma chave válida da plataforma foi encontrada."""
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
