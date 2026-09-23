"""
MathAI - Aplicação Principal (Streamlit)
Fase 1 (V1) - Plataforma Cognitiva de Resolução, Metacognição e Perfil do Estudante.
Layout: Header com Logo e Conta no Topo, Navegação em 3 Colunas Largas, Modo Dark/Light, Dourado Realçado.
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import streamlit as st

# 1. Configuração da Página
st.set_page_config(
    page_title="MathAI — Plataforma Cognitiva de Matemática",
    page_icon="📐",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Inicialização e Persistência do Tema (Dark / Light)
tema_url = st.query_params.get("theme")
if tema_url in ("dark", "light"):
    st.session_state.tema = tema_url
elif "tema" not in st.session_state:
    st.session_state.tema = "dark"

is_dark = (st.session_state.tema == "dark")

# Cores do Sistema
bg_page = "#0a0a0f" if is_dark else "#f8fafc"
card_bg = "rgba(19, 17, 28, 0.92)" if is_dark else "#ffffff"
card_border = "rgba(124, 58, 237, 0.35)" if is_dark else "rgba(124, 58, 237, 0.2)"
text_main = "#f8fafc" if is_dark else "#0f172a"
text_muted = "#94a3b8" if is_dark else "#64748b"
gold_accent = "#fbbf24"
gold_border = "#f59e0b"

# 3. CSS Global Dinâmico
if not is_dark:
    theme_css = """
    :root {
        --background-color: #f8fafc !important;
        --secondary-background-color: #ffffff !important;
        --text-color: #0f172a !important;
    }
    html, body, .stApp,
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewBlockContainer"],
    [data-testid="stMainBlockContainer"],
    .main, section.main {
        background-color: #f8fafc !important;
        color: #0f172a !important;
    }
    /* Sobrescrever o tema nativo dark do config.toml */
    [data-testid="stVerticalBlock"],
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stHorizontalBlock"] {
        background-color: transparent !important;
    }
    p, span, label, div[data-testid="stMarkdownContainer"] p, div[data-testid="stText"] {
        color: #0f172a !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #64748b !important;
    }
    input, textarea, [data-baseweb="select"] > div, [data-baseweb="base-input"], div[data-baseweb="input"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
    }
    div[data-baseweb="popover"] > div {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
    }
    div[data-baseweb="popover"], div[role="listbox"], ul[role="listbox"] {
        color: #0f172a !important;
    }
    li[role="option"], div[role="option"] {
        color: #0f172a !important;
        background-color: transparent !important;
    }
    li[role="option"] span, div[role="option"] span, li[role="option"] div, div[role="option"] div {
        color: #0f172a !important;
    }
    li[role="option"]:hover, li[role="option"][aria-selected="true"], div[role="option"]:hover {
        background-color: #f1f5f9 !important;
    }
    li[role="option"]:hover span, li[role="option"][aria-selected="true"] span, li[role="option"]:hover div, div[role="option"]:hover div {
        color: #7c3aed !important;
    }
    /* Expander no modo claro */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-testid="stExpander"] details {
        background-color: #ffffff !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: #f8fafc !important;
        color: #0f172a !important;
        border-bottom: 1px solid #e2e8f0 !important;
        padding: 12px 16px !important;
    }
    div[data-testid="stExpander"] summary:hover {
        background-color: #f1f5f9 !important;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span,
    div[data-testid="stExpander"] summary div {
        color: #0f172a !important;
        font-weight: 700 !important;
    }
    div[data-testid="stExpander"] summary svg {
        fill: #64748b !important;
        color: #64748b !important;
    }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    /* File Uploader no modo claro - Aplicação completa e transparente nos filhos */
    [data-testid="stFileUploader"] *,
    [data-testid="stFileUploadDropzone"] *,
    section[data-testid="stFileUploadDropzone"] * {
        background-color: transparent !important;
    }
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"],
    [data-testid="stFileUploaderDropzone"] {
        background-color: #ffffff !important;
        background: #ffffff !important;
        border: 2px dashed #cbd5e1 !important;
        border-radius: 12px !important;
        color: #0f172a !important;
    }
    section[data-testid="stFileUploadDropzone"]:hover,
    [data-testid="stFileUploader"] section:hover,
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #7c3aed !important;
        background-color: #f8fafc !important;
        background: #f8fafc !important;
    }
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] div,
    [data-testid="stFileUploader"] label,
    section[data-testid="stFileUploadDropzone"] span,
    section[data-testid="stFileUploadDropzone"] small,
    section[data-testid="stFileUploadDropzone"] p,
    section[data-testid="stFileUploadDropzone"] div {
        color: #334155 !important;
        font-weight: 500 !important;
    }
    [data-testid="stFileUploader"] button,
    section[data-testid="stFileUploadDropzone"] button,
    [data-testid="stFileUploaderDropzone"] button {
        background-color: #f1f5f9 !important;
        background: #f1f5f9 !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 6px 16px !important;
    }
    [data-testid="stFileUploader"] button:hover,
    section[data-testid="stFileUploadDropzone"] button:hover,
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: #e2e8f0 !important;
        background: #e2e8f0 !important;
        color: #7c3aed !important;
        border-color: #7c3aed !important;
    }
    [data-testid="stFileUploader"] svg,
    section[data-testid="stFileUploadDropzone"] svg {
        fill: #475569 !important;
        color: #475569 !important;
    }
    /* Number Input no modo claro */
    div[data-testid="stNumberInput"] div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
    }
    div[data-testid="stNumberInput"] input {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    div[data-testid="stNumberInput"] button {
        background-color: #f1f5f9 !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
    }
    div[data-testid="stNumberInput"] button:hover {
        background-color: #e2e8f0 !important;
        color: #7c3aed !important;
    }
    div[data-testid="stNumberInput"] button svg {
        fill: #0f172a !important;
    }
    /* Código e Badges Dourados no lugar de verde com preto */
    code, [data-testid="stMarkdownContainer"] code {
        background-color: rgba(245, 158, 11, 0.12) !important;
        color: #b45309 !important;
        border: 1px solid rgba(245, 158, 11, 0.35) !important;
        border-radius: 6px !important;
        padding: 2px 8px !important;
        font-weight: 700 !important;
        font-size: 0.86rem !important;
    }
    button[data-baseweb="tab"] {
        color: #64748b !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #7c3aed !important;
        border-bottom-color: #7c3aed !important;
    }
    div[data-testid="stMetric"] {
        background: #ffffff !important;
        border: 1.5px solid #e2e8f0 !important;
        color: #0f172a !important;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05) !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #64748b !important;
    }
    div[data-testid="stMetricValue"] {
        color: #0f172a !important;
    }
    /* Popover e botões secundários no modo claro (elimina a pílula/fundo escuro #13111c) */
    div[data-testid="stPopover"] > button,
    div[data-testid="stPopover"] button,
    button[kind="secondary"],
    button[data-testid="baseButton-secondary"] {
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #334155 !important;
        border: 1.5px solid #cbd5e1 !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04) !important;
    }
    div[data-testid="stPopover"] > button:hover,
    div[data-testid="stPopover"] button:hover,
    button[kind="secondary"]:hover,
    button[data-testid="baseButton-secondary"]:hover {
        background-color: #f8fafc !important;
        background: #f8fafc !important;
        color: #7c3aed !important;
        border-color: #7c3aed !important;
    }
    div[data-testid="stPopoverBody"],
    div[data-testid="stPopoverBody"] > div {
        background-color: #ffffff !important;
        background: #ffffff !important;
        color: #0f172a !important;
    }
    """
else:
    theme_css = """
    body, .stApp, [data-testid="stAppViewContainer"], .main {
        background-color: #0a0a0f !important;
        color: #f8fafc !important;
    }
    p, span, label, div[data-testid="stMarkdownContainer"] p {
        color: #f8fafc !important;
    }
    .stCaption, [data-testid="stCaptionContainer"] {
        color: #94a3b8 !important;
    }
    input, textarea, [data-baseweb="select"] > div, [data-baseweb="base-input"] {
        background-color: #13111c !important;
        color: #f8fafc !important;
        border: 1px solid rgba(124, 58, 237, 0.35) !important;
    }
    div[data-testid="stExpander"] {
        background-color: rgba(19, 17, 28, 0.92) !important;
        border: 1.5px solid rgba(124, 58, 237, 0.3) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="stExpander"] details {
        background-color: rgba(19, 17, 28, 0.92) !important;
    }
    div[data-testid="stExpander"] summary {
        background-color: rgba(26, 23, 38, 0.9) !important;
        color: #f8fafc !important;
        border-bottom: 1px solid rgba(124, 58, 237, 0.25) !important;
        padding: 12px 16px !important;
    }
    div[data-testid="stExpander"] summary:hover {
        background-color: rgba(124, 58, 237, 0.15) !important;
    }
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span,
    div[data-testid="stExpander"] summary div {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    div[data-testid="stExpander"] summary svg {
        fill: #c4b5fd !important;
        color: #c4b5fd !important;
    }
    div[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
        background-color: rgba(19, 17, 28, 0.92) !important;
        color: #f8fafc !important;
    }
    /* File Uploader no modo escuro */
    [data-testid="stFileUploader"] *,
    [data-testid="stFileUploadDropzone"] *,
    section[data-testid="stFileUploadDropzone"] * {
        background-color: transparent !important;
    }
    [data-testid="stFileUploader"],
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploadDropzone"],
    section[data-testid="stFileUploadDropzone"],
    [data-testid="stFileUploaderDropzone"] {
        background-color: rgba(19, 17, 28, 0.85) !important;
        background: rgba(19, 17, 28, 0.85) !important;
        border: 2px dashed rgba(124, 58, 237, 0.4) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
    }
    section[data-testid="stFileUploadDropzone"]:hover,
    [data-testid="stFileUploader"] section:hover,
    [data-testid="stFileUploaderDropzone"]:hover {
        border-color: #fbbf24 !important;
        background-color: rgba(124, 58, 237, 0.12) !important;
        background: rgba(124, 58, 237, 0.12) !important;
    }
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] p,
    [data-testid="stFileUploader"] div,
    section[data-testid="stFileUploadDropzone"] span,
    section[data-testid="stFileUploadDropzone"] small,
    section[data-testid="stFileUploadDropzone"] p,
    section[data-testid="stFileUploadDropzone"] div {
        color: #cbd5e1 !important;
    }
    [data-testid="stFileUploader"] button,
    section[data-testid="stFileUploadDropzone"] button,
    [data-testid="stFileUploaderDropzone"] button {
        background-color: rgba(124, 58, 237, 0.25) !important;
        background: rgba(124, 58, 237, 0.25) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(124, 58, 237, 0.4) !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        padding: 6px 16px !important;
    }
    [data-testid="stFileUploader"] button:hover,
    section[data-testid="stFileUploadDropzone"] button:hover,
    [data-testid="stFileUploaderDropzone"] button:hover {
        background-color: rgba(124, 58, 237, 0.45) !important;
        background: rgba(124, 58, 237, 0.45) !important;
        color: #fbbf24 !important;
        border-color: #fbbf24 !important;
    }
    [data-testid="stFileUploader"] svg,
    section[data-testid="stFileUploadDropzone"] svg {
        fill: #c4b5fd !important;
        color: #c4b5fd !important;
    }
    /* Number Input no modo escuro */
    div[data-testid="stNumberInput"] div[data-baseweb="input"] {
        background-color: #13111c !important;
        border-color: rgba(124, 58, 237, 0.35) !important;
    }
    div[data-testid="stNumberInput"] input {
        background-color: #13111c !important;
        color: #f8fafc !important;
    }
    div[data-testid="stNumberInput"] button {
        background-color: rgba(124, 58, 237, 0.2) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(124, 58, 237, 0.35) !important;
    }
    div[data-testid="stNumberInput"] button:hover {
        background-color: rgba(124, 58, 237, 0.4) !important;
        color: #fbbf24 !important;
    }
    div[data-testid="stNumberInput"] button svg {
        fill: #f8fafc !important;
    }
    /* Código e Badges Dourados no lugar de verde com preto */
    code, [data-testid="stMarkdownContainer"] code {
        background-color: rgba(245, 158, 11, 0.15) !important;
        color: #fbbf24 !important;
        border: 1px solid rgba(245, 158, 11, 0.4) !important;
        border-radius: 6px !important;
        padding: 2px 8px !important;
        font-weight: 700 !important;
        font-size: 0.86rem !important;
    }
    div[data-testid="stMetric"] {
        background: rgba(19, 17, 28, 0.92) !important;
        border: 1px solid rgba(124, 58, 237, 0.35) !important;
        color: #f8fafc !important;
    }
    """

btn_sec_bg = "rgba(19, 17, 28, 0.85)" if is_dark else "#ffffff"
btn_sec_color = "#cbd5e1" if is_dark else "#0f172a"
btn_sec_border = "rgba(124, 58, 237, 0.35)" if is_dark else "#cbd5e1"

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Ocultar barra lateral e header padrão do Streamlit para evitar corte no topo */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    [data-testid="stSidebarCollapsedControl"],
    div[data-testid="stSidebarCollapseButton"],
    header[data-testid="stHeader"] {{
        display: none !important;
    }}

    /* Espaçamento superior generoso para abaixar o header e evitar qualquer corte */
    .block-container {{
        padding-top: 3.2rem !important;
        padding-bottom: 3rem !important;
        max-width: 98% !important;
    }}

    {theme_css}

    /* Estilos globais para botões adaptados ao tema ativo (Modo Claro / Escuro) */
    div[data-testid="stButton"] button {{
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease-in-out !important;
    }}

    div[data-testid="stButton"] button p,
    div[data-testid="stButton"] button span {{
        color: inherit !important;
    }}

    /* Botões Secundários Globais (qualquer botão não primário) */
    div[data-testid="stButton"] button[kind="secondary"],
    div[data-testid="stButton"] button:not([kind="primary"]) {{
        background: {btn_sec_bg} !important;
        background-color: {btn_sec_bg} !important;
        color: {btn_sec_color} !important;
        border: 1.5px solid {btn_sec_border} !important;
    }}

    div[data-testid="stButton"] button[kind="secondary"]:hover,
    div[data-testid="stButton"] button:not([kind="primary"]):hover {{
        border-color: {'#fbbf24' if is_dark else '#7c3aed'} !important;
        color: {'#fbbf24' if is_dark else '#7c3aed'} !important;
        background: {'rgba(124, 58, 237, 0.15)' if is_dark else '#f1f5f9'} !important;
        background-color: {'rgba(124, 58, 237, 0.15)' if is_dark else '#f1f5f9'} !important;
    }}

    div[data-testid="stButton"] button[kind="secondary"] p,
    div[data-testid="stButton"] button:not([kind="primary"]) p,
    div[data-testid="stButton"] button[kind="secondary"] span,
    div[data-testid="stButton"] button:not([kind="primary"]) span {{
        color: {btn_sec_color} !important;
    }}

    div[data-testid="stButton"] button[kind="secondary"]:hover p,
    div[data-testid="stButton"] button:not([kind="primary"]):hover p,
    div[data-testid="stButton"] button[kind="secondary"]:hover span,
    div[data-testid="stButton"] button:not([kind="primary"]):hover span {{
        color: {'#fbbf24' if is_dark else '#7c3aed'} !important;
    }}

    /* Botões Primários Globais */
    div[data-testid="stButton"] button[kind="primary"] {{
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%) !important;
        background-color: #7c3aed !important;
        color: #ffffff !important;
        border: 1.5px solid {'rgba(245, 158, 11, 0.6)' if is_dark else '#7c3aed'} !important;
        border-radius: 10px !important;
        box-shadow: 0 0 14px rgba(124, 58, 237, 0.3) !important;
    }}

    div[data-testid="stButton"] button[kind="primary"] p,
    div[data-testid="stButton"] button[kind="primary"] span {{
        color: #ffffff !important;
    }}

    /* Estilos estritamente aplicados ao Cabeçalho do App */
    .st-key-mathai_header div[data-testid="stHorizontalBlock"] {{
        align-items: center !important;
    }}

    .st-key-mathai_header div[data-testid="stElementContainer"] {{
        margin-bottom: 0 !important;
        padding-bottom: 0 !important;
    }}

    .st-key-mathai_header div[data-testid="stMarkdownContainer"] {{
        display: flex !important;
        align-items: center !important;
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
    }}

    .st-key-mathai_header div[data-testid="stMarkdownContainer"] p {{
        margin: 0 !important;
        padding: 0 !important;
    }}

    .st-key-mathai_header div[data-testid="stButton"] button {{
        height: 42px !important;
        min-height: 42px !important;
        max-height: 42px !important;
        margin: 0 !important;
        border-radius: 12px !important;
        padding: 0 14px !important;
    }}

    .st-key-mathai_header div[data-testid="stButton"] button p {{
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1 !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        overflow: visible !important;
        white-space: nowrap !important;
    }}

    .st-key-mathai_header div[data-testid="stButton"] button[kind="primary"] {{
        border: 2px solid {gold_border} !important;
        box-shadow: 0 0 16px rgba(245, 158, 11, 0.35) !important;
        font-weight: 700 !important;
        font-size: 0.95rem !important;
    }}

    .st-key-mathai_header div[data-testid="stButton"] button[kind="secondary"] {{
        font-size: 0.92rem !important;
    }}

    .st-key-mathai_header div[data-testid="stButton"] button[kind="secondary"]:hover {{
        border-color: {gold_border} !important;
        color: {gold_accent} !important;
        box-shadow: 0 0 12px rgba(245, 158, 11, 0.25) !important;
        transform: translateY(-1px);
    }}

    .st-key-nav_btn_perfil_topbar button {{
        border-radius: 12px !important;
        font-weight: 700 !important;
        font-size: 0.82rem !important;
        border: 1.5px solid {gold_border} !important;
        padding: 0 8px !important;
    }}

    /* Correção do texto escuro invisível no Multiselect e Selectbox */
    div[data-baseweb="select"] ul, 
    ul[role="listbox"],
    li[role="option"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #334155 !important;
        color: #f59e0b !important;
    }
</style>
<script>
    try {{
        localStorage.setItem('mathai_theme', '{st.session_state.tema}');
        const savedTheme = localStorage.getItem('mathai_theme');
        const urlParams = new URLSearchParams(window.location.search);
        if (savedTheme && !urlParams.has('theme')) {{
            urlParams.set('theme', savedTheme);
            const newUrl = window.location.pathname + '?' + urlParams.toString();
            window.history.replaceState(null, '', newUrl);
        }}
    }} catch (e) {{}}
</script>
""", unsafe_allow_html=True)

# ── 4. Autenticação & Sessão Persistida (Lembre-me Seguro por Token de Navegador) ──
from src.database.users import verificar_token_sessao, encerrar_sessao_por_token

if "usuario_logado" not in st.session_state or not st.session_state.usuario_logado:
    token_url = st.query_params.get("session")
    if token_url:
        usuario_encontrado = verificar_token_sessao(token_url)
        if usuario_encontrado:
            st.session_state.usuario_logado = usuario_encontrado
        else:
            st.query_params.clear()

if "usuario_logado" not in st.session_state or not st.session_state.usuario_logado:
    from src.app.pages.login import show as show_login
    show_login()
    st.stop()

# ── 5. Usuário Logado & Perfil ────────────────────────────────────────────────
usuario = st.session_state.get("usuario_logado") or {}
aluno_id = usuario.get("id")
st.session_state.aluno_id = aluno_id

nome_completo = str(usuario.get("nome") or "Aluno")
iniciais = "".join(p[0].upper() for p in nome_completo.split()[:2])
nome_exibir = nome_completo.split()[0] if nome_completo.split() else "Aluno"

motivos_map = {
    "concurso_militar": "🎖️ Concurso Militar",
    "enem_vestibular": "📚 ENEM / Vestibular",
    "melhoria_propria": "📈 Autoaperfeiçoamento",
    "professor": "👨‍🏫 Professor de Matemática",
    "olimpiada": "🏆 Olimpíadas de Matemática",
    "uso_profissional": "💼 Área Técnica",
    "curiosidade": "🔍 Curiosidade & Lógica"
}
faculdade_user = usuario.get("faculdade") or ""
curso_user = usuario.get("curso") or ""
escolaridade_user = usuario.get("escolaridade") or ""
concursos_user = usuario.get("concursos_foco") or []
motivos_user = usuario.get("motivos") or []

if faculdade_user and curso_user:
    sigla_fac = faculdade_user.split(" - ")[0] if " - " in faculdade_user else faculdade_user
    badge_subtitulo = f"{sigla_fac} • {curso_user}"
elif faculdade_user:
    sigla_fac = faculdade_user.split(" - ")[0] if " - " in faculdade_user else faculdade_user
    badge_subtitulo = f"{sigla_fac}"
elif curso_user:
    badge_subtitulo = f"{curso_user}"
elif concursos_user:
    foco_item = concursos_user[0] if isinstance(concursos_user, list) else str(concursos_user).split(",")[0]
    badge_subtitulo = f"Foco: {foco_item.split('(')[0].strip()}"
elif escolaridade_user:
    badge_subtitulo = escolaridade_user.split("(")[0].strip()
elif motivos_user:
    badge_subtitulo = motivos_map.get(motivos_user[0], "Estudante MathAI")
else:
    badge_subtitulo = "Estudante MathAI"

# ── 6. Header Unificado no Topo (Logo, Navegação em 4 Módulos, Perfil e Sair) ───
PAGES = {
    "🎯 Resolver / Simulado": "resolver",
    "📊 Perfil Cognitivo": "dashboard",
    "📚 Banco & Listas": "banco",
    "💡 Sobre Nós": "sobre",
    "👤 Meu Perfil": "perfil",
}

# Compatibilidade retroativa de chaves
if "nav_page" not in st.session_state or st.session_state.nav_page not in PAGES:
    st.session_state.nav_page = "🎯 Resolver / Simulado"

with st.container(key="mathai_header"):
    col_logo, col_res, col_dash, col_banco, col_sobre, col_tema, col_space, col_user, col_sair = st.columns(
        [1.75, 0.95, 0.9, 1.2, 0.95, 0.45, 1.3, 1.9, 0.45],
        vertical_alignment="center"
    )

    with col_logo:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 8px; height: 42px; margin: 0; padding: 0;">
            <div style="width: 36px; height: 36px; min-width: 36px;
                        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                        border: 2px solid {gold_border}; border-radius: 10px;
                        display: flex; align-items: center; justify-content: center;
                        font-size: 19px; box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);">
                📐
            </div>
            <div style="display: flex; flex-direction: column; justify-content: center; line-height: 1;">
                <div style="font-size: 1.18rem; font-weight: 800; color: {text_main}; letter-spacing: -0.02em; display: flex; align-items: center; gap: 5px;">
                    <span>MathAI</span>
                    <span style="font-size: 0.6rem; font-weight: 700; padding: 1px 5px; border-radius: 999px;
                                 background: rgba(245, 158, 11, 0.15); color: {gold_accent}; border: 1px solid rgba(245, 158, 11, 0.4);">
                        V1.0
                    </span>
                </div>
                <div style="font-size: 0.68rem; color: {text_muted}; margin-top: 2px; white-space: nowrap;">
                    A IA que mapeia seu raciocínio
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_res:
        is_resolver = (st.session_state.nav_page == "🎯 Resolver / Simulado")
        if st.button(
            "🎯 Resolver",
            use_container_width=True,
            type="primary" if is_resolver else "secondary",
            key="nav_btn_resolver"
        ):
            st.session_state.nav_page = "🎯 Resolver / Simulado"
            st.rerun()

    with col_dash:
        is_dash = (st.session_state.nav_page == "📊 Perfil Cognitivo")
        if st.button(
            "📊 Perfil",
            use_container_width=True,
            type="primary" if is_dash else "secondary",
            key="nav_btn_dashboard"
        ):
            st.session_state.nav_page = "📊 Perfil Cognitivo"
            st.rerun()

    with col_banco:
        is_banco = (st.session_state.nav_page == "📚 Banco & Listas")
        if st.button(
            "📚 Banco & Listas",
            use_container_width=True,
            type="primary" if is_banco else "secondary",
            key="nav_btn_banco"
        ):
            st.session_state.nav_page = "📚 Banco & Listas"
            st.rerun()

    with col_sobre:
        is_sobre = (st.session_state.nav_page == "💡 Sobre Nós")
        if st.button(
            "💡 Sobre Nós",
            use_container_width=True,
            type="primary" if is_sobre else "secondary",
            key="nav_btn_sobre"
        ):
            st.session_state.nav_page = "💡 Sobre Nós"
            st.rerun()

    with col_tema:
        icone_tema = "☀️" if is_dark else "🌙"
        help_tema = "Modo Claro" if is_dark else "Modo Escuro"
        if st.button(icone_tema, help=help_tema, use_container_width=True, key="btn_toggle_tema"):
            novo_tema = "light" if is_dark else "dark"
            st.session_state.tema = novo_tema
            st.query_params["theme"] = novo_tema
            st.rerun()

    with col_space:
        st.write("")

    with col_user:
        is_perfil = (st.session_state.nav_page == "👤 Meu Perfil")
        sub_badge = badge_subtitulo.split('•')[-1].strip()
        if len(sub_badge) > 16:
            sub_badge = sub_badge[:14] + ".."
        btn_label = f"👤 {nome_exibir} • {sub_badge}"
        if st.button(
            btn_label,
            help=f"Meu Perfil: {nome_completo}\n{badge_subtitulo}\nClique para ver e alterar seus dados",
            use_container_width=True,
            type="primary" if is_perfil else "secondary",
            key="nav_btn_perfil_topbar"
        ):
            st.session_state.nav_page = "👤 Meu Perfil"
            st.rerun()

    with col_sair:
        if st.button("🚪", help="Sair da Conta", use_container_width=True, key="btn_sair_app"):
            token_url = st.query_params.get("session")
            if token_url:
                encerrar_sessao_por_token(token_url)
            st.query_params.clear()
            st.session_state.clear()
            st.rerun()

# Divisória luminosa dourada
st.markdown(f"""
<div style="height: 2px; background: linear-gradient(90deg, rgba(124, 58, 237, 0.15) 0%, {gold_border} 50%, rgba(124, 58, 237, 0.15) 100%);
            margin: 6px 0 14px 0; border-radius: 2px; box-shadow: 0 0 8px rgba(245, 158, 11, 0.25);"></div>
""", unsafe_allow_html=True)

# ── 8. Renderização da Página Ativa ───────────────────────────────────────────
pagina_ativa = PAGES.get(st.session_state.nav_page, "resolver")

if pagina_ativa == "resolver":
    from src.app.pages.resolver import show as show_resolver
    show_resolver()
elif pagina_ativa == "dashboard":
    from src.app.pages.dashboard import show as show_dashboard
    show_dashboard()
elif pagina_ativa == "banco":
    from src.app.pages.banco import show as show_banco
    show_banco()
elif pagina_ativa == "sobre":
    from src.app.pages.sobre import show as show_sobre
    show_sobre()
elif pagina_ativa == "perfil":
    from src.app.pages.perfil import show as show_perfil
    show_perfil()

