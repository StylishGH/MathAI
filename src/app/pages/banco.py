"""
Página do Banco de Questões do MathAI.
Permite filtrar o acervo por matéria/banca/ano, inspecionar questões e gerar
Listas de Exercícios personalizadas ou Simulados Cronometrados com tempo configurável.
"""

import json
import time
import random
import streamlit as st
from src.database.db import listar_questoes
from src.app.components.question_view import render_question
from src.app.utils import extrair_enunciado_e_alternativas


def show():
    is_dark = (st.session_state.get("tema", "dark") == "dark")
    card_bg = "rgba(19, 17, 28, 0.88)" if is_dark else "#ffffff"
    card_border = "rgba(124, 58, 237, 0.35)" if is_dark else "#e2e8f0"
    text_main = "#f8fafc" if is_dark else "#0f172a"
    text_muted = "#94a3b8" if is_dark else "#64748b"
    card_shadow = "0.4" if is_dark else "0.06"

    st.markdown("## 📚 Banco de Questões & Gerador de Simulados")
    st.caption("Filtre o acervo por matéria ou banca para criar Listas de Exercícios ou Simulados Cronometrados personalizados.")

    questoes_rows = listar_questoes()
    if not questoes_rows:
        st.warning("⚠️ Nenhuma questão cadastrada no banco de dados.")
        return

    questoes = [dict(q) for q in questoes_rows]

    # 1. Barra de Filtros
    col_mat, col_banca, col_ano, col_busca = st.columns([1.8, 1.3, 1.1, 2.2])

    with col_mat:
        materias = ["Todas"] + sorted(list(set(q.get("materia", "") for q in questoes if q.get("materia"))))
        sel_materia = st.selectbox("Matéria:", materias, key="banco_filtro_materia")

    with col_banca:
        bancas = ["Todas"] + sorted(list(set(q.get("banca", "") for q in questoes if q.get("banca"))))
        sel_banca = st.selectbox("Banca:", bancas, key="banco_filtro_banca")

    with col_ano:
        anos = ["Todos"] + sorted(list(set(str(q.get("ano", "")) for q in questoes if q.get("ano"))), reverse=True)
        sel_ano = st.selectbox("Ano:", anos, key="banco_filtro_ano")

    with col_busca:
        busca_termo = st.text_input("🔍 Buscar no enunciado / tópico:", key="banco_filtro_busca").strip().lower()

    # Verifica se algum filtro está ativo
    tem_filtro = (
        sel_materia != "Todas" or
        sel_banca != "Todas" or
        sel_ano != "Todos" or
        bool(busca_termo)
    )
    mostrar_todas = st.session_state.get("banco_mostrar_todas", False)

    # 2. Estado Inicial Vazio (quando nenhum filtro foi selecionado)
    if not tem_filtro and not mostrar_todas:
        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1.5px dashed {'rgba(245, 158, 11, 0.4)' if is_dark else '#cbd5e1'};
                    border-radius: 16px; padding: 28px 24px; text-align: center; margin: 12px 0;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, {card_shadow});">
            <div style="font-size: 2.5rem; margin-bottom: 8px;">🎯</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: {text_main}; margin-bottom: 6px;">
                Nenhum filtro aplicado no acervo
            </div>
            <div style="font-size: 0.92rem; color: {text_muted}; max-width: 600px; margin: 0 auto 6px auto; line-height: 1.5;">
                Selecione uma <b>Matéria</b> (ex: <i>Álgebra, Geometria</i>), uma <b>Banca</b> (ex: <i>ESA</i>) ou pesquise acima para encontrar as questões e gerar sua <b>Lista Personalizada</b> ou <b>Simulado Cronometrado</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Funções de callback para aplicar atalhos antes da renderização dos widgets
        def _aplicar_atalho_esa():
            st.session_state.banco_filtro_materia = "Todas"
            st.session_state.banco_filtro_banca = "ESA"
            st.session_state.banco_filtro_ano = "2026"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = False

        def _aplicar_atalho_geo(materia_alvo):
            st.session_state.banco_filtro_materia = materia_alvo
            st.session_state.banco_filtro_banca = "Todas"
            st.session_state.banco_filtro_ano = "Todos"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = False

        def _aplicar_atalho_todas():
            st.session_state.banco_filtro_materia = "Todas"
            st.session_state.banco_filtro_banca = "Todas"
            st.session_state.banco_filtro_ano = "Todos"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = True

        geo_alvo = "Geometria Plana" if "Geometria Plana" in materias else (materias[1] if len(materias) > 1 else "Todas")

        # Atalhos rápidos de seleção em Cards Ricos
        st.markdown("##### ⚡ Atalhos Rápidos Recomendados:")
        c_at1, c_at2, c_at3 = st.columns(3)

        with c_at1:
            st.markdown(f"""
            <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-top: 3px solid #f59e0b;
                        border-radius: 14px; padding: 18px 16px; margin-bottom: 10px;
                        box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow}); text-align: center;">
                <div style="font-size: 2.2rem; margin-bottom: 8px;">🎖️</div>
                <div style="font-weight: 800; font-size: 1.05rem; color: {text_main}; margin-bottom: 4px;">Prova ESA 2026</div>
                <div style="font-size: 0.82rem; color: {text_muted}; min-height: 38px; line-height: 1.4;">
                    12 questões oficiais completas com gabarito e resolução
                </div>
                <div style="margin-top: 8px; font-size: 0.72rem; font-weight: 700; color: #fbbf24; background: rgba(245, 158, 11, 0.12); padding: 3px 10px; border-radius: 999px; display: inline-block;">
                    Simulado • 60 min
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.button(
                "🚀 Carregar Prova ESA 2026",
                key="btn_at_esa",
                use_container_width=True,
                type="primary",
                on_click=_aplicar_atalho_esa
            )

        with c_at2:
            st.markdown(f"""
            <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-top: 3px solid #7c3aed;
                        border-radius: 14px; padding: 18px 16px; margin-bottom: 10px;
                        box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow}); text-align: center;">
                <div style="font-size: 2.2rem; margin-bottom: 8px;">📐</div>
                <div style="font-weight: 800; font-size: 1.05rem; color: {text_main}; margin-bottom: 4px;">Foco em Geometria</div>
                <div style="font-size: 0.82rem; color: {text_muted}; min-height: 38px; line-height: 1.4;">
                    Geometria Plana e Espacial: cilindros, esferas e áreas
                </div>
                <div style="margin-top: 8px; font-size: 0.72rem; font-weight: 700; color: {'#c4b5fd' if is_dark else '#7c3aed'}; background: rgba(124, 58, 237, 0.15); padding: 3px 10px; border-radius: 999px; display: inline-block;">
                    Treino por Tópico
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.button(
                "🔍 Filtrar Geometria",
                key="btn_at_geo",
                use_container_width=True,
                on_click=_aplicar_atalho_geo,
                args=(geo_alvo,)
            )

        with c_at3:
            st.markdown(f"""
            <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-top: 3px solid #6366f1;
                        border-radius: 14px; padding: 18px 16px; margin-bottom: 10px;
                        box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow}); text-align: center;">
                <div style="font-size: 2.2rem; margin-bottom: 8px;">📚</div>
                <div style="font-weight: 800; font-size: 1.05rem; color: {text_main}; margin-bottom: 4px;">Acervo Completo</div>
                <div style="font-size: 0.82rem; color: {text_muted}; min-height: 38px; line-height: 1.4;">
                    Visualize todas as questões catalogadas no banco de dados
                </div>
                <div style="margin-top: 8px; font-size: 0.72rem; font-weight: 700; color: {'#a5b4fc' if is_dark else '#4f46e5'}; background: rgba(99, 102, 241, 0.15); padding: 3px 10px; border-radius: 999px; display: inline-block;">
                    Exploração Livre
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.button(
                "👀 Exibir Todo o Banco",
                key="btn_at_todas",
                use_container_width=True,
                on_click=_aplicar_atalho_todas
            )
        return

    # Se filtrou algo, desativa o flag manual de "mostrar todas"
    if tem_filtro:
        st.session_state.banco_mostrar_todas = False

    # 3. Aplica os Filtros
    filtradas = questoes
    if sel_materia != "Todas":
        filtradas = [q for q in filtradas if q.get("materia") == sel_materia]
    if sel_banca != "Todas":
        filtradas = [q for q in filtradas if q.get("banca") == sel_banca]
    if sel_ano != "Todos":
        filtradas = [q for q in filtradas if str(q.get("ano", "")) == sel_ano]
    if busca_termo:
        filtradas = [
            q for q in filtradas
            if busca_termo in q.get("enunciado", "").lower()
            or busca_termo in q.get("topico", "").lower()
            or busca_termo in str(q.get("subtopico", "")).lower()
        ]

    if not filtradas:
        st.info("🔍 Nenhuma questão encontrada com os filtros selecionados. Tente ajustar a busca.")
        return

    # 4. Gerenciamento de Seleção de Questões
    total_filtradas = len(filtradas)
    filtro_key_hash = f"{sel_materia}_{sel_banca}_{sel_ano}_{busca_termo}"

    # Inicializa estado de seleção para esse conjunto de filtros
    if "banco_selecionadas" not in st.session_state or st.session_state.get("banco_ultimo_filtro") != filtro_key_hash:
        st.session_state.banco_selecionadas = {q["id"]: True for q in filtradas}
        st.session_state.banco_ultimo_filtro = filtro_key_hash

    selecionadas_ids = [qid for qid, sel in st.session_state.banco_selecionadas.items() if sel and any(q["id"] == qid for q in filtradas)]
    qtd_selecionadas = len(selecionadas_ids)

    # 5. Painel de Ações: Criar Simulado ou Criar Lista
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="background: {card_bg}; border: 1.5px solid {'rgba(245, 158, 11, 0.4)' if is_dark else '#cbd5e1'};
                border-radius: 14px; padding: 16px 20px; margin-bottom: 18px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, {card_shadow});">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
            <div>
                <span style="font-size: 1.15rem; font-weight: 700; color: {text_main};">
                    🎯 {qtd_selecionadas} de {total_filtradas} questões selecionadas
                </span>
                <span style="font-size: 0.85rem; color: {text_muted}; margin-left: 12px;">
                    Personalize e inicie seu treino ou prova cronometrada
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab_simulado, tab_lista = st.tabs(["⏱️ Criar Simulado Cronometrado", "📝 Criar Lista de Exercícios"])

    # ── TAB 1: SIMULADO CRONOMETRADO ──────────────────────────────────────────
    with tab_simulado:
        col_s1, col_s2, col_s3 = st.columns([2.5, 1.5, 1.5])

        with col_s1:
            nome_default_sim = f"Simulado {sel_banca if sel_banca != 'Todas' else 'Personalizado'} ({qtd_selecionadas} Questões)"
            titulo_simulado = st.text_input("Nome do Simulado:", value=nome_default_sim, key="input_nome_simulado")

        with col_s2:
            # Sugestão de 5 min por questão ou 60 min para ESA
            tempo_sugerido = 60 if (sel_banca == "ESA" and qtd_selecionadas == 12) else max(10, qtd_selecionadas * 5)
            tempo_limite_min = st.number_input(
                "Tempo Limite (minutos):",
                min_value=5,
                max_value=360,
                value=tempo_sugerido,
                step=5,
                key="input_tempo_simulado"
            )

        with col_s3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            embaralhar = st.checkbox("🔀 Embaralhar ordem", value=False, key="chk_embaralhar_sim")

        # Botões rápidos de tempo com callback para evitar erro de widget já instanciado
        def _definir_tempo_simulado(minutos):
            st.session_state.input_tempo_simulado = minutos

        c_t1, c_t2, c_t3, c_t4, c_t5 = st.columns(5)
        with c_t1:
            st.button("⏱️ 30 min", use_container_width=True, on_click=_definir_tempo_simulado, args=(30,))
        with c_t2:
            st.button("⏱️ 45 min", use_container_width=True, on_click=_definir_tempo_simulado, args=(45,))
        with c_t3:
            st.button("⏱️ 60 min (Padrão ESA)", use_container_width=True, on_click=_definir_tempo_simulado, args=(60,))
        with c_t4:
            st.button("⏱️ 90 min", use_container_width=True, on_click=_definir_tempo_simulado, args=(90,))
        with c_t5:
            st.button("⏱️ 120 min", use_container_width=True, on_click=_definir_tempo_simulado, args=(120,))

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.button("🚀 Iniciar Simulado Agora", type="primary", use_container_width=True, disabled=(qtd_selecionadas == 0)):
            questoes_simulado = [q for q in filtradas if q["id"] in selecionadas_ids]
            if embaralhar:
                random.shuffle(questoes_simulado)

            st.session_state.modo_sessao = "simulado"
            st.session_state.simulado_config = {
                "titulo": titulo_simulado,
                "tempo_limite_min": tempo_limite_min,
                "tempo_inicio": time.time(),
                "questoes": questoes_simulado,
                "respostas": {},
                "marcadas_revisao": set(),
                "entregue": False,
                "tempo_total_gasto": 0
            }
            st.session_state.questao_idx = 0
            st.session_state.nav_page = "🎯 Resolver / Simulado"
            st.rerun()

    # ── TAB 2: LISTA DE EXERCÍCIOS ────────────────────────────────────────────
    with tab_lista:
        col_l1, col_l2 = st.columns([3, 1.5])
        with col_l1:
            nome_default_lista = f"Lista: {sel_materia if sel_materia != 'Todas' else 'Matemática'} ({qtd_selecionadas} Questões)"
            titulo_lista = st.text_input("Nome da Lista:", value=nome_default_lista, key="input_nome_lista")
        with col_l2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 Iniciar Resolução da Lista", type="primary", use_container_width=True, disabled=(qtd_selecionadas == 0)):
                questoes_lista = [q for q in filtradas if q["id"] in selecionadas_ids]
                st.session_state.modo_sessao = "lista"
                st.session_state.lista_config = {
                    "titulo": titulo_lista,
                    "questoes": questoes_lista
                }
                st.session_state.questao_idx = 0
                st.session_state.nav_page = "🎯 Resolver / Simulado"
                st.rerun()

    st.markdown("---")

    # 6. Controles de Seleção em Massa
    col_sel_all, col_des_all, _ = st.columns([1.5, 1.5, 3])
    with col_sel_all:
        if st.button("☑️ Selecionar Todas", use_container_width=True):
            for q in filtradas:
                st.session_state.banco_selecionadas[q["id"]] = True
            st.rerun()
    with col_des_all:
        if st.button("⬜ Desmarcar Todas", use_container_width=True):
            for q in filtradas:
                st.session_state.banco_selecionadas[q["id"]] = False
            st.rerun()

    # 7. Listagem das Questões Filtradas com Checkboxes e Expansores
    for idx, q in enumerate(filtradas):
        q_id = q["id"]
        materia = q.get("materia", "")
        topico = q.get("topico", "")
        banca = q.get("banca", "")
        ano = q.get("ano", "")
        dificuldade = q.get("dificuldade")
        dif_str = f"Dificuldade: {dificuldade}" if dificuldade is not None else "Dificuldade: Não calibrada"
        banca_ano = f"{banca} {ano}" if banca and ano else (banca or str(ano or ""))

        col_check, col_card = st.columns([0.08, 0.92])

        with col_check:
            is_checked = st.session_state.banco_selecionadas.get(q_id, True)
            check_val = st.checkbox(
                " ",
                value=is_checked,
                key=f"chk_q_{q_id}",
                label_visibility="collapsed"
            )
            if check_val != is_checked:
                st.session_state.banco_selecionadas[q_id] = check_val
                st.rerun()

        with col_card:
            titulo_expander = f"#{q_id:02d} • {materia} — {topico} {f'({banca_ano})' if banca_ano else ''}"
            with st.expander(titulo_expander, expanded=(idx == 0 and len(filtradas) <= 3)):
                render_question(q, mostrar_alternativas=False)

                # Alternativas interativas: o gabarito só aparece quando o aluno marcar ou pedir para revelar
                _, alternativas = extrair_enunciado_e_alternativas(q.get("enunciado", ""))
                gabarito_oficial = str(q.get("gabarito", "")).strip().upper()

                if alternativas:
                    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
                    st.markdown("##### 📝 Escolha uma alternativa para testar seu raciocínio:")
                    
                    opcoes_alt = list(alternativas.keys())
                    resp_escolhida = st.radio(
                        "Alternativas da questão:",
                        options=opcoes_alt,
                        format_func=lambda k: f"({k}) {alternativas[k]}",
                        index=None,
                        key=f"banco_teste_resp_{q_id}",
                        label_visibility="collapsed"
                    )

                    # Chaves de confirmação
                    chave_confirmada = f"confirmada_resp_{q_id}"
                    chave_ultima_resp = f"ultima_resp_{q_id}"

                    # Se o usuário trocou a alternativa marcada, desfaz a confirmação anterior para ele ter que clicar novamente
                    if st.session_state.get(chave_ultima_resp) != resp_escolhida:
                        st.session_state[chave_confirmada] = False
                        st.session_state[chave_ultima_resp] = resp_escolhida

                    col_conf_btn, col_rev_chk = st.columns([1.6, 2.5])
                    with col_conf_btn:
                        if st.button(
                            "🎯 Confirmar Resposta",
                            key=f"btn_conf_{q_id}",
                            type="primary",
                            use_container_width=True,
                            disabled=(resp_escolhida is None)
                        ):
                            st.session_state[chave_confirmada] = True
                            st.rerun()

                    with col_rev_chk:
                        revelar_direto = st.checkbox("👁️ Revelar gabarito sem responder", key=f"rev_gab_{q_id}")

                    foi_confirmada = st.session_state.get(chave_confirmada, False)

                    if foi_confirmada and resp_escolhida is not None:
                        if resp_escolhida.strip().upper() == gabarito_oficial:
                            st.markdown(f"""
                            <div style="background: rgba(34, 197, 94, 0.12); border: 1.5px solid #22c55e;
                                        border-radius: 10px; padding: 12px 16px; margin: 10px 0; display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.3rem;">🎉</span>
                                <div>
                                    <div style="font-weight: 800; color: {'#15803d' if not is_dark else '#4ade80'}; font-size: 0.95rem;">
                                        Resposta Correta! Você marcou ({resp_escolhida}).
                                    </div>
                                    <div style="font-size: 0.85rem; color: {text_muted};">
                                        Gabarito Oficial Confirmado: <b style="color: {'#15803d' if not is_dark else '#4ade80'};">({gabarito_oficial})</b>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown(f"""
                            <div style="background: rgba(239, 68, 68, 0.1); border: 1.5px solid #ef4444;
                                        border-radius: 10px; padding: 12px 16px; margin: 10px 0; display: flex; align-items: center; gap: 10px;">
                                <span style="font-size: 1.3rem;">❌</span>
                                <div>
                                    <div style="font-weight: 800; color: {'#b91c1c' if not is_dark else '#f87171'}; font-size: 0.95rem;">
                                        Você marcou ({resp_escolhida}). Resposta incorreta.
                                    </div>
                                    <div style="font-size: 0.85rem; color: {text_muted};">
                                        O Gabarito Oficial desta questão é: <b style="color: {'#b45309' if not is_dark else '#fbbf24'};">({gabarito_oficial})</b>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    elif revelar_direto:
                        st.markdown(f"**Gabarito Oficial:** `{gabarito_oficial}`")

                st.markdown("<br>", unsafe_allow_html=True)
                col_meta1, col_meta2 = st.columns([3, 1])

                with col_meta1:
                    estrategias_raw = q.get("estrategias_esperadas", "[]")
                    try:
                        estrategias = json.loads(estrategias_raw) if isinstance(estrategias_raw, str) else (estrategias_raw or [])
                    except Exception:
                        estrategias = []

                    dif_badge = f'<span style="background: rgba(124, 58, 237, 0.12); color: {"#6d28d9" if not is_dark else "#c4b5fd"}; border: 1px solid rgba(124, 58, 237, 0.3); padding: 2px 8px; border-radius: 6px; font-size: 0.82rem; font-weight: 600;">{dif_str}</span>'
                    st.markdown(f"**Classificação:** {dif_badge}", unsafe_allow_html=True)

                    if estrategias:
                        badges_est = "".join(
                            f'<span style="background: rgba(245, 158, 11, {0.12 if not is_dark else 0.18}); '
                            f'color: {"#b45309" if not is_dark else "#fbbf24"}; '
                            f'border: 1px solid rgba(245, 158, 11, {0.4 if not is_dark else 0.45}); '
                            f'padding: 3px 10px; border-radius: 6px; font-size: 0.82rem; font-weight: 700; '
                            f'margin-right: 6px; margin-bottom: 4px; display: inline-block;">'
                            f'💡 {e}'
                            f'</span>'
                            for e in estrategias
                        )
                        st.markdown(f"<div style='margin-top: 8px;'><b>Estratégias Catalogadas:</b><div style='margin-top: 6px;'>{badges_est}</div></div>", unsafe_allow_html=True)

                with col_meta2:
                    if st.button(f"🎯 Treinar Esta Questão", key=f"btn_treinar_unica_{q_id}", use_container_width=True):
                        st.session_state.modo_sessao = "lista"
                        st.session_state.lista_config = {
                            "titulo": f"Questão Individual #{q_id:02d}",
                            "questoes": [q]
                        }
                        st.session_state.questao_idx = 0
                        st.session_state.nav_page = "🎯 Resolver / Simulado"
                        st.rerun()
