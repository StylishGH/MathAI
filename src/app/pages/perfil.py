"""
MathAI - Página de Perfil do Usuário
Visualização e edição completa de perfil, dados acadêmicos,
faculdade, curso, objetivos e concursos/vestibulares foco.
"""

import streamlit as st
from src.database.users import (
    buscar_usuario_por_id,
    atualizar_perfil_usuario,
    buscar_endereco_por_cep,
    formatar_cpf,
    validar_cpf
)

ESCOLARIDADE_OPCOES = [
    "Ensino Fundamental (em andamento / concluído)",
    "Ensino Médio (em andamento / concluído)",
    "Cursinho Pré-Vestibular / Pré-Militar",
    "Ensino Superior (Graduação)",
    "Pós-Graduação / Especialização",
    "Mestrado",
    "Doutorado"
]

FACULDADES_BRASIL = [
    "USP - Universidade de São Paulo",
    "UNICAMP - Universidade Estadual de Campinas",
    "UFRJ - Universidade Federal do Rio de Janeiro",
    "UFF - Universidade Federal Fluminense",
    "UFMG - Universidade Federal de Minas Gerais",
    "UNESP - Universidade Estadual Paulista",
    "UNIFESP - Universidade Federal de São Paulo",
    "UFRGS - Universidade Federal do Rio Grande do Sul",
    "UFSC - Universidade Federal de Santa Catarina",
    "UFPR - Universidade Federal do Paraná",
    "UnB - Universidade de Brasília",
    "UFPE - Universidade Federal de Pernambuco",
    "UFC - Universidade Federal do Ceará",
    "UFBA - Universidade Federal da Bahia",
    "UFSCar - Universidade Federal de São Carlos",
    "ITA - Instituto Tecnológico de Aeronáutica",
    "IME - Instituto Militar de Engenharia",
    "PUC-Rio - Pontifícia Universidade Católica do Rio",
    "PUC-SP - Pontifícia Universidade Católica de SP",
    "FGV - Fundação Getulio Vargas",
    "Mackenzie - Universidade Presbiteriana Mackenzie",
    "UERJ - Universidade do Estado do Rio de Janeiro",
    "CEFET/RJ - Centro Federal de Educ. Tecnológica",
    "IF - Instituto Federal de Educação, Ciência e Tecnologia",
    "Outra Faculdade / Universidade"
]

CONCURSOS_MILITARES = [
    "EFOMM (Oficiais da Marinha Mercante)",
    "Escola Naval (EN)",
    "AFA (Academia da Força Aérea)",
    "EsPCEx / AMAN (Exército)",
    "ESA (Sargentos do Exército)",
    "EEAR (Especialistas de Aeronáutica)",
    "Colégio Naval (CN)",
    "EPCAR (Cadetes do Ar)",
    "IME (Engenharia Militar)",
    "ITA (Engenharia Aeronáutica)",
    "Fuzileiro Naval / Aprendiz-Marinheiro",
    "Outro Concurso Militar"
]

CONCURSOS_VESTIBULARES = [
    "ENEM",
    "FUVEST (USP)",
    "UNICAMP",
    "UNESP",
    "UERJ",
    "UFRGS",
    "UFPR",
    "UFSC",
    "Outro Vestibular"
]

MOTIVOS_OPCOES = {
    "melhoria_propria": "📈 Quero melhorar na Matemática por conta própria",
    "concurso_militar": "🎖️ Concurso Militar (ESA, EsPCEx, AFA, EFOMM, IME, ITA...)",
    "enem_vestibular": "📚 ENEM / Vestibular",
    "professor": "👨‍🏫 Sou professor(a) de Matemática",
    "olimpiada": "🏆 Olimpíadas de Matemática (OBMEP, OBM...)",
    "uso_profissional": "💼 Uso profissional / área técnica",
    "curiosidade": "🔍 Curiosidade / aprendizado geral"
}


def show():
    is_dark = st.session_state.get("tema", "dark") == "dark"
    bg_card = "linear-gradient(135deg, rgba(19, 17, 28, 0.96) 0%, rgba(10, 10, 15, 0.98) 100%)" if is_dark else "#ffffff"
    border_card = "rgba(124, 58, 237, 0.35)" if is_dark else "#cbd5e1"
    text_main = "#f8fafc" if is_dark else "#0f172a"
    text_muted = "#94a3b8" if is_dark else "#64748b"
    gold_accent = "#fbbf24" if is_dark else "#d97706"
    gold_border = "rgba(245, 158, 11, 0.45)" if is_dark else "rgba(217, 119, 6, 0.5)"
    shadow_card = "0 8px 30px rgba(0, 0, 0, 0.45)" if is_dark else "0 4px 20px rgba(0, 0, 0, 0.05)"

    usuario_sessao = st.session_state.get("usuario_logado") or {}
    user_id = usuario_sessao.get("id")

    if not user_id:
        st.warning("Nenhum usuário logado. Por favor faça login.")
        return

    if st.session_state.pop("perfil_salvo_sucesso", False):
        st.success("🎉 Perfil e preferências atualizados com sucesso!")
        st.balloons()

    # Busca dados mais recentes do banco
    usuario_db = buscar_usuario_por_id(user_id)
    if usuario_db:
        usuario = usuario_db
        st.session_state.usuario_logado = usuario_db
    else:
        usuario = usuario_sessao

    # Cabeçalho com Card de Resumo do Usuário
    nome_completo = usuario.get("nome") or "Aluno"
    email_usuario = usuario.get("email") or ""
    iniciais = "".join(p[0].upper() for p in nome_completo.split()[:2])
    faculdade_atual = usuario.get("faculdade") or ""
    curso_atual = usuario.get("curso") or ""
    escolaridade_atual = usuario.get("escolaridade") or ""
    concursos_foco_atual = usuario.get("concursos_foco") or []

    # Subtítulo inteligente
    if faculdade_atual and curso_atual:
        tag_subtitulo = f"{faculdade_atual.split(' - ')[0]} • {curso_atual}"
    elif faculdade_atual:
        tag_subtitulo = faculdade_atual.split(' - ')[0]
    elif concursos_foco_atual:
        tag_subtitulo = f"Foco: {concursos_foco_atual[0]}"
    elif escolaridade_atual:
        tag_subtitulo = escolaridade_atual
    else:
        tag_subtitulo = "Estudante MathAI"

    st.markdown(f"""
    <div style="background: {bg_card}; border: 1.5px solid {border_card}; border-radius: 18px;
                padding: 22px 26px; box-shadow: {shadow_card}; margin-bottom: 24px;
                display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 16px;">
        <div style="display: flex; align-items: center; gap: 18px;">
            <div style="width: 64px; height: 64px; min-width: 64px; border-radius: 50%;
                        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
                        border: 2.5px solid {gold_border}; color: white; font-weight: 800;
                        display: flex; align-items: center; justify-content: center; font-size: 1.5rem;
                        box-shadow: 0 0 16px rgba(245, 158, 11, 0.35);">
                {iniciais}
            </div>
            <div>
                <h2 style="margin: 0; font-size: 1.45rem; font-weight: 800; color: {text_main};">
                    {nome_completo}
                </h2>
                <div style="display: flex; align-items: center; gap: 10px; margin-top: 4px; flex-wrap: wrap;">
                    <span style="font-size: 0.85rem; color: {text_muted};">{email_usuario}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; padding: 2px 10px; border-radius: 9999px;
                                 background: {'rgba(245, 158, 11, 0.15)' if is_dark else 'rgba(217, 119, 6, 0.12)'};
                                 color: {gold_accent}; border: 1px solid {gold_border};">
                        {tag_subtitulo}
                    </span>
                    <span style="font-size: 0.72rem; color: {text_muted};">ID #{user_id}</span>
                </div>
            </div>
        </div>
        <div>
            <span style="font-size: 0.82rem; color: {text_muted}; background: {'rgba(124, 58, 237, 0.12)' if is_dark else 'rgba(124, 58, 237, 0.08)'};
                         padding: 6px 14px; border-radius: 8px; border: 1px solid rgba(124, 58, 237, 0.25);">
                🔒 Perfil Verificado
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── FORMULÁRIO DE EDIÇÃO ──────────────────────────────────────────────────
    st.markdown("### ⚙️ Configurações & Personalização do Perfil")
    st.caption("Mantenha seus dados atualizados para personalizarmos simulados, questões recomendadas e diagnósticos cognitivos.")

    col_esq, col_dir = st.columns([1, 1], gap="large")

    # ── COLUNA ESQUERDA: DADOS PESSOAIS & ENDEREÇO ────────────────────────────
    with col_esq:
        st.markdown(f"""
        <div style="font-size: 1.08rem; font-weight: 700; color: {text_main}; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <span>👤</span> Dados Pessoais & Contato
        </div>
        """, unsafe_allow_html=True)

        novo_nome = st.text_input(
            "Nome Completo *",
            value=usuario.get("nome") or "",
            placeholder="Seu nome completo",
            key="perfil_nome"
        )

        col_id_cel1, col_id_cel2 = st.columns([1, 1.8])
        with col_id_cel1:
            idade_val = int(usuario.get("idade") or 18)
            idade_val = max(10, min(100, idade_val))
            nova_idade = st.number_input(
                "Idade",
                min_value=10,
                max_value=100,
                value=idade_val,
                key="perfil_idade"
            )
        with col_id_cel2:
            novo_celular = st.text_input(
                "📱 Celular / WhatsApp",
                value=usuario.get("celular") or "",
                placeholder="(21) 99999-9999",
                key="perfil_celular"
            )

        col_cpf1, col_cpf2 = st.columns([2, 1.2])
        with col_cpf1:
            novo_cpf = st.text_input(
                "🪪 CPF",
                value=usuario.get("cpf") or "",
                placeholder="000.000.000-00",
                key="perfil_cpf"
            )
        with col_cpf2:
            st.text_input("📧 E-mail (login)", value=usuario.get("email") or "", disabled=True, key="perfil_email_disabled")

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size: 1.08rem; font-weight: 700; color: {text_main}; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <span>📍</span> Localização & Endereço
        </div>
        """, unsafe_allow_html=True)

        col_cep_in, col_cep_btn = st.columns([2, 1])
        with col_cep_in:
            novo_cep = st.text_input(
                "CEP",
                value=usuario.get("cep") or "",
                placeholder="00000-000",
                key="perfil_input_cep"
            )
        with col_cep_btn:
            st.write("")
            st.write("")
            if st.button("🔍 Buscar CEP", use_container_width=True, key="btn_perfil_buscar_cep"):
                if novo_cep:
                    endereco_viacep = buscar_endereco_por_cep(novo_cep)
                    if endereco_viacep:
                        st.session_state["perfil_logradouro"] = endereco_viacep.get("logradouro", "")
                        st.session_state["perfil_bairro"] = endereco_viacep.get("bairro", "")
                        st.session_state["perfil_cidade"] = endereco_viacep.get("cidade", "")
                        st.session_state["perfil_estado"] = endereco_viacep.get("estado", "")
                        st.toast("Endereço preenchido via ViaCEP!", icon="📍")
                        st.rerun()
                    else:
                        st.warning("CEP não localizado. Preencha manualmente.")

        col_rua, col_num = st.columns([3, 1])
        with col_rua:
            novo_logradouro = st.text_input(
                "Logradouro / Rua",
                value=usuario.get("logradouro") or "",
                placeholder="Rua / Avenida...",
                key="perfil_logradouro"
            )
        with col_num:
            novo_numero = st.text_input(
                "Número",
                value=usuario.get("numero") or "",
                placeholder="Ex: 100",
                key="perfil_numero"
            )

        col_bair, col_cidade, col_estado = st.columns([1.5, 2, 1])
        with col_bair:
            novo_bairro = st.text_input(
                "Bairro",
                value=usuario.get("bairro") or "",
                placeholder="Bairro",
                key="perfil_bairro"
            )
        with col_cidade:
            novo_cidade = st.text_input(
                "Cidade",
                value=usuario.get("cidade") or "",
                placeholder="Cidade",
                key="perfil_cidade"
            )
        with col_estado:
            novo_estado = st.text_input(
                "UF",
                value=usuario.get("estado") or "",
                placeholder="RJ",
                max_chars=2,
                key="perfil_estado"
            )

    # ── COLUNA DIREITA: ESCOLARIDADE, FACULDADE, CURSO & CONCURSOS FOCO ──────
    with col_dir:
        st.markdown(f"""
        <div style="font-size: 1.08rem; font-weight: 700; color: {text_main}; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <span>🎓</span> Formação Acadêmica & Escolaridade
        </div>
        """, unsafe_allow_html=True)

        escolaridade_salva = usuario.get("escolaridade") or ""
        indice_esc = 0
        if escolaridade_salva in ESCOLARIDADE_OPCOES:
            indice_esc = ESCOLARIDADE_OPCOES.index(escolaridade_salva)
        elif "superior" in escolaridade_salva.lower() or "gradua" in escolaridade_salva.lower():
            indice_esc = 3

        nova_escolaridade = st.selectbox(
            "Nível de Escolaridade Atual *",
            options=ESCOLARIDADE_OPCOES,
            index=indice_esc,
            key="perfil_escolaridade"
        )

        eh_ensino_superior = nova_escolaridade in [
            "Ensino Superior (Graduação)",
            "Pós-Graduação / Especialização",
            "Mestrado",
            "Doutorado"
        ]

        nova_faculdade = None
        novo_curso = None

        if eh_ensino_superior:
            st.markdown(f"""
            <div style="background: {'rgba(124, 58, 237, 0.1)' if is_dark else 'rgba(124, 58, 237, 0.05)'};
                        border: 1px dashed {'rgba(124, 58, 237, 0.35)' if is_dark else '#cbd5e1'};
                        border-radius: 12px; padding: 14px; margin-top: 6px; margin-bottom: 10px;">
                <div style="font-size: 0.84rem; font-weight: 700; color: {'#c7d2fe' if is_dark else '#6d28d9'}; margin-bottom: 8px;">
                    🏛️ Dados Universitários / Pós-Graduação
                </div>
            """, unsafe_allow_html=True)

            faculdade_salva = usuario.get("faculdade") or ""
            faculdade_eh_outra = False
            indice_fac = 0

            # Procura faculdade na lista
            encontrado = False
            for idx, fac_item in enumerate(FACULDADES_BRASIL):
                if faculdade_salva and (faculdade_salva.lower() in fac_item.lower() or fac_item.lower() in faculdade_salva.lower()):
                    indice_fac = idx
                    encontrado = True
                    break

            if faculdade_salva and not encontrado:
                indice_fac = len(FACULDADES_BRASIL) - 1  # "Outra Faculdade / Universidade"
                faculdade_eh_outra = True

            faculdade_sel = st.selectbox(
                "Instituição de Ensino Superior *",
                options=FACULDADES_BRASIL,
                index=indice_fac,
                key="perfil_sel_faculdade"
            )

            if faculdade_sel == "Outra Faculdade / Universidade" or faculdade_eh_outra:
                valor_outra = faculdade_salva if (faculdade_salva and faculdade_salva not in FACULDADES_BRASIL) else ""
                faculdade_custom = st.text_input(
                    "Nome da sua Faculdade / Universidade",
                    value=valor_outra,
                    placeholder="Ex: UERJ, PUC-Minas, Estácio, etc.",
                    key="perfil_faculdade_custom"
                )
                nova_faculdade = faculdade_custom.strip() if faculdade_custom else "Outra Faculdade"
            else:
                nova_faculdade = faculdade_sel

            novo_curso = st.text_input(
                "Curso / Graduação / Área de Estudo *",
                value=usuario.get("curso") or "",
                placeholder="Ex: Matemática, Engenharia Elétrica, Medicina, Economia...",
                key="perfil_curso"
            )

            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size: 1.08rem; font-weight: 700; color: {text_main}; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
            <span>🎯</span> Motivações & Concursos Foco (Personalização)
        </div>
        """, unsafe_allow_html=True)

        st.caption("Selecione seus objetivos para que a plataforma priorize listas e simulados direcionados:")

        # Motivos gerais
        motivos_salvos = usuario.get("motivos") or []
        novos_motivos = []
        for chave, label in MOTIVOS_OPCOES.items():
            marcado = chave in motivos_salvos
            if st.checkbox(label, value=marcado, key=f"perfil_motivo_{chave}"):
                novos_motivos.append(chave)

        # Segmentação Específica: Concursos Militares e Vestibulares
        tem_foco_militar = "concurso_militar" in novos_motivos
        tem_foco_vestibular = "enem_vestibular" in novos_motivos
        foco_salvo = usuario.get("concursos_foco") or []

        # Sempre oferece os campos se selecionado ou se o usuário estiver em cursinho/médio
        concursos_foco_selecionados = []

        if tem_foco_militar:
            st.markdown(f"""
            <div style="margin-top: 10px; font-size: 0.88rem; font-weight: 700; color: {'#fbbf24' if is_dark else '#b45309'};">
                🎖️ Concursos Militares de Foco (selecione os seus):
            </div>
            """, unsafe_allow_html=True)

            militares_defaults = [c for c in CONCURSOS_MILITARES if any(f.lower() in c.lower() for f in foco_salvo)]
            sel_militares = st.multiselect(
                "Selecione seus concursos militares de interesse",
                options=CONCURSOS_MILITARES,
                default=militares_defaults,
                key="perfil_sel_militares"
            )
            concursos_foco_selecionados.extend(sel_militares)
            if "Outro Concurso Militar" in sel_militares:
                outros = [f for f in foco_salvo if f not in CONCURSOS_MILITARES and f not in CONCURSOS_VESTIBULARES]
                val_outro_m = outros[0] if outros else ""
                outro_m = st.text_input("Qual outro concurso militar?", value=val_outro_m, key="perfil_outro_militar")
                if outro_m:
                    concursos_foco_selecionados.append(outro_m)

        if tem_foco_vestibular:
            st.markdown(f"""
            <div style="margin-top: 10px; font-size: 0.88rem; font-weight: 700; color: {'#60a5fa' if is_dark else '#1d4ed8'};">
                📚 Vestibulares de Foco:
            </div>
            """, unsafe_allow_html=True)

            vestibulares_defaults = [v for v in CONCURSOS_VESTIBULARES if any(f.lower() in v.lower() for f in foco_salvo)]
            sel_vestibulares = st.multiselect(
                "Selecione seus vestibulares de interesse",
                options=CONCURSOS_VESTIBULARES,
                default=vestibulares_defaults,
                key="perfil_sel_vestibulares"
            )
            concursos_foco_selecionados.extend(sel_vestibulares)
            if "Outro Vestibular" in sel_vestibulares:
                outros = [f for f in foco_salvo if f not in CONCURSOS_MILITARES and f not in CONCURSOS_VESTIBULARES]
                val_outro_v = outros[-1] if outros else ""
                outro_v = st.text_input("Qual outro vestibular?", value=val_outro_v, key="perfil_outro_vestibular")
                if outro_v:
                    concursos_foco_selecionados.append(outro_v)

    # ── BOTÃO DE SALVAR ───────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("---")
    st.markdown("#### 🔒 Privacidade e Consentimento de Dados")
    st.markdown("<div style='font-size: 0.9em; color: #64748b; margin-bottom: 10px;'>Visando o futuro da plataforma, o MathAI separa estritamente o que são <b>dados observados</b> (suas resoluções, respostas e tempo) de <b>dados derivados</b> (diagnóstico da IA e estimativa de dificuldade). Precisamos do seu consentimento para armazenar e utilizar seus dados observados (de forma anônima) no treinamento das futuras IAs do projeto.</div>", unsafe_allow_html=True)
    consentimento_atual = bool(usuario.get('consentimento_dados', 0))
    novo_consentimento = st.checkbox(
        "Autorizo o armazenamento e o uso anônimo das minhas resoluções para desenvolvimento e treinamento do MathAI.", 
        value=consentimento_atual, 
        key="check_consentimento"
    )

    c_save_esq, c_save_btn, c_save_dir = st.columns([1, 2, 1])

    with c_save_btn:
        if st.button("💾 Salvar Alterações no Perfil", type="primary", use_container_width=True, key="btn_salvar_perfil"):
            erros = []
            if not novo_nome.strip():
                erros.append("O campo Nome Completo não pode estar vazio.")
            if novo_cpf and not validar_cpf(novo_cpf):
                erros.append("O CPF informado é inválido. Verifique os números digitados.")
            if not novos_motivos:
                erros.append("Selecione pelo menos um motivo / objetivo de estudo.")

            if erros:
                for erro in erros:
                    st.error(erro)
            else:
                res = atualizar_perfil_usuario(
                    usuario_id=user_id,
                    nome=novo_nome.strip(),
                    celular=novo_celular.strip() if novo_celular else None,
                    cpf=novo_cpf.strip() if novo_cpf else None,
                    cep=novo_cep.strip() if novo_cep else None,
                    logradouro=novo_logradouro.strip() if novo_logradouro else None,
                    numero=novo_numero.strip() if novo_numero else None,
                    bairro=novo_bairro.strip() if novo_bairro else None,
                    cidade=novo_cidade.strip() if novo_cidade else None,
                    estado=novo_estado.strip() if novo_estado else None,
                    escolaridade=nova_escolaridade,
                    faculdade=nova_faculdade if eh_ensino_superior else None,
                    curso=novo_curso.strip() if (eh_ensino_superior and novo_curso) else None,
                    motivos=novos_motivos,
                    concursos_foco=concursos_foco_selecionados
                )

                if res["ok"]:
                    # Atualiza os dados na sessão
                    usuario_atualizado = buscar_usuario_por_id(user_id)
                    st.session_state.usuario_logado = usuario_atualizado
                    st.session_state.perfil_salvo_sucesso = True
                    st.toast("Perfil e preferências salvos com sucesso!", icon="💾")
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar: {res.get('erro')}")
