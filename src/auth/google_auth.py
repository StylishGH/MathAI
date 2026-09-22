"""
Módulo de Autenticação OAuth2 do Google para o MathAI.
Permite login social, extração de nome/e-mail e fluxo de onboarding para novos usuários.
"""

import urllib.parse
import requests
import os


def obter_credenciais_google():
    """Tenta obter GOOGLE_CLIENT_ID e GOOGLE_CLIENT_SECRET via os.environ, .env ou st.secrets."""
    client_id = os.environ.get("GOOGLE_CLIENT_ID")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

    if not client_id or not client_secret:
        try:
            import streamlit as st
            client_id = st.secrets.get("GOOGLE_CLIENT_ID") or client_id
            client_secret = st.secrets.get("GOOGLE_CLIENT_SECRET") or client_secret

            # Se configurado em seção [google]
            if "google" in st.secrets:
                sec = st.secrets["google"]
                client_id = sec.get("client_id") or sec.get("GOOGLE_CLIENT_ID") or client_id
                client_secret = sec.get("client_secret") or sec.get("GOOGLE_CLIENT_SECRET") or client_secret
        except Exception:
            pass

    if client_id:
        client_id = str(client_id).strip().strip('"').strip("'")
    if client_secret:
        client_secret = str(client_secret).strip().strip('"').strip("'")

    return client_id, client_secret


def gerar_url_auth_google(client_id: str, redirect_uri: str) -> str:
    """Gera o link de autorização do Google OAuth2."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "online",
        "prompt": "select_account"
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def trocar_codigo_por_usuario_google(code: str, client_id: str, client_secret: str, redirect_uri: str) -> dict | None:
    """
    Troca o authorization code temporário pelo access_token e busca o perfil do usuário no Google.
    Retorna dict com nome, email, picture e google_id ou None em caso de falha.
    """
    token_url = "https://oauth2.googleapis.com/token"
    payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    try:
        resp = requests.post(token_url, data=payload, timeout=10)
        if resp.status_code != 200:
            print(f"Erro ao trocar código Google: {resp.status_code} - {resp.text}")
            return None

        tokens = resp.json()
        access_token = tokens.get("access_token")
        if not access_token:
            return None

        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        resp_user = requests.get(userinfo_url, headers=headers, timeout=10)
        if resp_user.status_code != 200:
            return None

        info = resp_user.json()
        return {
            "google_id": info.get("id"),
            "email": (info.get("email") or "").lower().strip(),
            "nome": info.get("name") or info.get("given_name") or "Estudante",
            "picture": info.get("picture"),
            "verified_email": info.get("verified_email", True)
        }
    except Exception as e:
        print(f"Exceção ao autenticar com Google: {e}")
        return None
