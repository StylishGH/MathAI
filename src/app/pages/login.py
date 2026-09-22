"""
MathAI - Página de Login & Cadastro
Suporte a Tema Escuro / Claro, Lembre-me (Persistência de Sessão),
Dados cadastrais completos (CPF, CEP, Endereço via ViaCEP)
e Verificação em Duas Etapas (2FA / OTP de 6 dígitos).
"""

import streamlit as st
from src.database.users import (
    cadastrar_usuario,
    fazer_login,
    verificar_codigo_otp,
    reenviar_codigo_otp,
    buscar_endereco_por_cep,
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
    # 1. Configurações de Tema Dinâmico (Claro / Escuro)
    if "tema" not in st.session_state:
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
    button[data-baseweb="tab"] {
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
    """, unsafe_allow_html=True)

    # Barra superior do login com Alternador de Tema no canto direito
    c_top_vazio, c_top_tema = st.columns([9, 1])
    with c_top_tema:
        icone_tema = "☀️" if is_dark else "🌙"
        help_tema = "Modo Claro" if is_dark else "Modo Escuro"
        if st.button(icone_tema, help=help_tema, key="btn_login_tema", use_container_width=True):
            st.session_state.tema = "light" if is_dark else "dark"
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

            if codigo_teste:
                st.markdown(f"""
                <div class="otp-display-box">
                    <div style="font-size: 0.75rem; color: #f59e0b; text-transform: uppercase; font-weight: 700; margin-bottom: 4px;">
                        🔑 Código de Verificação (Modo de Teste)
                    </div>
                    <div class="otp-code-text">{codigo_teste}</div>
                    <div style="font-size: 0.75rem; color: {text_muted}; margin-top: 4px;">
                        Copie os 6 dígitos acima e cole no campo abaixo
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
                            st.success("🎉 Conta verificada com sucesso! Bem-vindo(a) ao MathAI!")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(resultado["erro"])

            col_btn_reenviar, col_btn_voltar = st.columns(2)
            with col_btn_reenviar:
                if st.button("🔄 Reenviar Código", use_container_width=True, key="btn_reenviar_otp"):
                    res_reenvio = reenviar_codigo_otp(email_verif)
                    st.session_state.codigo_teste_otp = res_reenvio.get("codigo_teste", "")
                    st.info("Novo código gerado!")
                    st.rerun()

            with col_btn_voltar:
                if st.button("⬅️ Voltar para Login", use_container_width=True, key="btn_voltar_login"):
                    st.session_state.pop("verificando_email", None)
                    st.session_state.pop("codigo_teste_otp", None)
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)
            return

        # ── ABAS: LOGIN & CADASTRO ────────────────────────────────────────────
        aba = st.tabs(["🔑 Entrar", "✨ Criar Conta"])

        # ── 1. ABA LOGIN ───────────────────────────────────────────────────────
        with aba[0]:
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

            if tem_militar or "Cursinho" in c_escolaridade:
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

            if tem_vestibular or "Cursinho" in c_escolaridade or "Médio" in c_escolaridade:
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
                        st.session_state.codigo_teste_otp = resultado.get("codigo_teste", "")
                        st.toast("Código de verificação gerado!", icon="🔑")
                        st.rerun()
                    else:
                        st.error(resultado["erro"])
