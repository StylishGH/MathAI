"""
Componente de exibição de questões matemáticas com suporte a LaTeX, texto justificado e SVG.
"""

import base64
from pathlib import Path
import streamlit as st
from src.app.utils import extrair_enunciado_e_alternativas, corrigir_latex


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

        tags_html = f"""
        <div style="display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; align-items: center;">
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
    enunciado_raw = questao.get("enunciado", "")
    # Corrige bugs de LaTeX antes de renderizar (ex: 8imes8 -> 8\times 8)
    enunciado_raw = corrigir_latex(enunciado_raw)
    corpo, alternativas = extrair_enunciado_e_alternativas(enunciado_raw)
    texto_exibir = corpo if alternativas else enunciado_raw

    st.markdown(texto_exibir)

    # 3. Figura associada (se houver)
    figura_path = questao.get("figura_path")
    if figura_path:
        p = Path(figura_path)
        if not p.is_absolute():
            p = Path(__file__).resolve().parent.parent.parent.parent / figura_path

        if p.exists():
            st.markdown("<br>", unsafe_allow_html=True)
            if p.suffix.lower() == ".svg":
                b64_svg = base64.b64encode(p.read_bytes()).decode("utf-8")
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: center; margin: 16px 0;">
                        <img src="data:image/svg+xml;base64,{b64_svg}" 
                             alt="Diagrama Matemático"
                             style="max-width: 540px; width: 100%; border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; padding: 12px; background: white;" />
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                # Imagem PNG/JPG: centralizada com tamanho controlado (máx 480px)
                # Não usar use_container_width=True pois estica até 100% da tela
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
                             style="max-width: 480px; width: 100%; border: 1px solid rgba(128,128,128,0.2);
                                    border-radius: 12px; padding: 8px; background: {'#1a1726' if is_dark else 'white'};
                                    box-shadow: 0 4px 12px rgba(0,0,0,{'0.4' if is_dark else '0.1'});" />
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
