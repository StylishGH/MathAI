"""
Componente de exibição de questões matemáticas com suporte a LaTeX, texto justificado e SVG.
"""

import base64
from pathlib import Path
import streamlit as st
from src.app.utils import extrair_enunciado_e_alternativas, corrigir_latex


def _localizar_arquivo_figura(fp: str) -> Path | None:
    """Busca o arquivo de figura de forma resiliente tanto local quanto no Streamlit Cloud."""
    if not fp:
        return None
    raw = str(fp).strip().replace("\\", "/")
    nome_arquivo = Path(raw).name

    p_abs = Path(raw)
    if p_abs.is_absolute() and p_abs.exists():
        return p_abs

    rel_limpo = raw.lstrip("/")

    candidatos_base = [
        Path.cwd(),
        Path(__file__).resolve().parent.parent.parent.parent,
        Path(__file__).resolve().parent.parent.parent,
        Path(__file__).resolve().parent.parent,
    ]

    for base in candidatos_base:
        cand = base / rel_limpo
        if cand.exists():
            return cand
        cand_upload = base / "data" / "uploads" / nome_arquivo
        if cand_upload.exists():
            return cand_upload
        if rel_limpo.startswith("data/"):
            cand_sem_data = base / rel_limpo[5:]
            if cand_sem_data.exists():
                return cand_sem_data

    return None


def render_question(questao: dict, mostrar_alternativas: bool = False):
    """
    Renderiza o cabeçalho, enunciado com texto justificado e LaTeX,
    figura (SVG ou PNG) e opcionalmente as alternativas estáticas.
    """
    is_dark = (st.session_state.get("tema", "dark") == "dark")

    # Cores dos Badges ajustadas para contraste no modo claro e escuro
    mat_color = "#c4b5fd" if is_dark else "#6d28d9"
    mat_bg = "rgba(124, 58, 237, 0.18)" if is_dark else "rgba(124, 58, 237, 0.12)"
    top_color = "#a5b4fc" if is_dark else "#4338ca"
    top_bg = "rgba(99, 102, 241, 0.15)" if is_dark else "rgba(99, 102, 241, 0.12)"
    gold_color = "#fbbf24" if is_dark else "#b45309"
    gold_bg = "rgba(245, 158, 11, 0.15)" if is_dark else "rgba(245, 158, 11, 0.12)"

    # 1. Cabeçalho da Questão com Badges (Dourado & Roxo)
    col_info, col_id = st.columns([4, 1])
    with col_info:
        materia = questao.get("materia", "")
        topico = questao.get("topico", "")
        banca = questao.get("banca", "")
        ano = questao.get("ano", "")
        banca_ano = f"{banca} {ano}" if banca and ano else (banca or (str(ano) if ano else ""))

        tipo = str(questao.get("tipo", "")).strip().lower()
        if not tipo:
            from src.app.utils import e_questao_discursiva
            tipo = "discursiva" if e_questao_discursiva(questao) else "objetiva"

        if tipo == "discursiva":
            badge_tipo = '<span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700;">📝 Discursiva</span>'
        else:
            badge_tipo = '<span style="background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.4); padding: 4px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700;">🎯 Objetiva</span>'

        tags_html = f"""
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; align-items: center;">
            {badge_tipo}
            <span style="background: {mat_bg}; color: {mat_color}; border: 1px solid rgba(124, 58, 237, 0.35); padding: 4px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700;">
                {materia}
            </span>
            <span style="background: {top_bg}; color: {top_color}; border: 1px solid rgba(99, 102, 241, 0.3); padding: 4px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 600;">
                {topico}
            </span>
            {f'<span style="background: {gold_bg}; color: {gold_color}; border: 1px solid rgba(245, 158, 11, 0.45); padding: 4px 12px; border-radius: 9999px; font-size: 0.82rem; font-weight: 700; box-shadow: 0 0 10px rgba(245, 158, 11, 0.2);">{banca_ano}</span>' if banca_ano else ''}
        </div>
        """
        st.markdown(tags_html, unsafe_allow_html=True)

    with col_id:
        st.markdown(
            f"""
            <div style="text-align: right;">
                <span style="background: {gold_bg}; color: {gold_color}; border: 1px solid rgba(245, 158, 11, 0.35);
                             padding: 4px 10px; border-radius: 8px; font-size: 0.85rem; font-weight: 700; font-family: monospace;">
                    #{questao.get('id', 0):02d}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

    # 2. Enunciado com Texto Justificado e LaTeX
    import re
    enunciado_raw = questao.get("enunciado", "")
    # Corrige bugs de LaTeX antes de renderizar (ex: 8imes8 -> 8\times 8)
    enunciado_raw = corrigir_latex(enunciado_raw)
    corpo, alternativas = extrair_enunciado_e_alternativas(enunciado_raw)
    texto_exibir = corpo if alternativas else enunciado_raw
    # Remove tags residuais de imagem no markdown (ex: ![](attached_image_1.png))
    texto_exibir = re.sub(r'!\[.*?\]\(.*?\)', '', texto_exibir).strip()

    st.markdown(texto_exibir)

    # 3. Figura(s) associada(s) (suporta 1 ou múltiplas imagens)
    figura_raw = questao.get("figura_path")
    lista_figuras = []
    if figura_raw:
        if str(figura_raw).strip().startswith("["):
            try:
                import json
                lista_figuras = json.loads(figura_raw)
            except Exception:
                lista_figuras = [figura_raw]
        elif "," in str(figura_raw):
            lista_figuras = [f.strip() for f in str(figura_raw).split(",") if f.strip()]
        else:
            lista_figuras = [str(figura_raw).strip()]

    # Fallback inteligente por metadados da questão caso o campo figura_path no banco esteja nulo
    if not lista_figuras:
        banca = str(questao.get("banca", "")).strip().upper()
        ano = str(questao.get("ano", "")).strip()
        enunc = str(questao.get("enunciado", "")).lower()
        if banca == "ESA" and ano == "2026":
            if "log_2" in enunc or "região sombreada" in enunc or "regiao sombreada" in enunc:
                lista_figuras = ["data/uploads/esa_2026_q02.svg"]
            elif "5 questões" in enunc or "5 questoes" in enunc or "moda" in enunc:
                lista_figuras = ["data/uploads/esa_2026_q06.svg"]
            elif "pelotão de obras" in enunc or "pelotao de obras" in enunc:
                lista_figuras = ["data/uploads/esa_2026_q09.svg"]
            elif "paralelepípedo" in enunc or "paralelepipedo" in enunc or "abcdefgh" in enunc:
                lista_figuras = ["data/uploads/esa_2026_q10.svg"]

    for fp in lista_figuras:
        p = _localizar_arquivo_figura(fp)

        if p and p.exists():
            st.markdown("<br>", unsafe_allow_html=True)
            if p.suffix.lower() == ".svg":
                b64_svg = base64.b64encode(p.read_bytes()).decode("utf-8")
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; margin: 16px 0;">
                        <img src="data:image/svg+xml;base64,{b64_svg}" 
                             alt="Diagrama Matemático"
                             style="max-width: 540px; width: auto; border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; padding: 12px; background: white;" />
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Imagem PNG/JPG: centralizada com tamanho natural e fundo branco para máxima legibilidade
                img_bytes = p.read_bytes()
                import base64 as _b64
                ext = p.suffix.lower().lstrip(".")
                mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
                b64_img = _b64.b64encode(img_bytes).decode("utf-8")
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; margin: 16px 0;">
                        <img src="data:{mime};base64,{b64_img}"
                             alt="Figura da Questão"
                             style="min-width: 140px; max-width: 520px; width: auto; height: auto; max-height: 420px;
                                    image-rendering: crisp-edges; image-rendering: pixelated;
                                    border: 1px solid rgba(128,128,128,0.25);
                                    border-radius: 12px; padding: 12px; background: #ffffff;
                                    box-shadow: 0 4px 14px rgba(0,0,0,{'0.4' if is_dark else '0.1'});" />
                    </div>
                    """,
                    unsafe_allow_html=True
                )

    # 4. Alternativas estáticas (usado para preview opcional)
    if mostrar_alternativas and alternativas:
        alt_bg = "rgba(255, 255, 255, 0.03)" if is_dark else "#f8fafc"
        alt_border = "rgba(128, 128, 128, 0.2)" if is_dark else "#cbd5e1"
        alt_color = "#f8fafc" if is_dark else "#0f172a"
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("##### Alternativas:")
        for letra, texto_alt in alternativas.items():
            st.markdown(
                f"""
                <div style="background: {alt_bg}; border: 1px solid {alt_border}; color: {alt_color}; border-radius: 8px; padding: 8px 14px; margin-bottom: 6px;">
                    <b>({letra})</b> {texto_alt}
                </div>
                """,
                unsafe_allow_html=True
            )

    # 5. Botão Discreto de Reportar Problema
    q_id = questao.get("id", 0)
    col_vazia, col_rep = st.columns([4.2, 1.3])
    with col_rep:
        with st.popover("🚩 Reportar", use_container_width=True):
            st.markdown(f"**Reportar Questão #{q_id:02d}**")
            st.caption("Identificou algum erro no enunciado, LaTeX ou figura?")
            motivo = st.selectbox(
                "Tipo de problema:",
                [
                    "📐 Fórmula ou LaTeX quebrado",
                    "🖼️ Figura ausente ou ilegível",
                    "📝 Tradução confusa / termos errados",
                    "🎯 Gabarito incorreto",
                    "⚠️ Outro problema"
                ],
                key=f"rep_motivo_{q_id}"
            )
            detalhes = st.text_area(
                "Descrição (opcional):",
                placeholder="Ex: No passo final faltou um sinal de menos...",
                key=f"rep_detalhes_{q_id}"
            )
            if st.button("Enviar Reporte", type="primary", use_container_width=True, key=f"btn_send_rep_{q_id}"):
                from src.database.db import reportar_questao
                aluno_id = st.session_state.get("aluno_id")
                reportar_questao(questao_id=q_id, motivo=motivo, descricao=detalhes, aluno_id=aluno_id)
                st.success("✅ Reporte enviado! Nossa equipe revisará.")
