"""
MathAI - Página de Login & Cadastro
Suporte a Tema Escuro / Claro, Lembre-me (Persistência de Sessão),
Dados cadastrais completos (CPF, CEP, Endereço via ViaCEP)
e Verificação em Duas Etapas (2FA / OTP de 6 dígitos).
"""

import uuid
import streamlit as st
from src.auth.google_auth import (
    obter_credenciais_google,
    gerar_url_auth_google,
    trocar_codigo_por_usuario_google
)
from src.database.users import (
    cadastrar_usuario,
    fazer_login,
    verificar_codigo_otp,
    reenviar_codigo_otp,
    buscar_endereco_por_cep,
    buscar_usuario_por_email,
    formatar_cpf,
    validar_cpf,
    criar_sessao_lembrada,
    encerrar_sessao_por_token
)
from src.app.pages.perfil import (
    ESCOLARIDADE_OPCOES,
    FACULDADES_BRASIL,
    CONCURSOS_MILITARES,
    CONCURSOS_VESTIBULARES
)

MOTIVOS_OPCOES = {
    "melhoria_propria":   "📈 Quero melhorar na Matemática por conta própria",
    "concurso_militar":   "🎖️ Concurso Militar (ESA, EsPCEx, AFA, EFOMM, IME, ITA...)",
    "enem_vestibular":    "📚 ENEM / Vestibular",
    "professor":          "👨‍🏫 Sou professor(a) de Matemática",
    "olimpiada":          "🏆 Olimpíadas de Matemática (OBMEP, OBM...)",
    "uso_profissional":   "💼 Uso profissional / área técnica",
    "curiosidade":        "🔍 Curiosidade / aprendizado geral",
}


def show():
    # 1. Configurações de Tema Dinâmico (Claro / Escuro) com persistência via URL
    tema_url = st.query_params.get("theme")
    if tema_url in ("dark", "light"):
        st.session_state.tema = tema_url
    elif "tema" not in st.session_state:
        st.session_state.tema = "dark"

    is_dark = (st.session_state.tema == "dark")
    bg_page = "#0a0a0f" if is_dark else "#f8fafc"
    card_bg = "linear-gradient(135deg, rgba(19, 17, 28, 0.96) 0%, rgba(10, 10, 15, 0.98) 100%)" if is_dark else "#ffffff"
    card_border = "rgba(124, 58, 237, 0.35)" if is_dark else "#cbd5e1"
    text_main = "#f8fafc" if is_dark else "#0f172a"
    text_muted = "#94a3b8" if is_dark else "#64748b"
    title_grad = "linear-gradient(135deg, #ffffff 0%, #c7d2fe 60%, #fbbf24 100%)" if is_dark else "linear-gradient(135deg, #0f172a 0%, #4f46e5 50%, #7c3aed 100%)"
    card_shadow = "0 16px 40px rgba(0, 0, 0, 0.6), 0 0 24px rgba(124, 58, 237, 0.15)" if is_dark else "0 10px 30px rgba(0, 0, 0, 0.06), 0 0 20px rgba(124, 58, 237, 0.08)"

    # CSS Dinâmico com Tema e Espaçamento Perfeito
    theme_inputs_css = """
    input, textarea, [data-baseweb="select"] > div, [data-baseweb="base-input"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1.5px solid #cbd5e1 !important;
    }
    div[data-baseweb="popover"], div[role="listbox"], ul[role="listbox"] {
        background-color: #ffffff !important;
        color: #0f172a !important;
    }
    li[role="option"] {
        color: #0f172a !important;
        background-color: #ffffff !important;
    }
    /* Separar as abas: Entrar no canto esquerdo, Criar Conta no canto direito */
    div[data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: space-between !important;
        width: 100% !important;
        border-bottom: 1.5px solid rgba(124, 58, 237, 0.25) !important;
        margin-bottom: 18px !important;
        gap: 0 !important;
    }
    button[data-baseweb="tab"] {
        flex: 0 1 auto !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        color: #64748b !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #7c3aed !important;
        border-bottom-color: #7c3aed !important;
    }
    """ if not is_dark else """
    input, textarea, [data-baseweb="select"] > div, [data-baseweb="base-input"] {
        background-color: #13111c !important;
        color: #f8fafc !important;
        border: 1.5px solid rgba(124, 58, 237, 0.35) !important;
    }
    div[data-baseweb="tab-list"] {
        display: flex !important;
        justify-content: space-between !important;
        width: 100% !important;
        border-bottom: 1.5px solid rgba(124, 58, 237, 0.25) !important;
        margin-bottom: 18px !important;
        gap: 0 !important;
    }
    button[data-baseweb="tab"] {
        flex: 0 1 auto !important;
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        padding: 8px 12px !important;
        color: #94a3b8 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #c084fc !important;
        border-bottom-color: #a855f7 !important;
    }
    """

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    /* Ocultar barra superior e lateral do Streamlit para evitar corte */
    [data-testid="stSidebar"],
    section[data-testid="stSidebar"],
    header[data-testid="stHeader"] {{
        display: none !important;
    }}

    .block-container {{
        padding-top: 2.8rem !important;
        padding-bottom: 3rem !important;
        max-width: 98% !important;
    }}

    body, .stApp, [data-testid="stAppViewContainer"], .main {{
        background-color: {bg_page} !important;
        color: {text_main} !important;
    }}

    p, span, label, div[data-testid="stMarkdownContainer"] p {{
        color: {text_main} !important;
    }}

    {theme_inputs_css}

    /* Container Principal */
    .auth-brand-badge {{
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: {'rgba(245, 158, 11, 0.12)' if is_dark else 'rgba(124, 58, 237, 0.08)'};
        color: {'#fbbf24' if is_dark else '#7c3aed'};
        border: 1px solid {'rgba(245, 158, 11, 0.35)' if is_dark else 'rgba(124, 58, 237, 0.25)'};
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        margin-bottom: 12px;
    }}

    .auth-card {{
        background: {card_bg};
        border: 1.5px solid {card_border};
        border-radius: 20px;
        padding: 32px 28px;
        box-shadow: {card_shadow};
        margin-bottom: 24px;
    }}

    .auth-logo-box {{
        width: 68px;
        height: 68px;
        margin: 0 auto 12px;
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        border: 2px solid rgba(245, 158, 11, 0.5);
        border-radius: 20px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 34px;
        box-shadow: 0 8px 24px rgba(124, 58, 237, 0.4), 0 0 12px rgba(245, 158, 11, 0.25);
    }}

    .auth-title {{
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin: 0;
        background: {title_grad};
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
    }}

    .auth-subtitle {{
        font-size: 0.9rem;
        color: {text_muted};
        margin-top: 6px;
        text-align: center;
        margin-bottom: 20px;
    }}

    /* Caixa de Código OTP */
    .otp-display-box {{
        background: rgba(245, 158, 11, 0.1);
        border: 2px dashed #f59e0b;
        border-radius: 14px;
        padding: 16px;
        text-align: center;
        margin: 16px 0;
    }}

    .otp-code-text {{
        font-size: 2rem;
        font-weight: 800;
        letter-spacing: 10px;
        color: #fbbf24;
        font-family: monospace;
    }}
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

    # Barra superior do login com Alternador de Tema no canto direito
    c_top_vazio, c_top_tema = st.columns([9, 1])
    with c_top_tema:
        icone_tema = "☀️" if is_dark else "🌙"
        help_tema = "Modo Claro" if is_dark else "Modo Escuro"
        if st.button(icone_tema, help=help_tema, key="btn_login_tema", use_container_width=True):
            novo_tema = "light" if is_dark else "dark"
            st.session_state.tema = novo_tema
            st.query_params["theme"] = novo_tema
            st.rerun()

    col_esq, col_centro, col_dir = st.columns([1, 1.8, 1])

    with col_centro:
        # Cabeçalho da Marca
        st.markdown("""
        <div style="text-align: center;">
            <div class="auth-logo-box">📐</div>
            <div class="auth-brand-badge">⚡ Plataforma Cognitiva</div>
            <h1 class="auth-title">MathAI</h1>
            <p class="auth-subtitle">
                Aprenda Matemática com diagnóstico de raciocínio orientado por IA
            </p>
        </div>
        """, unsafe_allow_html=True)

        # ── 0. INTERCEPTOR GOOGLE OAUTH ──────────────────────────────────────
        code = st.query_params.get("code")
        if code:
            g_cid, g_csec = obter_credenciais_google()
            if g_cid and g_csec:
                red_uri = "https://mathia.streamlit.app"
                with st.spinner("Autenticando com o Google..."):
                    u_google = trocar_codigo_por_usuario_google(code, g_cid, g_csec, red_uri)
                st.query_params.clear()
                if u_google:
                    u_db = buscar_usuario_por_email(u_google["email"])
                    if u_db:
                        st.session_state.usuario_logado = u_db
                        tok = criar_sessao_lembrada(u_db["id"])
                        st.query_params["session"] = tok
                        st.toast(f"Bem-vindo(a) de volta, {u_db['nome'].split()[0]}! 👋", icon="🚀")
                        st.rerun()
                    else:
                        # Usuário novo! Aciona tela de onboarding para completar perfil
                        st.session_state.google_onboarding = u_google
                        st.rerun()
                else:
                    st.error("Falha ao autenticar com o Google. Tente novamente.")

        # ── FLUXO ONBOARDING GOOGLE (NOVO USUÁRIO) ───────────────────────────
        if st.session_state.get("google_onboarding"):
            g_user = st.session_state.google_onboarding
            g_nome = g_user.get("nome", "")
            g_email = g_user.get("email", "")
            g_pic = g_user.get("picture", "")

            st.markdown(f"""
            <div class="auth-card">
                <div style="text-align: center; margin-bottom: 20px;">
                    {'<img src="' + g_pic + '" style="width: 64px; height: 64px; border-radius: 50%; margin-bottom: 8px; border: 2px solid #7c3aed;">' if g_pic else '<div style="font-size: 2.2rem; margin-bottom: 4px;">🎓</div>'}
                    <h3 style="margin: 0; color: {text_main}; font-weight: 700;">Quase lá, {g_nome.split()[0]}!</h3>
                    <p style="font-size: 0.86rem; color: {text_muted}; margin-top: 4px;">
                        Sua conta Google foi verificada. Complete seus dados de estudante para personalizarmos seus treinos.
                    </p>
                </div>
            """, unsafe_allow_html=True)

            with st.form("form_google_onboarding"):
                col_n, col_e = st.columns(2)
                with col_n:
                    st.text_input("Nome", value=g_nome, disabled=True)
                with col_e:
                    st.text_input("E-mail", value=g_email, disabled=True)

                col_id, col_cpf = st.columns(2)
                with col_id:
                    g_idade = st.number_input("Idade *", min_value=10, max_value=90, value=18, key="g_idade")
                with col_cpf:
                    g_cpf = st.text_input("🪪 CPF *", placeholder="000.000.000-00", key="g_cpf")

                g_celular = st.text_input("📱 Celular / WhatsApp", placeholder="(21) 99999-9999", key="g_celular")

                # Endereço
                st.markdown("---")
                st.markdown("##### 📍 Endereço")
                col_c1, col_c2 = st.columns([2, 1])
                with col_c1:
                    g_cep = st.text_input("CEP", placeholder="00000-000", key="g_cad_cep")
                with col_c2:
                    st.write("")
                    st.write("")
                    if st.form_submit_button("🔍 Buscar CEP"):
                        if g_cep:
                            end = buscar_endereco_por_cep(g_cep)
                            if end:
                                st.session_state["g_logradouro"] = end.get("logradouro", "")
                                st.session_state["g_bairro"] = end.get("bairro", "")
                                st.session_state["g_cidade"] = end.get("cidade", "")
                                st.session_state["g_estado"] = end.get("estado", "")
                                st.toast("Endereço preenchido!", icon="📍")
                                st.rerun()

                col_r, col_num = st.columns([3, 1])
                with col_r:
                    g_logradouro = st.text_input("Logradouro / Rua", placeholder="Rua...", key="g_logradouro")
                with col_num:
                    g_numero = st.text_input("Número", placeholder="123", key="g_numero")

                col_b, col_cid, col_uf = st.columns([1.5, 2, 1])
                with col_b:
                    g_bairro = st.text_input("Bairro", placeholder="Bairro", key="g_bairro")
                with col_cid:
                    g_cidade = st.text_input("Cidade", placeholder="Cidade", key="g_cidade")
                with col_uf:
                    g_estado = st.text_input("UF", placeholder="RJ", max_chars=2, key="g_estado")

                # Escolaridade & Objetivos
                st.markdown("---")
                st.markdown("##### 🎓 Formação & Objetivos")
                g_escolaridade = st.selectbox("Nível de Escolaridade *", options=ESCOLARIDADE_OPCOES, index=1, key="g_esc")
                eh_sup = g_escolaridade in ["Ensino Superior (Graduação)", "Pós-Graduação / Especialização", "Mestrado", "Doutorado"]
                g_faculdade = None
                g_curso = None
                if eh_sup:
                    col_f, col_cur = st.columns(2)
                    with col_f:
                        g_faculdade = st.selectbox("Instituição / Faculdade", options=FACULDADES_BRASIL, key="g_fac")
                    with col_cur:
                        g_curso = st.text_input("Curso de Graduação *", placeholder="Ex: Engenharia, Matemática", key="g_curso")

                st.markdown("##### 🎯 Objetivos de Estudo *")
                g_motivos = []
                for cod, rotulo in MOTIVOS_OPCOES.items():
                    if st.checkbox(rotulo, key=f"g_mot_{cod}"):
                        g_motivos.append(cod)

                st.markdown("##### 🎖️ Concursos de Interesse")
                col_m, col_v = st.columns(2)
                g_focos = []
                with col_m:
                    st.caption("Concursos Militares:")
                    for conc in CONCURSOS_MILITARES:
                        if st.checkbox(conc, key=f"g_cm_{conc}"):
                            g_focos.append(conc)
                with col_v:
                    st.caption("Vestibulares / Outros:")
                    for conc in CONCURSOS_VESTIBULARES:
                        if st.checkbox(conc, key=f"g_cv_{conc}"):
                            g_focos.append(conc)

                btn_concluir_google = st.form_submit_button("🚀 Concluir Cadastro e Começar a Treinar", use_container_width=True, type="primary")

                if btn_concluir_google:
                    erros = []
                    if not g_cpf.strip():
                        erros.append("CPF é obrigatório.")
                    elif not validar_cpf(g_cpf):
                        erros.append("CPF inválido.")
                    if not g_motivos:
                        erros.append("Selecione pelo menos 1 objetivo de estudo.")
                    if eh_sup and not (g_curso and g_curso.strip()):
                        erros.append("Informe seu curso de graduação.")

                    if erros:
                        for e in erros:
                            st.error(e)
                    else:
                        senha_segura = uuid.uuid4().hex
                        res_cad = cadastrar_usuario(
                            nome=g_nome,
                            email=g_email,
                            senha=senha_segura,
                            cpf=g_cpf,
                            idade=int(g_idade),
                            celular=g_celular or None,
                            cep=g_cep or None,
                            logradouro=g_logradouro or None,
                            numero=g_numero or None,
                            bairro=g_bairro or None,
                            cidade=g_cidade or None,
                            estado=g_estado or None,
                            motivos=g_motivos,
                            escolaridade=g_escolaridade,
                            faculdade=g_faculdade if eh_sup else None,
                            curso=g_curso.strip() if (eh_sup and g_curso) else None,
                            concursos_foco=g_focos,
                            verificado=1
                        )
                        if res_cad["ok"]:
                            st.session_state.usuario_logado = res_cad["usuario"]
                            token = criar_sessao_lembrada(res_cad["usuario"]["id"])
                            st.query_params["session"] = token
                            st.session_state.pop("google_onboarding", None)
                            st.success(f"Bem-vindo(a) ao MathAI, {g_nome.split()[0]}! 🎉")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(res_cad["erro"])

            if st.button("⬅️ Cancelar e Voltar", use_container_width=True, key="btn_cancel_google"):
                st.session_state.pop("google_onboarding", None)
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            return

        # ── FLUXO DE VERIFICAÇÃO EM 2 ETAPAS (2FA / OTP) ──────────────────────
        if st.session_state.get("verificando_email"):
            email_verif = st.session_state.verificando_email
            codigo_teste = st.session_state.get("codigo_teste_otp", "")

            st.markdown(f"""
            <div class="auth-card">
                <div style="text-align: center; margin-bottom: 18px;">
                    <div style="font-size: 2.2rem; margin-bottom: 4px;">🔐</div>
                    <h3 style="margin: 0; color: {text_main}; font-weight: 700;">Verificação em Duas Etapas</h3>
                    <p style="font-size: 0.86rem; color: {text_muted}; margin-top: 4px;">
                        Enviamos um código de 6 dígitos para:<br>
                        <b style="color: {'#c7d2fe' if is_dark else '#4f46e5'};">{email_verif}</b>
                    </p>
                </div>
            """, unsafe_allow_html=True)

            email_enviado_real = st.session_state.get("email_enviado_real", False)
            if email_enviado_real:
                st.markdown(f"""
                <div style="background: rgba(16, 185, 129, 0.12); border: 1.5px solid #10b981; border-radius: 12px; padding: 14px 18px; margin: 16px 0; text-align: center;">
                    <div style="font-size: 1.1rem; font-weight: 700; color: #10b981; margin-bottom: 4px;">📧 Código enviado para seu e-mail!</div>
                    <div style="font-size: 0.82rem; color: {text_muted};">
                        Verifique sua Caixa de Entrada e também a pasta de <b>Spam / Lixo Eletrônico</b>.<br>
                        O código é composto por 6 dígitos numéricos.
                    </div>
                </div>
                """, unsafe_allow_html=True)
            elif codigo_teste:
                st.markdown(f"""
                <div class="otp-display-box">
                    <div style="font-size: 0.75rem; color: #f59e0b; text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">
                        🔑 Código de Verificação (Modo de Teste / Dev)
                    </div>
                    <div class="otp-code-text">{codigo_teste}</div>
                    <div style="font-size: 0.75rem; color: {text_muted}; margin-top: 4px;">
                        Para enviar para a caixa de e-mail real, configure as credenciais SMTP no Streamlit Cloud
                    </div>
                </div>
                """, unsafe_allow_html=True)

            with st.form("form_otp", clear_on_submit=False):
                codigo_digitado = st.text_input(
                    "Digite o código de 6 dígitos",
                    max_chars=6,
                    placeholder="000000",
                    key="input_codigo_otp"
                )
                btn_confirmar_otp = st.form_submit_button(
                    "✅ Confirmar e Ativar Conta",
                    use_container_width=True,
                    type="primary"
                )

                if btn_confirmar_otp:
                    if not codigo_digitado or len(codigo_digitado.strip()) != 6:
                        st.warning("Por favor, digite os 6 dígitos do código.")
                    else:
                        resultado = verificar_codigo_otp(email_verif, codigo_digitado.strip())
                        if resultado["ok"]:
                            st.session_state.usuario_logado = resultado["usuario"]
                            novo_token = criar_sessao_lembrada(resultado["usuario"]["id"])
                            st.query_params["session"] = novo_token
                            st.session_state.pop("verificando_email", None)
                            st.session_state.pop("codigo_teste_otp", None)
                            st.session_state.pop("email_enviado_real", None)
                            st.success("🎉 Conta verificada com sucesso! Bem-vindo(a) ao MathAI!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(resultado["erro"])

            col_btn_reenviar, col_btn_voltar = st.columns(2)
            with col_btn_reenviar:
                if st.button("🔄 Reenviar Código", use_container_width=True, key="btn_reenviar_otp"):
                    res_reenvio = reenviar_codigo_otp(email_verif)
                    st.session_state.email_enviado_real = res_reenvio.get("enviado_email", False)
                    if not res_reenvio.get("enviado_email"):
                        st.session_state.codigo_teste_otp = res_reenvio.get("codigo_teste", "")
                    else:
                        st.session_state.codigo_teste_otp = ""
                    st.info("Novo código gerado!")
                    st.rerun()

            with col_btn_voltar:
                if st.button("⬅️ Voltar para Login", use_container_width=True, key="btn_voltar_login"):
                    st.session_state.pop("verificando_email", None)
                    st.session_state.pop("codigo_teste_otp", None)
                    st.session_state.pop("email_enviado_real", None)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            return

        # ── ABAS: LOGIN & CADASTRO ────────────────────────────────────────────
        aba = st.tabs(["🔑 Entrar", "✨ Criar Conta"])

        # ── 1. ABA LOGIN ───────────────────────────────────────────────────────
        with aba[0]:
            g_cid, g_csec = obter_credenciais_google()
            if g_cid:
                auth_url = gerar_url_auth_google(g_cid, "https://mathia.streamlit.app")
                bg_btn = "#161329" if is_dark else "#ffffff"
                border_btn = "rgba(124, 58, 237, 0.55)" if is_dark else "#cbd5e1"
                text_btn = "#ffffff" if is_dark else "#1e293b"
                shadow_btn = "0 4px 16px rgba(0,0,0,0.4)" if is_dark else "0 2px 8px rgba(0,0,0,0.06)"
                st.markdown(f"""
                <div style="margin-bottom: 16px;">
                    <a href="{auth_url}" target="_self" style="text-decoration: none !important; display: block; width: 100%;">
                        <div style="display: flex; align-items: center; justify-content: center; gap: 12px;
                                    background: {bg_btn}; border: 1.5px solid {border_btn}; border-radius: 12px;
                                    padding: 12px 18px; box-shadow: {shadow_btn}; cursor: pointer; transition: all 0.2s ease;">
                            <svg width="20" height="20" viewBox="0 0 24 24" style="flex-shrink: 0;">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                            </svg>
                            <span style="color: {text_btn} !important; font-weight: 600 !important; font-size: 0.95rem !important;">Continuar com o Google</span>
                        </div>
                    </a>
                </div>
                <div style="display: flex; align-items: center; text-align: center; margin: 14px 0 18px 0;">
                    <div style="flex: 1; height: 1px; background: {'rgba(255,255,255,0.15)' if is_dark else '#e2e8f0'};"></div>
                    <span style="padding: 0 10px; font-size: 0.76rem; color: {text_muted}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">ou com e-mail</span>
                    <div style="flex: 1; height: 1px; background: {'rgba(255,255,255,0.15)' if is_dark else '#e2e8f0'};"></div>
                </div>
                """, unsafe_allow_html=True)
            with st.form("form_login", clear_on_submit=False):
                st.markdown("#### Acesse sua conta")
                email_login = st.text_input("📧 E-mail", placeholder="seu@email.com", key="login_email")
                senha_login = st.text_input("🔒 Senha", type="password", key="login_senha")

                # Checkbox de Lembre-me
                lembrar_login = st.checkbox("Manter conectado neste dispositivo (Lembre-me)", value=True, key="login_lembrar_me")

                btn_login = st.form_submit_button("Entrar no MathAI →", use_container_width=True, type="primary")

                if btn_login:
                    if not email_login or not senha_login:
                        st.warning("Preencha e-mail e senha.")
                    else:
                        resultado = fazer_login(email_login, senha_login)
                        if resultado["ok"]:
                            st.session_state.usuario_logado = resultado["usuario"]
                            if lembrar_login:
                                novo_token = criar_sessao_lembrada(resultado["usuario"]["id"])
                                st.query_params["session"] = novo_token
                            else:
                                st.query_params.clear()
                            st.success(f"Bem-vindo(a) de volta, {resultado['usuario']['nome'].split()[0]}! 🎉")
                            st.rerun()
                        elif resultado.get("pendente_verificacao"):
                            st.session_state.verificando_email = resultado["email"]
                            st.session_state.codigo_teste_otp = resultado.get("codigo_teste", "")
                            st.warning(resultado["erro"])
                            st.rerun()
                        else:
                            st.error(resultado["erro"])

        # ── 2. ABA CADASTRO ────────────────────────────────────────────────────
        with aba[1]:
            g_cid, g_csec = obter_credenciais_google()
            if g_cid:
                auth_url = gerar_url_auth_google(g_cid, "https://mathia.streamlit.app")
                bg_btn = "#161329" if is_dark else "#ffffff"
                border_btn = "rgba(124, 58, 237, 0.55)" if is_dark else "#cbd5e1"
                text_btn = "#ffffff" if is_dark else "#1e293b"
                shadow_btn = "0 4px 14px rgba(0,0,0,0.4)" if is_dark else "0 2px 8px rgba(0,0,0,0.06)"
                st.markdown(f"""
                <div style="margin-bottom: 16px;">
                    <a href="{auth_url}" target="_self" style="text-decoration: none !important; display: block; width: 100%;">
                        <div style="display: flex; align-items: center; justify-content: center; gap: 12px;
                                    background: {bg_btn}; border: 1.5px solid {border_btn}; border-radius: 12px;
                                    padding: 12px 18px; box-shadow: {shadow_btn}; cursor: pointer; transition: all 0.2s ease;">
                            <svg width="20" height="20" viewBox="0 0 24 24" style="flex-shrink: 0;">
                                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"/>
                                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"/>
                            </svg>
                            <span style="color: {text_btn} !important; font-weight: 600 !important; font-size: 0.95rem !important;">Cadastrar com o Google</span>
                        </div>
                    </a>
                </div>
                <div style="display: flex; align-items: center; text-align: center; margin: 14px 0 18px 0;">
                    <div style="flex: 1; height: 1px; background: {'rgba(255,255,255,0.15)' if is_dark else '#e2e8f0'};"></div>
                    <span style="padding: 0 10px; font-size: 0.76rem; color: {text_muted}; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 600;">ou cadastro manual completo</span>
                    <div style="flex: 1; height: 1px; background: {'rgba(255,255,255,0.15)' if is_dark else '#e2e8f0'};"></div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown("#### Cadastro Completo & Personalizado")
            st.caption("Preencha seus dados para montarmos sua grade de estudos e liberar o acesso.")

            # Dados Pessoais
            col_nome, col_idade = st.columns([2.5, 1])
            with col_nome:
                c_nome = st.text_input("👤 Nome completo *", placeholder="Ex: Pedro Alvares Cabral", key="cad_nome")
            with col_idade:
                c_idade = st.number_input("Idade", min_value=10, max_value=90, value=18, key="cad_idade")

            col_cpf, col_cel = st.columns(2)
            with col_cpf:
                c_cpf = st.text_input("🪪 CPF *", placeholder="000.000.000-00", key="cad_cpf")
            with col_cel:
                c_celular = st.text_input("📱 Celular / WhatsApp *", placeholder="(21) 99999-9999", key="cad_celular")

            c_email = st.text_input("📧 E-mail *", placeholder="seu@email.com", key="cad_email")

            # Endereço e Localização (com busca ViaCEP)
            st.markdown("---")
            st.markdown("##### 📍 Endereço & Localização")

            col_cep, col_btn_cep = st.columns([2, 1])
            with col_cep:
                c_cep = st.text_input("CEP", placeholder="00000-000", key="cad_cep")
            with col_btn_cep:
                st.write("")
                st.write("")
                if st.button("🔍 Buscar CEP", use_container_width=True, key="cad_btn_buscar_cep"):
                    if c_cep:
                        endereco_cep = buscar_endereco_por_cep(c_cep)
                        if endereco_cep:
                            st.session_state["cad_logradouro"] = endereco_cep.get("logradouro", "")
                            st.session_state["cad_bairro"] = endereco_cep.get("bairro", "")
                            st.session_state["cad_cidade"] = endereco_cep.get("cidade", "")
                            st.session_state["cad_estado"] = endereco_cep.get("estado", "")
                            st.toast("Endereço preenchido com sucesso!", icon="📍")
                            st.rerun()
                        else:
                            st.warning("CEP não encontrado. Preencha os campos manualmente.")
                    else:
                        st.warning("Digite o CEP antes de buscar.")

            col_logr, col_num = st.columns([3, 1])
            with col_logr:
                c_logradouro = st.text_input(
                    "Logradouro / Rua",
                    placeholder="Rua das Flores",
                    key="cad_logradouro"
                )
            with col_num:
                c_numero = st.text_input("Número", placeholder="123", key="cad_numero")

            col_bairro, col_cid, col_uf = st.columns([1.5, 2, 1])
            with col_bairro:
                c_bairro = st.text_input(
                    "Bairro",
                    placeholder="Centro",
                    key="cad_bairro"
                )
            with col_cid:
                c_cidade = st.text_input(
                    "Cidade",
                    placeholder="Niterói",
                    key="cad_cidade"
                )
            with col_uf:
                c_estado = st.text_input(
                    "UF",
                    placeholder="RJ",
                    max_chars=2,
                    key="cad_estado"
                )

            # ── Formação Acadêmica & Escolaridade ──
            st.markdown("---")
            st.markdown("##### 🎓 Formação Acadêmica & Escolaridade")

            c_escolaridade = st.selectbox(
                "Nível de Escolaridade Atual *",
                options=ESCOLARIDADE_OPCOES,
                index=1,  # Padrão: Ensino Médio
                key="cad_escolaridade"
            )

            eh_ensino_superior = c_escolaridade in [
                "Ensino Superior (Graduação)",
                "Pós-Graduação / Especialização",
                "Mestrado",
                "Doutorado"
            ]

            c_faculdade = None
            c_curso = None

            if eh_ensino_superior:
                st.markdown(f"""
                <div style="background: {'rgba(124, 58, 237, 0.1)' if is_dark else 'rgba(124, 58, 237, 0.05)'};
                            border: 1px dashed {'rgba(124, 58, 237, 0.35)' if is_dark else '#cbd5e1'};
                            border-radius: 12px; padding: 12px; margin-top: 4px; margin-bottom: 8px;">
                    <div style="font-size: 0.82rem; font-weight: 700; color: {'#c7d2fe' if is_dark else '#6d28d9'}; margin-bottom: 6px;">
                        🏛️ Informações da Faculdade & Graduação
                    </div>
                """, unsafe_allow_html=True)

                faculdade_sel = st.selectbox(
                    "Instituição de Ensino Superior *",
                    options=FACULDADES_BRASIL,
                    key="cad_sel_faculdade"
                )

                if faculdade_sel == "Outra Faculdade / Universidade":
                    c_faculdade_custom = st.text_input(
                        "Digite o nome da sua Faculdade / Universidade *",
                        placeholder="Ex: UERJ, Estácio, Mackenzie, etc.",
                        key="cad_faculdade_custom"
                    )
                    c_faculdade = c_faculdade_custom.strip() if c_faculdade_custom else "Outra Faculdade"
                else:
                    c_faculdade = faculdade_sel

                c_curso = st.text_input(
                    "Curso / Graduação *",
                    placeholder="Ex: Engenharia Civil, Matemática, Medicina, Direito...",
                    key="cad_curso"
                )
                st.markdown("</div>", unsafe_allow_html=True)

            # ── Objetivos & Concursos Foco ──
            st.markdown("---")
            st.markdown("##### 🎯 Objetivos de Estudo & Foco")
            st.caption("Selecione seus objetivos para que possamos priorizar suas listas e simulados:")

            motivos_selecionados = []
            for chave, label in MOTIVOS_OPCOES.items():
                if st.checkbox(label, key=f"cad_motivo_{chave}"):
                    motivos_selecionados.append(chave)

            tem_militar = "concurso_militar" in motivos_selecionados
            tem_vestibular = "enem_vestibular" in motivos_selecionados
            concursos_foco_selecionados = []

            if tem_militar:
                st.markdown(f"""
                <div style="margin-top: 8px; font-size: 0.88rem; font-weight: 700; color: {'#fbbf24' if is_dark else '#b45309'};">
                    🎖️ Concursos Militares de Interesse:
                </div>
                """, unsafe_allow_html=True)
                sel_militares = st.multiselect(
                    "Quais concursos você pretende prestar?",
                    options=CONCURSOS_MILITARES,
                    key="cad_sel_militares"
                )
                concursos_foco_selecionados.extend(sel_militares)
                if "Outro Concurso Militar" in sel_militares:
                    outro_m = st.text_input("Qual outro concurso militar?", key="cad_outro_militar")
                    if outro_m:
                        concursos_foco_selecionados.append(outro_m)

            if tem_vestibular:
                st.markdown(f"""
                <div style="margin-top: 8px; font-size: 0.88rem; font-weight: 700; color: {'#60a5fa' if is_dark else '#1d4ed8'};">
                    📚 Vestibulares de Interesse:
                </div>
                """, unsafe_allow_html=True)
                sel_vestibulares = st.multiselect(
                    "Quais vestibulares você pretende prestar?",
                    options=CONCURSOS_VESTIBULARES,
                    key="cad_sel_vestibulares"
                )
                concursos_foco_selecionados.extend(sel_vestibulares)
                if "Outro Vestibular" in sel_vestibulares:
                    outro_v = st.text_input("Qual outro vestibular?", key="cad_outro_vestibular")
                    if outro_v:
                        concursos_foco_selecionados.append(outro_v)

            # Segurança / Senha
            st.markdown("---")
            st.markdown("##### 🔒 Senha de Acesso")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                c_senha = st.text_input("Senha (mínimo 6 caracteres) *", type="password", key="cad_senha")
            with col_s2:
                c_senha2 = st.text_input("Confirmar Senha *", type="password", key="cad_senha2")

            # Botão de Cadastro
            st.markdown("---")
            btn_cadastrar = st.button(
                "Criar Conta e Receber Código 2FA →",
                use_container_width=True,
                type="primary",
                key="btn_submeter_cadastro"
            )

            if btn_cadastrar:
                erros = []
                if not c_nome.strip():        erros.append("Nome completo é obrigatório.")
                if not c_email.strip():       erros.append("E-mail é obrigatório.")
                if not c_cpf.strip():         erros.append("CPF é obrigatório.")
                elif not validar_cpf(c_cpf):  erros.append("CPF inválido. Verifique os dígitos.")
                if not c_senha:               erros.append("Senha é obrigatória.")
                if c_senha != c_senha2:       erros.append("As senhas não coincidem.")
                if len(c_senha) < 6:          erros.append("Senha deve ter pelo menos 6 caracteres.")
                if not motivos_selecionados:  erros.append("Selecione pelo menos 1 objetivo de estudo.")
                if eh_ensino_superior and not (c_curso and c_curso.strip()):
                    erros.append("Informe o seu curso de graduação.")

                if erros:
                    for e in erros:
                        st.error(e)
                else:
                    # Auto-preenchimento de CEP se não tiver buscado antes
                    logr = c_logradouro
                    bair = c_bairro
                    cid = c_cidade
                    uf = c_estado
                    if c_cep and not logr:
                        end_auto = buscar_endereco_por_cep(c_cep)
                        if end_auto:
                            logr = end_auto.get("logradouro", "")
                            bair = end_auto.get("bairro", "")
                            cid = end_auto.get("cidade", "")
                            uf = end_auto.get("estado", "")

                    resultado = cadastrar_usuario(
                        nome=c_nome,
                        email=c_email,
                        senha=c_senha,
                        cpf=c_cpf,
                        idade=int(c_idade),
                        celular=c_celular or None,
                        cep=c_cep or None,
                        logradouro=logr or None,
                        numero=c_numero or None,
                        bairro=bair or None,
                        cidade=cid or None,
                        estado=uf or None,
                        motivos=motivos_selecionados,
                        escolaridade=c_escolaridade,
                        faculdade=c_faculdade if eh_ensino_superior else None,
                        curso=c_curso.strip() if (eh_ensino_superior and c_curso) else None,
                        concursos_foco=concursos_foco_selecionados
                    )
                    if resultado["ok"]:
                        st.session_state.verificando_email = resultado["email"]
                        st.session_state.email_enviado_real = resultado.get("enviado_email", False)
                        if not resultado.get("enviado_email"):
                            st.session_state.codigo_teste_otp = resultado.get("codigo_teste", "")
                        else:
                            st.session_state.codigo_teste_otp = ""
                        st.toast("Conta criada! Código de verificação gerado.", icon="🔑")
                        st.rerun()
                    else:
                        st.error(resultado["erro"])
