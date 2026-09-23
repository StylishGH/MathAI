"""
Página do Treinador / Modo Resolução do MathAI.
Atua como o player interativo para:
1. Simulados Cronometrados (com contagem regressiva, marcação de questões e entrega com relatório).
2. Listas de Exercícios Personalizadas (com feedback imediato, dicas socráticas e análise de IA).
3. Modo Standby / Treino Livre.
"""

import time
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from src.database.db import listar_questoes
from src.database.attempts import registrar_tentativa
from src.app.components.question_view import render_question
from src.app.components.feedback_form import render_resolution_form
from src.app.utils import extrair_enunciado_e_alternativas, e_questao_discursiva


def show():
    is_dark = (st.session_state.get("tema", "dark") == "dark")
    card_bg = "rgba(19, 17, 28, 0.88)" if is_dark else "#ffffff"
    card_border = "rgba(124, 58, 237, 0.35)" if is_dark else "#e2e8f0"
    text_main = "#f8fafc" if is_dark else "#0f172a"
    text_muted = "#94a3b8" if is_dark else "#64748b"
    card_shadow = "0.4" if is_dark else "0.06"

    modo_sessao = st.session_state.get("modo_sessao", None)

    # ═════════════════════════════════════════════════════════════════════════
    # MODO 1: SIMULADO CRONOMETRADO
    # ═════════════════════════════════════════════════════════════════════════
    if modo_sessao == "simulado":
        sim = st.session_state.get("simulado_config")
        if not sim or not sim.get("questoes"):
            st.session_state.modo_sessao = None
            st.rerun()
            return

        questoes = sim["questoes"]
        total_q = len(questoes)

        # ── SUB-ESTADO: SIMULADO ENTREGUE (RELATÓRIO DE DESEMPENHO) ──────────
        if sim.get("entregue", False):
            st.markdown(f"## 🏁 Resultado: {sim.get('titulo', 'Simulado')}")
            st.caption("Confira o gabarito oficial, seu aproveitamento por área e o diagnóstico das questões.")

            # Cálculo de estatísticas
            respostas = sim.get("respostas", {})
            acertos = 0
            por_materia = {}

            for q in questoes:
                qid = q["id"]
                mat = q.get("materia", "Geral")
                gab = str(q.get("gabarito", "")).strip().upper()
                resp = str(respostas.get(qid, "")).strip().upper()

                if mat not in por_materia:
                    por_materia[mat] = {"total": 0, "acertos": 0}
                por_materia[mat]["total"] += 1

                if resp and resp == gab:
                    acertos += 1
                    por_materia[mat]["acertos"] += 1

            pct_acerto = (acertos / total_q * 100) if total_q > 0 else 0
            tempo_gasto = sim.get("tempo_total_gasto", 0)
            m_gasto = tempo_gasto // 60
            s_gasto = tempo_gasto % 60
            tempo_formatado = f"{m_gasto}m {s_gasto:02d}s"

            # Cards de Métricas Principais
            c_m1, c_m2, c_m3 = st.columns(3)
            with c_m1:
                st.metric("Pontuação Final", f"{acertos} / {total_q}", f"{pct_acerto:.1f}% de aproveitamento")
            with c_m2:
                st.metric("Tempo Utilizado", tempo_formatado, f"Limite: {sim.get('tempo_limite_min', 60)} min")
            with c_m3:
                taxa_str = "Excelente! 🚀" if pct_acerto >= 75 else ("Bom desempenho 👍" if pct_acerto >= 50 else "Atenção aos tópicos ⚠️")
                st.metric("Status Cognitivo", taxa_str)

            st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

            # Desempenho por Tópico / Matéria
            st.markdown("##### 📊 Desempenho por Matéria no Simulado:")
            cols_mat = st.columns(min(len(por_materia), 4) or 1)
            for i, (mat, dados) in enumerate(por_materia.items()):
                with cols_mat[i % len(cols_mat)]:
                    pct_mat = (dados["acertos"] / dados["total"] * 100) if dados["total"] > 0 else 0
                    st.markdown(f"""
                    <div style="background: {card_bg}; border: 1px solid {card_border};
                                border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;
                                box-shadow: 0 2px 8px rgba(0,0,0,{card_shadow});">
                        <div style="font-size: 0.82rem; color: {text_muted}; font-weight: 600;">{mat}</div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #fbbf24; margin-top: 2px;">
                            {dados['acertos']}/{dados['total']} <span style="font-size: 0.8rem; color: {'#a78bfa' if is_dark else '#7c3aed'};">({pct_mat:.0f}%)</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("##### 🔍 Revisão Questão a Questão:")

            for idx, q in enumerate(questoes):
                qid = q["id"]
                gab = str(q.get("gabarito", "")).strip().upper()
                resp = str(respostas.get(qid, "")).strip().upper()
                acertou = (resp == gab)
                status_icon = "✅" if acertou else "❌"
                status_texto = f"Acertou (marcou {resp})" if acertou else (f"Errou (marcou {resp or 'Em branco'}, gabarito: {gab})")

                with st.expander(f"Questão #{idx+1:02d} (ID #{qid:02d}) • {status_icon} {status_texto}"):
                    render_question(q, mostrar_alternativas=True)
                    st.markdown(f"**Sua Resposta:** `{resp or 'Não respondeu'}` | **Gabarito Oficial:** `{gab}`")

            st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if st.button("🔄 Refazer este Simulado", use_container_width=True):
                    sim["respostas"] = {}
                    sim["marcadas_revisao"] = set()
                    sim["entregue"] = False
                    sim["tempo_inicio"] = time.time()
                    st.session_state.questao_idx = 0
                    st.rerun()
            with col_b2:
                if st.button("📚 Criar Novo Simulado no Banco", type="primary", use_container_width=True):
                    st.session_state.modo_sessao = None
                    st.session_state.nav_page = "📚 Banco & Listas"
                    st.rerun()
            with col_b3:
                if st.button("📊 Ver Perfil Cognitivo Completo", use_container_width=True):
                    st.session_state.nav_page = "📊 Perfil Cognitivo"
                    st.rerun()
            return

        # ── SUB-ESTADO: SIMULADO EM ANDAMENTO (CRONÔMETRO ATIVO) ──────────────
        # Autorefresh a cada 1 segundo para atualizar o timer em tempo real
        st_autorefresh(interval=1000, limit=None, key="simulado_timer_refresh")

        tempo_limite_s = sim["tempo_limite_min"] * 60
        tempo_decorrido = int(time.time() - sim["tempo_inicio"])
        tempo_restante_s = max(0, tempo_limite_s - tempo_decorrido)

        # Se o tempo esgotou, entrega automaticamente
        if tempo_restante_s <= 0:
            st.warning("⏰ O tempo limite do simulado esgotou! Finalizando prova...")
            _finalizar_simulado(sim, tempo_limite_s)
            st.rerun()
            return

        # Header do Simulado em Execução
        m_rest = tempo_restante_s // 60
        s_rest = tempo_restante_s % 60
        cor_timer = "#ef4444" if tempo_restante_s < 300 else "#fbbf24"
        respostas = sim.setdefault("respostas", {})
        marcadas = sim.setdefault("marcadas_revisao", set())

        # Linha Superior do Simulado: Título à esquerda, Cronômetro à direita
        col_s_tit, col_s_tim = st.columns([3, 1.2], vertical_alignment="center")
        with col_s_tit:
            st.markdown(f"""
            <div style="font-size: 1.25rem; font-weight: 800; color: {text_main}; display: flex; align-items: center; gap: 10px;">
                <span>⏱️ {sim.get('titulo', 'Simulado')}</span>
                <span style="font-size: 0.75rem; background: {'rgba(124, 58, 237, 0.2)' if is_dark else 'rgba(124, 58, 237, 0.1)'};
                             color: {'#c4b5fd' if is_dark else '#7c3aed'};
                             border: 1px solid {'rgba(124, 58, 237, 0.4)' if is_dark else 'rgba(124, 58, 237, 0.25)'};
                             padding: 3px 10px; border-radius: 999px;">
                    {len(respostas)} de {total_q} respondidas
                </span>
            </div>
            """, unsafe_allow_html=True)

        with col_s_tim:
            st.markdown(f"""
            <div style="text-align: right; background: {card_bg}; border: 1.5px solid {cor_timer};
                        border-radius: 12px; padding: 6px 14px; box-shadow: 0 0 12px {cor_timer}35;">
                <div style="font-size: 0.7rem; color: {text_muted}; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Tempo Restante</div>
                <div style="font-size: 1.45rem; font-weight: 900; color: {cor_timer}; font-family: monospace; line-height: 1.1;">
                    {m_rest:02d}:{s_rest:02d}
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # ── Jumper de Questões (máximo 20 botões visíveis) ────────────────────
        if "questao_idx" not in st.session_state or st.session_state.questao_idx >= total_q:
            st.session_state.questao_idx = 0

        q_idx = st.session_state.questao_idx
        q_atual = questoes[q_idx]
        q_id = q_atual["id"]

        MAX_JUMPER = 20
        # Janela deslizante centrada na questão atual
        metade = MAX_JUMPER // 2
        inicio = max(0, min(q_idx - metade, total_q - MAX_JUMPER))
        fim = min(total_q, inicio + MAX_JUMPER)
        questoes_visiveis = list(enumerate(questoes))[inicio:fim]

        # Indicador de paginação se houver mais questões que o limite
        if total_q > MAX_JUMPER:
            st.markdown(
                f"<div style='font-size:0.78rem; color:{text_muted}; margin-bottom:4px;'>"
                f"Mostrando questões <b>{inicio+1}</b>–<b>{fim}</b> de <b>{total_q}</b> "
                f"(questão atual: <b>#{q_idx+1}</b>)</div>",
                unsafe_allow_html=True
            )

        cols_jumper = st.columns(len(questoes_visiveis))
        for col_idx, (i, q) in enumerate(questoes_visiveis):
            qid = q["id"]
            is_cur = (i == q_idx)
            is_rev = (qid in marcadas)
            is_ans = (qid in respostas)

            rotulo = f"🚩{i+1}" if is_rev else (f"✓{i+1}" if is_ans else f"{i+1}")

            with cols_jumper[col_idx]:
                if st.button(rotulo, key=f"jmp_{i}", use_container_width=True,
                             type="primary" if is_cur else "secondary"):
                    st.session_state.questao_idx = i
                    st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Enunciado da Questão Atual
        render_question(q_atual, mostrar_alternativas=False)

        # Seleção de Alternativa ou Resposta Discursiva (Sem spoiler durante o simulado)
        st.markdown("---")
        is_discursiva = e_questao_discursiva(q_atual)

        if not is_discursiva:
            st.markdown("#### 🔘 Selecione a Alternativa:")

            enunciado_raw = q_atual.get("enunciado", "")
            _, alternativas = extrair_enunciado_e_alternativas(enunciado_raw)
            alt_opcoes = alternativas if alternativas else {"A": "Alternativa A", "B": "Alternativa B", "C": "Alternativa C", "D": "Alternativa D", "E": "Alternativa E"}

            resp_atual = respostas.get(q_id, None)

            for letra, texto_alt in alt_opcoes.items():
                is_sel = (resp_atual == letra)
                icone = "🔘" if is_sel else "⚪"
                if st.button(
                    f"{icone}  ({letra})  {texto_alt}",
                    key=f"sim_alt_{q_id}_{letra}",
                    use_container_width=True,
                    type="primary" if is_sel else "secondary"
                ):
                    respostas[q_id] = letra
                    st.rerun()
        else:
            st.markdown("#### 📝 Questão Discursiva")
            st.caption("Esta questão é discursiva. Insira sua resposta final ou resumo do raciocínio:")
            resp_atual = respostas.get(q_id, "")
            nova_resp = st.text_area("Sua resolução / resposta:", value=resp_atual, key=f"sim_disc_{q_id}", height=120)
            if nova_resp != resp_atual:
                respostas[q_id] = nova_resp

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Barra Inferior: Anterior, Marcar Revisão, Próxima, Entregar
        c_p, c_r, c_n, c_f = st.columns([1.5, 2, 1.5, 2.5])

        with c_p:
            if st.button("⬅️ Anterior", use_container_width=True, disabled=(q_idx == 0)):
                st.session_state.questao_idx = q_idx - 1
                st.rerun()

        with c_r:
            ja_marcada = (q_id in marcadas)
            lbl_rev = "🏳️ Desmarcar Revisão" if ja_marcada else "🚩 Marcar para Revisar"
            if st.button(lbl_rev, use_container_width=True):
                if ja_marcada:
                    marcadas.remove(q_id)
                else:
                    marcadas.add(q_id)
                st.rerun()

        with c_n:
            if st.button("Próxima ➡️", use_container_width=True, disabled=(q_idx == total_q - 1)):
                st.session_state.questao_idx = q_idx + 1
                st.rerun()

        with c_f:
            if st.button("🏁 Finalizar Simulado", type="primary", use_container_width=True):
                _finalizar_simulado(sim, tempo_decorrido)
                st.rerun()

        return

    # ═════════════════════════════════════════════════════════════════════════
    # MODO 2: LISTA DE EXERCÍCIOS PERSONALIZADA
    # ═════════════════════════════════════════════════════════════════════════
    elif modo_sessao == "lista":
        lista = st.session_state.get("lista_config")
        if not lista or not lista.get("questoes"):
            st.session_state.modo_sessao = None
            st.rerun()
            return

        questoes = lista["questoes"]
        total_q = len(questoes)

        if "questao_idx" not in st.session_state or st.session_state.questao_idx >= total_q:
            st.session_state.questao_idx = 0

        q_idx = st.session_state.questao_idx
        q_atual_raw = questoes[q_idx]
        from src.database.db import buscar_questao_por_id
        q_db = buscar_questao_por_id(q_atual_raw.get("id"))
        q_atual = dict(q_db) if q_db else q_atual_raw

        # Header da Lista
        col_ltit, col_lbtn = st.columns([3, 1], vertical_alignment="center")
        with col_ltit:
            st.markdown(f"### 📝 {lista.get('titulo', 'Lista de Exercícios')}")
            st.caption(f"Questão {q_idx + 1} de {total_q} • Resolva com cronômetro, dicas socráticas e análise de IA.")
        with col_lbtn:
            if st.button("🏁 Concluir Lista", use_container_width=True):
                st.session_state.modo_sessao = None
                st.session_state.nav_page = "📚 Banco & Listas"
                st.rerun()

        # Grade de Questões da Lista
        MAX_JUMPER = 20
        metade = MAX_JUMPER // 2
        inicio = max(0, min(q_idx - metade, total_q - MAX_JUMPER))
        fim = min(total_q, inicio + MAX_JUMPER)
        questoes_visiveis = list(enumerate(questoes))[inicio:fim]

        if total_q > MAX_JUMPER:
            st.markdown(
                f"<div style='font-size:0.78rem; color:{text_muted}; margin-bottom:4px;'>"
                f"Mostrando navegação <b>{inicio+1}</b>—<b>{fim}</b> de <b>{total_q}</b> "
                f"</div>",
                unsafe_allow_html=True
            )

        cols_jumper = st.columns(len(questoes_visiveis))
        for col_idx, (i, q) in enumerate(questoes_visiveis):
            with cols_jumper[col_idx]:
                tipo_btn = "primary" if (i == q_idx) else "secondary"
                if st.button(f"#{i+1}", key=f"jmp_lista_{i}", use_container_width=True, type=tipo_btn):
                    st.session_state.questao_idx = i
                    st.rerun()

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        # Resolução Completa
        render_question(q_atual)
        render_resolution_form(q_atual)

        # Navegação Anterior / Próxima
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        col_prev, col_prog, col_next = st.columns([2, 3, 2])
        with col_prev:
            if st.button("⬅️ Anterior", use_container_width=True, disabled=(q_idx == 0), key="btn_prev_lista"):
                st.session_state.questao_idx = q_idx - 1
                st.rerun()
        with col_prog:
            st.markdown(
                f"<div style='text-align: center; color: {text_muted}; font-size: 0.9rem; padding-top: 8px;'>"
                f"Questão <b>{q_idx + 1}</b> de <b>{total_q}</b>"
                f"</div>",
                unsafe_allow_html=True
            )
        with col_next:
            if st.button("Próxima ➡️", use_container_width=True, disabled=(q_idx == total_q - 1), key="btn_next_lista"):
                st.session_state.questao_idx = q_idx + 1
                st.rerun()

        return

    # ═════════════════════════════════════════════════════════════════════════
    # MODO 3: STANDBY / NENHUMA LISTA OU SIMULADO ATIVO
    # ═════════════════════════════════════════════════════════════════════════
    else:
        st.markdown("## 🎯 Resolução & Simulados")
        st.caption("Resolva questões no seu ritmo ou faça simulados cronometrados com contagem regressiva.")

        st.markdown(f"""
        <div style="background: {card_bg}; border: 1.5px solid {card_border};
                    border-radius: 16px; padding: 28px 24px; text-align: center; margin: 14px 0;
                    box-shadow: 0 4px 16px rgba(0, 0, 0, {card_shadow});">
            <div style="font-size: 2.5rem; margin-bottom: 8px;">📚</div>
            <div style="font-size: 1.25rem; font-weight: 800; color: {text_main}; margin-bottom: 6px;">
                Nenhum simulado ou lista em andamento
            </div>
            <div style="font-size: 0.92rem; color: {text_muted}; max-width: 600px; margin: 0 auto 12px auto; line-height: 1.5;">
                O MathAI permite que você escolha no <b>Banco de Questões</b> exatamente quais matérias quer treinar,
                monte listas personalizadas ou inicie um <b>Simulado Cronometrado</b> com o tempo que desejar!
            </div>
        </div>
        """, unsafe_allow_html=True)

        usuario = st.session_state.get("usuario_logado") or {}
        focos_user = usuario.get("concursos_foco") or []
        foco_primario = focos_user[0].split("(")[0].strip() if focos_user else "ESA"

        st.markdown(f"##### ⚡ Início Rápido Recomendado{' (Personalizado para seu Foco)' if focos_user else ''}:")
        c_q1, c_q2, c_q3 = st.columns(3)

        with c_q1:
            st.markdown(f"""
            <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-top: 3px solid #f59e0b;
                        border-radius: 14px; padding: 18px 16px; margin-bottom: 10px;
                        box-shadow: 0 4px 14px rgba(0,0,0,{card_shadow}); text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 6px;">⏱️</div>
                <div style="font-weight: 800; font-size: 1.02rem; color: {text_main}; margin-bottom: 4px;">Simulado {foco_primario}</div>
                <div style="font-size: 0.8rem; color: {text_muted}; min-height: 36px; line-height: 1.3;">
                    Questões focadas no seu concurso alvo com limite de 60 minutos
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🚀 Iniciar Simulado {foco_primario} (60 min)", type="primary", use_container_width=True):
                questoes_all = [dict(q) for q in listar_questoes()]
                foco_questoes = [q for q in questoes_all if foco_primario.upper() in str(q.get("banca", "")).upper()]
                if not foco_questoes:
                    # Ordena priorizando os focos do aluno
                    focos_norm = [f.split("(")[0].strip().upper() for f in focos_user]
                    def _score_q(q):
                        b = str(q.get("banca") or "").upper()
                        for i, fn in enumerate(focos_norm):
                            if fn and fn in b: return i
                        return 999
                    foco_questoes = sorted(questoes_all, key=_score_q)[:12]

                st.session_state.modo_sessao = "simulado"
                st.session_state.simulado_config = {
                    "titulo": f"Simulado Focado — {foco_primario}",
                    "tempo_limite_min": 60,
                    "tempo_inicio": time.time(),
                    "questoes": foco_questoes,
                    "respostas": {},
                    "marcadas_revisao": set(),
                    "entregue": False,
                    "tempo_total_gasto": 0
                }
                st.session_state.questao_idx = 0
                st.rerun()

        with c_q2:
            st.markdown(f"""
            <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-top: 3px solid #7c3aed;
                        border-radius: 14px; padding: 18px 16px; margin-bottom: 10px;
                        box-shadow: 0 4px 14px rgba(0,0,0,{card_shadow}); text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 6px;">🔍</div>
                <div style="font-weight: 800; font-size: 1.02rem; color: {text_main}; margin-bottom: 4px;">Filtrar no Banco</div>
                <div style="font-size: 0.8rem; color: {text_muted}; min-height: 36px; line-height: 1.3;">
                    Filtre por matéria ou banca e crie um simulado personalizado
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("📚 Ir ao Banco de Questões", use_container_width=True):
                st.session_state.nav_page = "📚 Banco & Listas"
                st.rerun()

        with c_q3:
            st.markdown(f"""
            <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-top: 3px solid #6366f1;
                        border-radius: 14px; padding: 18px 16px; margin-bottom: 10px;
                        box-shadow: 0 4px 14px rgba(0,0,0,{card_shadow}); text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 6px;">📝</div>
                <div style="font-weight: 800; font-size: 1.02rem; color: {text_main}; margin-bottom: 4px;">Treino Livre</div>
                <div style="font-size: 0.8rem; color: {text_muted}; min-height: 36px; line-height: 1.3;">
                    Resolva questões com as do seu foco priorizadas no início
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🎯 Iniciar Treino Livre", use_container_width=True):
                questoes_all = [dict(q) for q in listar_questoes()]
                if focos_user:
                    focos_norm = [f.split("(")[0].strip().upper() for f in focos_user]
                    def _score_q2(q):
                        b = str(q.get("banca") or "").upper()
                        for i, fn in enumerate(focos_norm):
                            if fn and fn in b: return i
                        return 999
                    questoes_all = sorted(questoes_all, key=_score_q2)

                st.session_state.modo_sessao = "lista"
                st.session_state.lista_config = {
                    "titulo": f"Treino Livre — Foco {foco_primario}" if focos_user else "Treino Livre — Todas as Questões",
                    "questoes": questoes_all
                }
                st.session_state.questao_idx = 0
                st.rerun()


def _finalizar_simulado(sim: dict, tempo_gasto: int):
    """Calcula acertos, registra tentativas no banco de dados e marca o simulado como entregue."""
    sim["entregue"] = True
    sim["tempo_total_gasto"] = tempo_gasto

    questoes = sim.get("questoes", [])
    respostas = sim.get("respostas", {})
    aluno_id = st.session_state.get("aluno_id", 1)
    tempo_por_q = max(1, tempo_gasto // len(questoes)) if questoes else 10

    for q in questoes:
        qid = q["id"]
        gab = str(q.get("gabarito", "")).strip().upper()
        resp = str(respostas.get(qid, "")).strip().upper()
        acertou = (resp == gab)

        # Registra a tentativa para alimentar o perfil cognitivo do aluno
        try:
            registrar_tentativa(
                questao_id=qid,
                tempo_segundos=tempo_por_q,
                acertou=acertou,
                aluno_id=aluno_id,
                estrategia_usada="Simulado Cronometrado",
                tipo_erro="nenhum" if acertou else "simulado_incorreto",
                confianca_aluno=4 if acertou else 2,
                anotacoes=f"Simulado: {sim.get('titulo')} • Resposta marcada: ({resp})"
            )
        except Exception:
            pass
