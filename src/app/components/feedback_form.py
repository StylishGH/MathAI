"""
Componente do formulário de resolução, validação e feedback cognitivo.
Permite seleção direta nas alternativas em botões dedicados, campo de justificativa e diagnóstico metacognitivo.
"""

import json
import time
import base64
from pathlib import Path
import streamlit as st
from src.database.attempts import registrar_tentativa, salvar_diagnostico_ia, registrar_dica_socratica
from src.app.utils import extrair_enunciado_e_alternativas, e_questao_discursiva, formatar_transcricao_latex


def _renderizar_anexo(bytes_conteudo: bytes, mime_type: str = "image/png", nome_arquivo: str = ""):
    """Renderiza uma imagem ou um documento PDF na interface do Streamlit."""
    if not bytes_conteudo:
        return

    if mime_type == "application/pdf" or bytes_conteudo.startswith(b"%PDF"):
        b64_pdf = base64.b64encode(bytes_conteudo).decode("utf-8")
        nome_exibicao = nome_arquivo if nome_arquivo else "resolucao.pdf"
        tamanho_kb = len(bytes_conteudo) / 1024
        st.markdown(
            f"""
            <div style="background: rgba(99, 102, 241, 0.08); border: 1.5px solid #6366f1; border-radius: 10px; padding: 10px 14px; margin-bottom: 8px;">
                <div style="display: flex; align-items: center; gap: 10px;">
                    <span style="font-size: 1.6rem;">📄</span>
                    <div>
                        <div style="font-weight: 600; font-size: 0.92rem; color: #818cf8;">Documento PDF Anexado</div>
                        <div style="font-size: 0.78rem; color: #888;">{nome_exibicao} • {tamanho_kb:.1f} KB</div>
                    </div>
                </div>
            </div>
            <iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="320px" style="border: 1px solid rgba(128,128,128,0.2); border-radius: 8px;"></iframe>
            """,
            unsafe_allow_html=True
        )
    else:
        st.image(bytes_conteudo, caption="Sua resolução anexada", use_container_width=True)


def render_resolution_form(questao: dict, on_success_callback=None):
    """
    Renderiza as alternativas como botões clicáveis, cronômetro, campo de justificativa
    e o formulário pós-resolução com diagnóstico cognitivo.
    """
    q_id = questao["id"]
    gabarito_oficial = str(questao.get("gabarito", "")).strip().upper()

    # Inicializa estados de sessão específicos da questão
    if f"tempo_inicio_{q_id}" not in st.session_state:
        st.session_state[f"tempo_inicio_{q_id}"] = time.time()
    if f"resolvido_{q_id}" not in st.session_state:
        st.session_state[f"resolvido_{q_id}"] = False
    if f"acertou_{q_id}" not in st.session_state:
        st.session_state[f"acertou_{q_id}"] = False
    if f"resposta_escolhida_{q_id}" not in st.session_state:
        st.session_state[f"resposta_escolhida_{q_id}"] = "A"
    if f"tempo_total_{q_id}" not in st.session_state:
        st.session_state[f"tempo_total_{q_id}"] = 0
    if f"justificativa_{q_id}" not in st.session_state:
        st.session_state[f"justificativa_{q_id}"] = ""

    # Extrai alternativas do enunciado
    enunciado_raw = questao.get("enunciado", "")
    _, alternativas = extrair_enunciado_e_alternativas(enunciado_raw)
    is_discursiva = e_questao_discursiva(questao)

    st.markdown("---")

    # =========================================================================
    # ESTADO 1: AINDA NÃO RESPONDEU (Alternativas Clicáveis + Campo Justificativa)
    # =========================================================================
    if not st.session_state[f"resolvido_{q_id}"]:
        if not is_discursiva:
            st.markdown("#### 🔘 Selecione a Alternativa:")
            st.caption("Clique diretamente na alternativa que você considera correta:")

            if alternativas:
                for letra, texto_alt in alternativas.items():
                    is_selected = (st.session_state[f"resposta_escolhida_{q_id}"] == letra)
                    icone = "🔘" if is_selected else "⚪"
                    btn_texto = f"{icone}  ({letra})  {texto_alt}"
                    if st.button(
                        btn_texto,
                        key=f"btn_alt_{q_id}_{letra}",
                        use_container_width=True,
                        type="primary" if is_selected else "secondary"
                    ):
                        st.session_state[f"resposta_escolhida_{q_id}"] = letra
                        st.rerun()
            else:
                # Fallback caso a questão não possua alternativas no formato (A)...(E)
                opcoes_fallback = ["A", "B", "C", "D", "E"]
                cols = st.columns(len(opcoes_fallback))
                for i, opt in enumerate(opcoes_fallback):
                    is_selected = (st.session_state[f"resposta_escolhida_{q_id}"] == opt)
                    with cols[i]:
                        if st.button(
                            f"({opt})",
                            key=f"btn_fallback_{q_id}_{opt}",
                            use_container_width=True,
                            type="primary" if is_selected else "secondary"
                        ):
                            st.session_state[f"resposta_escolhida_{q_id}"] = opt
                            st.rerun()
        else:
            st.markdown(
                """
                <div style="display: flex; align-items: center; gap: 10px; margin: 6px 0 16px 0;
                            padding: 10px 16px; border-radius: 12px;
                            background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.3);
                            color: #10b981; font-weight: 600; font-size: 0.92rem;">
                    <span style="font-size: 1.25rem;">📝</span>
                    <span><b>Questão Discursiva:</b> Esta questão não possui alternativas. Desenvolva seus passos no campo de justificativa ou anexe uma foto/PDF do seu rascunho abaixo.</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        # =====================================================================
        # Dicas Socráticas Progressivas (Níveis 1 a 5)
        # =====================================================================
        with st.expander("💡 Precisa de Ajuda? Dicas Socráticas Progressivas (Nível 1 a 5)", expanded=False):
            st.caption("O método socrático não entrega a resposta: ele estimula o seu raciocínio matemático em etapas.")
            
            from src.ai.evaluator import obter_dica_socratica, analisar_resolucao
            
            col_sl, col_bt = st.columns([3, 1])
            with col_sl:
                nivel_dica = st.slider(
                    "Selecione o nível de profundidade da dica:",
                    min_value=1,
                    max_value=5,
                    value=st.session_state.get(f"nivel_dica_{q_id}", 1),
                    format="%d",
                    help="1: Dados do enunciado | 2: Teorema | 3: Primeira equação | 4: Contas intermediárias | 5: Resolução completa",
                    key=f"slider_dica_{q_id}"
                )
                legenda_dica = {
                    1: "Nível 1: Reflexão sobre dados e grandezas",
                    2: "Nível 2: Teorema ou propriedade aplicável",
                    3: "Nível 3: Pista da primeira equação ou traçado",
                    4: "Nível 4: Passos intermediários do cálculo",
                    5: "Nível 5: Resolução passo a passo completa"
                }.get(nivel_dica, "")
                st.markdown(f"<span style='font-size: 0.85rem; color: #a78bfa;'><b>{legenda_dica}</b></span>", unsafe_allow_html=True)
            
            with col_bt:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                if st.button("💡 Revelar Dica", use_container_width=True, key=f"btn_dica_{q_id}"):
                    with st.spinner("Consultando tutor pedagógico..."):
                        dica_texto = obter_dica_socratica(questao, nivel_dica)
                        st.session_state[f"dica_conteudo_{q_id}"] = dica_texto
                        st.session_state[f"dica_nivel_mostrado_{q_id}"] = nivel_dica
                        # ⭐ Rastreia o pedido de dica no dataset
                        aluno_id = st.session_state.get("aluno_id", 1)
                        registrar_dica_socratica(
                            questao_id=q_id,
                            nivel_dica=nivel_dica,
                            texto_dica=dica_texto,
                            aluno_id=aluno_id
                        )
            
            if f"dica_conteudo_{q_id}" in st.session_state:
                st.markdown(
                    f"""
                    <div style="background: rgba(139, 92, 246, 0.1); border-left: 3px solid #8b5cf6; border-radius: 8px; padding: 12px 16px; margin-top: 12px;">
                        <div style="font-weight: 700; color: #a78bfa; font-size: 0.9rem; margin-bottom: 6px;">
                            💡 Dica Socrática (Nível {st.session_state.get(f'dica_nivel_mostrado_{q_id}', 1)} de 5):
                        </div>
                        <div style="font-size: 0.95rem; line-height: 1.6;">
                    """,
                    unsafe_allow_html=True
                )
                st.markdown(st.session_state[f"dica_conteudo_{q_id}"])
                st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

        # Detecta se a questão é discursiva (justificativa obrigatória)
        is_discursiva = e_questao_discursiva(questao)

        # Campos lado a lado: Justificativa em Texto & Upload da Resolução Manuscrita
        col_just, col_img = st.columns([1, 1], gap="medium", vertical_alignment="top")

        with col_just:
            if is_discursiva:
                st.markdown("##### 📝 Justificativa do seu Raciocínio 🔴 Obrigatória")
                st.caption("⚠️ Questão discursiva: explique sua resolução e o resultado obtido:")
            else:
                st.markdown("##### 📝 Justificativa do seu Raciocínio (Opcional)")
                st.caption("Explique como você chegou a essa resposta ou os passos:")

            justificativa_input = st.text_area(
                "Justificativa:",
                value=st.session_state.get(f"justificativa_{q_id}", ""),
                placeholder="Ex: Usando o Teorema de Pitágoras, a² + b² = c²...\nResultado final: x = 4",
                key=f"txt_justificativa_input_{q_id}",
                label_visibility="collapsed",
                height=150
            )
            st.session_state[f"justificativa_{q_id}"] = justificativa_input

        with col_img:
            if is_discursiva:
                st.markdown("##### 📷 Resolução Manuscrita / Tablet / PDF 🔴 Obrigatória")
                st.caption("⚠️ Questão discursiva: envie foto, print ou PDF da sua resolução:")
            else:
                st.markdown("##### 📷 Resolução Manuscrita / Tablet / PDF (Opcional)")
                st.caption("Envie uma foto do caderno, print do tablet ou documento PDF:")

            uploaded_file = st.file_uploader(
                "Upload da resolução (Imagem ou PDF):",
                type=["png", "jpg", "jpeg", "webp", "pdf"],
                key=f"uploader_resolucao_{q_id}",
                label_visibility="collapsed"
            )
            if uploaded_file is not None:
                conteudo = uploaded_file.getvalue()
                nome = uploaded_file.name
                is_pdf = nome.lower().endswith(".pdf") or conteudo.startswith(b"%PDF")
                mime = "application/pdf" if is_pdf else "image/png"
                st.session_state[f"imagem_resolucao_{q_id}"] = conteudo
                st.session_state[f"mime_resolucao_{q_id}"] = mime
                st.session_state[f"nome_resolucao_{q_id}"] = nome
                _renderizar_anexo(conteudo, mime, nome)
            elif f"imagem_resolucao_{q_id}" in st.session_state and st.session_state[f"imagem_resolucao_{q_id}"]:
                _renderizar_anexo(
                    st.session_state[f"imagem_resolucao_{q_id}"],
                    st.session_state.get(f"mime_resolucao_{q_id}", "image/png"),
                    st.session_state.get(f"nome_resolucao_{q_id}", "")
                )

        # Botão de Análise de Rascunho com IA (Se houver texto ou imagem/PDF)
        tem_conteudo = bool(st.session_state.get(f"justificativa_{q_id}", "").strip()) or bool(st.session_state.get(f"imagem_resolucao_{q_id}", None))
        if tem_conteudo:
            col_ai_btn, _ = st.columns([2, 3])
            with col_ai_btn:
                if st.button("🧠 Analisar Rascunho com IA", use_container_width=True, key=f"btn_ai_analisar_{q_id}"):
                    with st.spinner("Avaliador Cognitivo analisando seu raciocínio..."):
                        from src.ai.evaluator import analisar_resolucao
                        img_bytes = st.session_state.get(f"imagem_resolucao_{q_id}", None)
                        mime_arq = st.session_state.get(f"mime_resolucao_{q_id}", "image/png")
                        txt_just = st.session_state.get(f"justificativa_{q_id}", "")
                        diag = analisar_resolucao(
                            questao,
                            imagem_bytes=img_bytes,
                            mime_type=mime_arq,
                            justificativa_texto=txt_just
                        )
                        st.session_state[f"analise_ia_{q_id}"] = diag
                        # ⭐ Auto-salva o diagnóstico no banco imediatamente
                        aluno_id = st.session_state.get("aluno_id", 1)
                        salvar_diagnostico_ia(
                            questao_id=q_id,
                            diagnostico_dict=diag,
                            aluno_id=aluno_id,
                            imagem_path=st.session_state.get(f"nome_resolucao_{q_id}"),
                            justificativa_texto=txt_just
                        )
                        st.rerun()

        # Exibição do Card Diagnóstico da IA se já tiver sido gerado
        if f"analise_ia_{q_id}" in st.session_state:
            _renderizar_card_ia(st.session_state[f"analise_ia_{q_id}"])

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

        col_btn, col_info = st.columns([2, 3])
        with col_btn:
            # Verifica obrigatoriedade para questões discursivas
            tem_texto = bool(st.session_state.get(f"justificativa_{q_id}", "").strip())
            tem_imagem = bool(st.session_state.get(f"imagem_resolucao_{q_id}", None))

            if is_discursiva and not (tem_texto or tem_imagem):
                st.warning("🔴 **Questão discursiva:** preencha a justificativa OU envie uma imagem antes de confirmar.")
                st.button("🎯 Confirmar Resposta", use_container_width=True, type="primary",
                          key=f"btn_confirmar_{q_id}", disabled=True)
            else:
                btn_label = "📋 Enviar Resolução" if is_discursiva else "🎯 Confirmar Resposta"
                if st.button(btn_label, use_container_width=True, type="primary",
                             key=f"btn_confirmar_{q_id}"):
                    tempo_decorrido = int(time.time() - st.session_state[f"tempo_inicio_{q_id}"])
                    st.session_state[f"tempo_total_{q_id}"] = max(tempo_decorrido, 1)
                    st.session_state[f"resolvido_{q_id}"] = True
                    if is_discursiva:
                        st.session_state[f"acertou_{q_id}"] = True
                    else:
                        resposta_atual = st.session_state[f"resposta_escolhida_{q_id}"]
                        st.session_state[f"acertou_{q_id}"] = (resposta_atual == gabarito_oficial)
                    st.rerun()

        with col_info:
            if is_discursiva:
                st.markdown(
                    f"<div style='padding-top: 8px; color: #10b981; font-size: 0.92rem; font-weight: 600;'>"
                    f"📝 <b>Questão Discursiva:</b> Justificativa ou anexo obrigatórios."
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                escolhida = st.session_state[f"resposta_escolhida_{q_id}"]
                st.markdown(
                    f"<div style='padding-top: 8px; color: #888; font-size: 0.95rem;'>"
                    f"Alternativa selecionada: <b style='color: #6366f1; font-size: 1.1rem;'>({escolhida})</b>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # =========================================================================
    # ESTADO 2: JÁ RESPONDEU (Gabarito, Destaque Visual e Diagnóstico)
    # =========================================================================
    else:
        acertou = st.session_state[f"acertou_{q_id}"]
        resposta_usuario = st.session_state[f"resposta_escolhida_{q_id}"]
        tempo_segundos = st.session_state[f"tempo_total_{q_id}"]
        minutos = tempo_segundos // 60
        segs = tempo_segundos % 60
        tempo_formatado = f"{minutos}m {segs:02d}s" if minutos > 0 else f"{segs}s"
        is_dark = (st.session_state.get("tema", "dark") == "dark")

        if is_discursiva:
            st.success(f"📋 **Resolução enviada com sucesso!** • Tempo gasto: **{tempo_formatado}**")
            gabarito_exibicao = questao.get("gabarito") or "Ver estratégias esperadas abaixo"
            st.markdown(
                f"""
                <div style="background: rgba(16, 185, 129, 0.1); border: 1.5px solid #10b981; border-radius: 12px; padding: 14px 18px; margin: 12px 0;">
                    <div style="color: #10b981; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; margin-bottom: 4px;">
                        🎯 Gabarito Oficial / Resposta Esperada
                    </div>
                    <div style="font-size: 1.1rem; font-weight: 700; color: {'#ffffff' if is_dark else '#0f172a'};">
                        {gabarito_exibicao}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        else:
            if acertou:
                st.success(f"🎉 **Parabéns, você acertou!** (Gabarito: **{gabarito_oficial}**) • Tempo: **{tempo_formatado}**")
            else:
                st.error(f"❌ **Resposta incorreta.** Você marcou **({resposta_usuario})**, mas o gabarito oficial é **({gabarito_oficial})**. • Tempo: **{tempo_formatado}**")

        # Exibição visual das alternativas (apenas para questões objetivas)
        if not is_discursiva and alternativas:
            st.markdown("##### Alternativas:")
            for letra, texto_alt in alternativas.items():
                if letra == gabarito_oficial:
                    # Alternativa Correta (Gabarito)
                    st.markdown(
                        f"""
                        <div style="background: rgba(16, 185, 129, 0.15); border: 2px solid #10b981; border-radius: 10px; padding: 10px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div><b>({letra})</b> {texto_alt}</div>
                            <span style="color: #10b981; font-weight: 700; font-size: 0.85rem;">✅ Gabarito Oficial</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                elif letra == resposta_usuario and not acertou:
                    # Alternativa Incorreta Escolhida pelo Aluno
                    st.markdown(
                        f"""
                        <div style="background: rgba(239, 68, 68, 0.15); border: 2px solid #ef4444; border-radius: 10px; padding: 10px 16px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div><b>({letra})</b> {texto_alt}</div>
                            <span style="color: #ef4444; font-weight: 700; font-size: 0.85rem;">❌ Sua Resposta</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                else:
                    # Outras Alternativas
                    st.markdown(
                        f"""
                        <div style="background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(128, 128, 128, 0.15); border-radius: 10px; padding: 10px 16px; margin-bottom: 8px; opacity: 0.6;">
                            <b>({letra})</b> {texto_alt}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # Exibe a justificativa e a imagem enviada
        justificativa_salva = st.session_state.get(f"justificativa_{q_id}", "")
        imagem_salva = st.session_state.get(f"imagem_resolucao_{q_id}", None)

        if justificativa_salva or imagem_salva:
            col_rev_just, col_rev_img = st.columns([1, 1] if (justificativa_salva and imagem_salva) else [1, 0.01], gap="medium")
            with col_rev_just:
                if justificativa_salva:
                    import html
                    just_safe = html.escape(justificativa_salva).replace("*", "&#42;")
                    st.markdown(
                        f"""
                        <div style="background: rgba(99, 102, 241, 0.08); border-left: 3px solid #6366f1; border-radius: 6px; padding: 10px 14px; margin: 12px 0;">
                            <div style="font-size: 0.8rem; font-weight: 600; color: #818cf8; margin-bottom: 4px;">SUA JUSTIFICATIVA REGISTRADA:</div>
                            <div style="font-style: italic; font-size: 0.95rem; white-space: pre-wrap;">"{just_safe}"</div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            if imagem_salva:
                with col_rev_img:
                    mime_salvo = st.session_state.get(f"mime_resolucao_{q_id}", "image/png")
                    nome_salvo = st.session_state.get(f"nome_resolucao_{q_id}", "")
                    _renderizar_anexo(imagem_salva, mime_salvo, nome_salvo)

        # Botão para obter ou reexecutar análise de IA pós-resolução
        if justificativa_salva or imagem_salva:
            col_ai2, _ = st.columns([2, 3])
            with col_ai2:
                btn_texto = "🔄 Reavaliar com IA" if f"analise_ia_{q_id}" in st.session_state else "🧠 Analisar Resolução com IA"
                if st.button(btn_texto, use_container_width=True, key=f"btn_ai_analisar_pos_{q_id}"):
                    with st.spinner("Avaliador Cognitivo analisando seu raciocínio..."):
                        from src.ai.evaluator import analisar_resolucao
                        mime_salvo = st.session_state.get(f"mime_resolucao_{q_id}", "image/png")
                        diag = analisar_resolucao(
                            questao,
                            imagem_bytes=imagem_salva,
                            mime_type=mime_salvo,
                            justificativa_texto=justificativa_salva
                        )
                        st.session_state[f"analise_ia_{q_id}"] = diag
                        st.rerun()

        # Exibição do Card Diagnóstico da IA
        if f"analise_ia_{q_id}" in st.session_state:
            _renderizar_card_ia(st.session_state[f"analise_ia_{q_id}"])

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
        st.markdown("### 🧠 Diagnóstico Cognitivo & Metacognição")
        st.caption("A IA do MathAI utiliza esses dados para mapear o seu estilo de raciocínio e padrões de erro.")

        # Carregar estratégias esperadas do banco
        estrategias_raw = questao.get("estrategias_esperadas", "[]")
        try:
            estrategias_opcoes = json.loads(estrategias_raw) if isinstance(estrategias_raw, str) else (estrategias_raw or [])
        except Exception:
            estrategias_opcoes = []
        estrategias_opcoes.append("Outra estratégia...")

        col_est, col_conf = st.columns([3, 2])
        with col_est:
            estrategia_selecionada = st.selectbox(
                "Qual estratégia principal você utilizou?",
                options=estrategias_opcoes,
                key=f"sel_est_{q_id}"
            )
            if estrategia_selecionada == "Outra estratégia...":
                estrategia_custom = st.text_input("Especifique a estratégia usada:", key=f"txt_est_{q_id}")
                estrategia_final = estrategia_custom if estrategia_custom else "Outra"
            else:
                estrategia_final = estrategia_selecionada or "Não informada"

        with col_conf:
            confianca = st.select_slider(
                "Nível de Confiança / Certeza:",
                options=[1, 2, 3, 4, 5],
                value=3,
                format_func=lambda x: {
                    1: "1 - Chute total",
                    2: "2 - Pouca certeza",
                    3: "3 - Razoável",
                    4: "4 - Quase certeza",
                    5: "5 - Certeza absoluta"
                }.get(x, str(x)),
                key=f"slider_conf_{q_id}"
            )

        # Se errou, pergunta a causa do erro
        tipo_erro_final = "nenhum"
        if not acertou:
            tipo_erro_opcoes = {
                "conta_sinal": "➕ Erro de Conta ou Sinal",
                "manipulacao_algebrica": "📐 Manipulação Algébrica / Fatoração",
                "conceitual": "🧠 Erro Conceitual / Teorema Incorreto",
                "interpretacao": "📖 Erro de Interpretação do Enunciado",
                "outro": "❓ Outro motivo"
            }
            tipo_erro_escolhido = st.selectbox(
                "Qual foi a causa principal do erro?",
                options=list(tipo_erro_opcoes.keys()),
                format_func=lambda k: tipo_erro_opcoes[k],
                key=f"sel_erro_{q_id}"
            )
            tipo_erro_final = tipo_erro_escolhido

        anotacoes_reflexao = st.text_area(
            "Reflexão adicional / Anotações pós-resolução (opcional):",
            placeholder="Ex: 'Na próxima vez vou tentar por semelhança antes de montar a equação...'",
            key=f"txt_anot_{q_id}"
        )

        col_save, col_reset = st.columns([3, 1])
        with col_save:
            if st.button("💾 Salvar Tentativa e Atualizar Perfil", type="primary", use_container_width=True, key=f"btn_save_{q_id}"):
                # Junta justificativa inicial com anotações de reflexão
                texto_anotacoes_final = ""
                if justificativa_salva:
                    texto_anotacoes_final += f"Justificativa: {justificativa_salva}\n"
                if anotacoes_reflexao.strip():
                    texto_anotacoes_final += f"Reflexão: {anotacoes_reflexao.strip()}"

                # Salva anexo da resolução (imagem ou PDF) em disco se houver
                caminho_imagem_salva = None
                if imagem_salva:
                    pasta_resolucoes = Path("data/uploads/resolucoes")
                    pasta_resolucoes.mkdir(parents=True, exist_ok=True)
                    is_pdf_salvo = (st.session_state.get(f"mime_resolucao_{q_id}") == "application/pdf")
                    extensao = "pdf" if is_pdf_salvo else "png"
                    arquivo_nome = f"tentativa_q{q_id}_{int(time.time())}.{extensao}"
                    arquivo_path = pasta_resolucoes / arquivo_nome
                    arquivo_path.write_bytes(imagem_salva)
                    caminho_imagem_salva = str(arquivo_path).replace("\\", "/")

                tentativa_id = registrar_tentativa(
                    questao_id=q_id,
                    tempo_segundos=tempo_segundos,
                    acertou=acertou,
                    aluno_id=st.session_state.get("aluno_id", 1),
                    estrategia_usada=estrategia_final,
                    tipo_erro=tipo_erro_final,
                    confianca_aluno=confianca,
                    anotacoes=texto_anotacoes_final.strip() or None,
                    imagem_resolucao_path=caminho_imagem_salva
                )

                # Se houver análise de IA gerada, salva também na tabela de diagnósticos
                if f"analise_ia_{q_id}" in st.session_state:
                    salvar_diagnostico_ia(
                        questao_id=q_id,
                        diagnostico_dict=st.session_state[f"analise_ia_{q_id}"],
                        aluno_id=st.session_state.get("aluno_id", 1),
                        tentativa_id=tentativa_id,
                        imagem_path=caminho_imagem_salva,
                        justificativa_texto=justificativa_salva
                    )

                st.success(f"✅ Tentativa #{tentativa_id} registrada no banco! Perfil e dataset atualizados.")
                if on_success_callback:
                    on_success_callback()

        with col_reset:
            if st.button("🔄 Mudar Resposta / Tentar Novamente", use_container_width=True, key=f"btn_reset_{q_id}"):
                st.session_state[f"resolvido_{q_id}"] = False
                st.session_state[f"tempo_inicio_{q_id}"] = time.time()
                st.rerun()


def _renderizar_card_ia(diag: dict):
    """Renderiza um card visual elegante com o diagnóstico cognitivo gerado pela IA."""
    status = diag.get("status_resolucao", "incompleto")
    status_map = {
        "correto": ("✅ Raciocínio Correto", "#10b981", "rgba(16, 185, 129, 0.1)"),
        "erro_conta_sinal": ("⚠️ Erro de Conta / Sinal", "#f59e0b", "rgba(245, 158, 11, 0.1)"),
        "erro_algebraico": ("📐 Erro Algébrico / Fatoração", "#f59e0b", "rgba(245, 158, 11, 0.1)"),
        "erro_conceitual": ("🧠 Erro Conceitual / Teorema", "#ef4444", "rgba(239, 68, 68, 0.1)"),
        "erro_interpretacao": ("📖 Erro de Interpretação", "#ef4444", "rgba(239, 68, 68, 0.1)"),
        "incompleto": ("⏳ Resolução Parcial / Incompleta", "#8b5cf6", "rgba(139, 92, 246, 0.1)")
    }
    label_status, cor_status, bg_status = status_map.get(
        status, ("⏳ Resolução Parcial / Incompleta", "#8b5cf6", "rgba(139, 92, 246, 0.1)")
    )
    raw_modelo = str(diag.get("modelo_utilizado", ""))
    modelo_badge = raw_modelo.replace("Gemini Pro", "MathAI Pro").replace("Gemini 3.7 Flash", "MathAI Flash").replace("Gemini", "MathAI")
    badge_html = f'<span style="background: rgba(124, 58, 237, 0.12); border: 1px solid rgba(124, 58, 237, 0.3); padding: 3px 10px; border-radius: 9999px; font-size: 0.76rem; color: #a78bfa; margin-right: 6px; font-weight: 600;">{modelo_badge}</span>' if modelo_badge else ""


    with st.container(border=True):
        st.markdown(
            f"""
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="font-size: 1.2rem;">🧠</span>
                    <span style="font-weight: 700; font-size: 1.05rem;">Avaliador Cognitivo MathAI</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    {badge_html}
                    <span style="background: {cor_status}; color: white; padding: 3px 10px; border-radius: 9999px; font-weight: 600; font-size: 0.8rem;">
                        {label_status}
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # 1. Estratégia Identificada
        estrategia = diag.get("estrategia_identificada")
        if estrategia:
            st.markdown(f"**🎯 Técnica / Estratégia Identificada:** `{estrategia}`")

        # 2. Transcrição em LaTeX
        transcricao = diag.get("transcricao_latex")
        if transcricao:
            st.markdown("**📝 Leitura da sua Resolução (OCR / LaTeX):**")
            transcricao_formatada = formatar_transcricao_latex(transcricao)
            with st.container(border=True):
                st.markdown(transcricao_formatada)

        # 3. Passos Identificados
        passos = diag.get("passos", [])
        if passos and isinstance(passos, list):
            st.markdown("**🔢 Passos do Raciocínio:**")
            for p in passos:
                st.markdown(f"- {p}")

        # 4. Parecer Pedagógico
        diagnostico_texto = diag.get("diagnostico")
        if diagnostico_texto:
            diag_limpo = str(diagnostico_texto).replace("Gemini Pro", "MathAI Pro").replace("Gemini 3.7 Flash", "MathAI Flash").replace("Gemini", "MathAI")
            st.markdown(f"**💬 Parecer Pedagógico:** {diag_limpo}")

        # 5. Linha do Erro (se houver)
        linha_erro = diag.get("linha_do_erro")
        if linha_erro:
            st.warning(f"⚠️ **Ponto de Atenção:** {linha_erro}")

        # 6. Dica Socrática de Próximo Passo
        dica = diag.get("dica_proximo_passo")
        if dica:
            st.info(f"💡 **Provocação para Evolução:** {dica}")

