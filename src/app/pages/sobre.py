"""
Página "Sobre Nós" / Quem Somos do MathAI.
Apresenta a visão, metodologia pedagógica, arquitetura e diferenciais da plataforma.
"""

import streamlit as st


def show():
    is_dark = (st.session_state.get("tema", "dark") == "dark")
    card_bg = "rgba(19, 17, 28, 0.88)" if is_dark else "#ffffff"
    card_border = "rgba(124, 58, 237, 0.35)" if is_dark else "#e2e8f0"
    text_main = "#f8fafc" if is_dark else "#0f172a"
    text_muted = "#94a3b8" if is_dark else "#64748b"
    card_shadow = "0.4" if is_dark else "0.06"
    gold_color = "#fbbf24" if is_dark else "#b45309"
    gold_border = "#f59e0b"

    # ── 1. Hero Banner ────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-top: 4px solid #7c3aed;
                border-radius: 20px; padding: 36px 30px; margin-bottom: 24px; text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, {card_shadow});">
        <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(245, 158, 11, 0.12);
                    border: 1px solid rgba(245, 158, 11, 0.4); padding: 4px 14px; border-radius: 999px;
                    font-size: 0.8rem; font-weight: 700; color: {gold_color}; margin-bottom: 14px;">
            ✨ PLATAFORMA COGNITIVA DE MATEMÁTICA • VERSÃO 1.0
        </div>
        <h1 style="font-size: 2.2rem; font-weight: 800; color: {text_main}; margin-bottom: 12px; letter-spacing: -0.02em;">
            A IA que aprende como você pensa Matemática
        </h1>
        <p style="font-size: 1.05rem; color: {text_muted}; max-width: 760px; margin: 0 auto; line-height: 1.6;">
            Diferente dos bancos de questões convencionais que apenas conferem respostas, o <b>MathAI</b> investiga o seu 
            <b>processo de raciocínio</b>, identifica <b>vícios de cálculo</b> e mapeia <b>estratégias cognitivas</b> para acelerar sua evolução.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # ── 2. O Manifesto / Filosofia Pedagógica ─────────────────────────────────
    st.markdown("### 💡 Por que o MathAI é Diferente?")
    st.caption("A maioria dos estudantes de matemática não falha por falta de fórmulas, mas pela ausência de diagnóstico metacognitivo.")

    c_pil1, c_pil2, c_pil3, c_pil4 = st.columns(4)

    with c_pil1:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 22px 18px;
                    height: 100%; box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="font-size: 2rem; margin-bottom: 10px;">🧠</div>
            <div style="font-weight: 800; font-size: 1.05rem; color: {text_main}; margin-bottom: 8px;">
                Diagnóstico Cognitivo
            </div>
            <div style="font-size: 0.86rem; color: {text_muted}; line-height: 1.5;">
                Mapeamos se seu erro foi por <b>conta de aritmética</b>, <b>interpretação do enunciado</b>, <b>falha conceitual</b> ou <b>manipulação algébrica</b>.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_pil2:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 22px 18px;
                    height: 100%; box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="font-size: 2rem; margin-bottom: 10px;">📷</div>
            <div style="font-weight: 800; font-size: 1.05rem; color: {text_main}; margin-bottom: 8px;">
                Caderno & Tablet
            </div>
            <div style="font-size: 0.86rem; color: {text_muted}; line-height: 1.5;">
                Envie foto do seu rascunho manuscrito ou documento PDF. Nossa IA multimodal analisa seus passos intermediários linha por linha.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_pil3:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 22px 18px;
                    height: 100%; box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="font-size: 2rem; margin-bottom: 10px;">⏱️</div>
            <div style="font-weight: 800; font-size: 1.05rem; color: {text_main}; margin-bottom: 8px;">
                Simulados Reais
            </div>
            <div style="font-size: 0.86rem; color: {text_muted}; line-height: 1.5;">
                Treine com cronômetro regressivo com tempo oficial de prova (ESA, ENEM, vestibulares) e receba relatórios analíticos de rendimento.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_pil4:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 22px 18px;
                    height: 100%; box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="font-size: 2rem; margin-bottom: 10px;">📈</div>
            <div style="font-weight: 800; font-size: 1.05rem; color: {text_main}; margin-bottom: 8px;">
                Repetição Espaçada
            </div>
            <div style="font-size: 0.86rem; color: {text_muted}; line-height: 1.5;">
                Algoritmo SuperMemo-2 (SM-2) integrado que agenda revisões nos intervalos ideais para fixar na memória de longo prazo.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ── 3. Metodologia: Como a IA Mapeia Você ──────────────────────────────────
    st.markdown("### 🔬 Como a Mágica Acontece?")
    st.caption("O ciclo de resolução e aprendizagem em 4 etapas.")

    col_et1, col_et2 = st.columns(2)

    with col_et1:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 16px; padding: 22px 24px;
                    margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: #7c3aed; color: white;
                            display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem;">1</div>
                <div style="font-weight: 800; font-size: 1.1rem; color: {text_main};">Resolução Focada & Cronometrada</div>
            </div>
            <p style="font-size: 0.9rem; color: {text_muted}; margin: 0; line-height: 1.6;">
                Você resolve a questão visualizando diagramas vetoriais nítidos em SVG e fórmulas em KaTeX (LaTeX). O tempo exato gasto em cada item é monitorado de forma invisível.
            </p>
        </div>

        <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 16px; padding: 22px 24px;
                    box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: #7c3aed; color: white;
                            display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem;">2</div>
                <div style="font-weight: 800; font-size: 1.1rem; color: {text_main};">Metacognição Ativa</div>
            </div>
            <p style="font-size: 0.9rem; color: {text_muted}; margin: 0; line-height: 1.6;">
                Antes ou depois de marcar sua alternativa, você indica qual teorema ou estratégia tentou utilizar (ex: <i>Teorema de Menelaus</i>, <i>Girard</i>, <i>Áreas</i>) e justifica seu raciocínio.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_et2:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 16px; padding: 22px 24px;
                    margin-bottom: 16px; box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: {gold_border}; color: #0a0a0f;
                            display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem;">3</div>
                <div style="font-weight: 800; font-size: 1.1rem; color: {text_main};">Avaliação Multimodal com IA</div>
            </div>
            <p style="font-size: 0.9rem; color: {text_muted}; margin: 0; line-height: 1.6;">
                Modelos de visão e raciocínio avançados (Google Gemini) comparam seu rascunho com as resoluções esperadas, indicando onde houve o desvio exato no seu desenvolvimento.
            </p>
        </div>

        <div style="background: {card_bg}; border: 1.5px solid {card_border}; border-radius: 16px; padding: 22px 24px;
                    box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 10px;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background: {gold_border}; color: #0a0a0f;
                            display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 0.9rem;">4</div>
                <div style="font-weight: 800; font-size: 1.1rem; color: {text_main};">Construção do Perfil Cognitivo</div>
            </div>
            <p style="font-size: 0.9rem; color: {text_muted}; margin: 0; line-height: 1.6;">
                O radar de habilidades e o gráfico de domínio mapeiam seus pontos fortes e fracos em tempo real, direcionando os próximos treinos para onde você mais precisa.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 24px;'></div>", unsafe_allow_html=True)

    # ── 4. Para Quem É a Plataforma ──────────────────────────────────────────
    st.markdown("### 🎯 Feito Sob Medida Para:")

    c_pub1, c_pub2, c_pub3 = st.columns(3)

    with c_pub1:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 20px;
                    box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">🎖️</div>
            <div style="font-weight: 700; color: {text_main}; margin-bottom: 6px;">Concursos Militares</div>
            <div style="font-size: 0.85rem; color: {text_muted}; line-height: 1.5;">
                ESA, EsPCEx, Colégio Naval, EPCAr, AFA, EFOMM, IME e ITA. Foco em velocidade, precisão de conta e repertório geométrico.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_pub2:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 20px;
                    box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">📚</div>
            <div style="font-weight: 700; color: {text_main}; margin-bottom: 6px;">ENEM & Vestibulares Tradicionais</div>
            <div style="font-size: 0.85rem; color: {text_muted}; line-height: 1.5;">
                ENEM, Fuvest, Unicamp, UERJ e Unesp. Ênfase em interpretação de modelos matemáticos, probabilidade e funções.
            </div>
        </div>
        """, unsafe_allow_html=True)

    with c_pub3:
        st.markdown(f"""
        <div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 20px;
                    box-shadow: 0 4px 16px rgba(0,0,0,{card_shadow});">
            <div style="font-size: 1.8rem; margin-bottom: 8px;">📈</div>
            <div style="font-weight: 700; color: {text_main}; margin-bottom: 6px;">Graduação & Autoaperfeiçoamento</div>
            <div style="font-size: 0.85rem; color: {text_muted}; line-height: 1.5;">
                Estudantes de Exatas (Engenharia, Matemática, Ciência da Computação) que buscam solidificar a base e eliminar lacunas.
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)

    # ── 5. Botões de Ação ────────────────────────────────────────────────────
    col_cta1, col_cta2, _ = st.columns([1.8, 1.8, 2.4])

    with col_cta1:
        if st.button("🚀 Começar a Treinar Agora", type="primary", use_container_width=True):
            st.session_state.nav_page = "🎯 Resolver / Simulado"
            st.rerun()

    with col_cta2:
        if st.button("📚 Explorar o Banco de Questões", use_container_width=True):
            st.session_state.nav_page = "📚 Banco & Listas"
            st.rerun()
