"""
Página do Dashboard Cognitivo e Métricas de Desempenho do Estudante.
Apresenta gráficos interativos via Plotly e histórico de tentativas.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from src.database.attempts import obter_metricas_estudante, obter_historico_tentativas
from src.database.db import pegar_conexao


def show():
    st.markdown("## 📊 Perfil Cognitivo & Métricas de Desempenho")
    st.caption("Visão analítica de domínio matemático, repertório de estratégias e diagnóstico de erros.")

    aluno_id = st.session_state.get("aluno_id")
    metricas = obter_metricas_estudante(aluno_id=aluno_id)
    total_resolvidas = metricas["total_resolvidas"]

    # 1. Estado Vazio (Nenhuma tentativa registrada ainda)
    if total_resolvidas == 0:
        st.info("💡 Você ainda não registrou nenhuma tentativa de resolução! Vá para a aba **🎯 Resolver Questões** e inicie seu treinamento.")
        return

    # 2. Linha de Métricas Principais (KPIs)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="Total Resolvidas",
            value=f"{total_resolvidas}",
            help="Número total de tentativas registradas no banco"
        )
    with col2:
        taxa = metricas["taxa_acerto"]
        st.metric(
            label="Taxa de Acerto",
            value=f"{taxa}%",
            delta=f"{'+' if taxa >= 70 else ''}{taxa - 50:.1f}% vs base (50%)" if total_resolvidas > 1 else None
        )
    with col3:
        tempo_medio = metricas["tempo_medio"]
        mins = int(tempo_medio // 60)
        segs = int(tempo_medio % 60)
        tempo_str = f"{mins}m {segs:02d}s" if mins > 0 else f"{segs}s"
        st.metric(
            label="Tempo Médio",
            value=tempo_str,
            help="Tempo médio por questão com cronômetro"
        )
    with col4:
        st.metric(
            label="Total de Acertos",
            value=f"{metricas['total_acertos']} / {total_resolvidas}",
            help="Acertos sobre o total de resoluções"
        )

    st.markdown("---")

    # 3. Gráficos Cognitivos (Radar de Domínio + Distribuição de Estratégias)
    col_radar, col_estrategias = st.columns([1, 1])

    with col_radar:
        st.markdown("### 🕸️ Domínio por Matéria")
        materias_data = metricas["materias"]
        if materias_data:
            df_mat = pd.DataFrame(materias_data)
            if len(df_mat) >= 3:
                # Gráfico de Radar para 3 ou mais matérias
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=df_mat["taxa_acerto"].tolist() + [df_mat["taxa_acerto"].iloc[0]],
                    theta=df_mat["materia"].tolist() + [df_mat["materia"].iloc[0]],
                    fill='toself',
                    fillcolor='rgba(99, 102, 241, 0.25)',
                    line=dict(color='#6366f1', width=2),
                    marker=dict(size=6, color='#4f46e5'),
                    name='Taxa de Acerto (%)'
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], ticksuffix="%"),
                    ),
                    showlegend=False,
                    margin=dict(l=40, r=40, t=30, b=30),
                    height=340
                )
                st.plotly_chart(fig_radar, use_container_width=True)
            else:
                # Gráfico de barras quando há poucas matérias para o radar
                fig_bar_mat = px.bar(
                    df_mat,
                    x="materia",
                    y="taxa_acerto",
                    color="taxa_acerto",
                    color_continuous_scale="Purples",
                    labels={"materia": "Matéria", "taxa_acerto": "Taxa de Acerto (%)"},
                    text="taxa_acerto"
                )
                fig_bar_mat.update_layout(
                    showlegend=False,
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=340,
                    yaxis=dict(range=[0, 100], ticksuffix="%"),
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_bar_mat, use_container_width=True)
        else:
            st.caption("Sem dados suficientes para o radar.")

    with col_estrategias:
        st.markdown("### 💡 Repertório de Estratégias")
        estrategias_data = metricas["estrategias"]
        if estrategias_data:
            df_est = pd.DataFrame(estrategias_data)
            fig_est = px.bar(
                df_est,
                x="quantidade",
                y="estrategia_usada",
                orientation="h",
                color="quantidade",
                color_continuous_scale="Purples",
                labels={"quantidade": "Utilizações", "estrategia_usada": "Estratégia"}
            )
            fig_est.update_layout(
                showlegend=False,
                margin=dict(l=20, r=20, t=20, b=20),
                height=340,
                coloraxis_showscale=False,
                yaxis=dict(autorange="reversed")
            )
            st.plotly_chart(fig_est, use_container_width=True)
        else:
            st.caption("Nenhuma estratégia registrada ainda.")

    # 4. Diagnóstico de Erros + Revisão Espaçada (SM-2)
    col_erros, col_revisao = st.columns([1, 1])

    with col_erros:
        st.markdown("### 🔍 Diagnóstico de Padrões de Erro")
        erros_data = metricas["erros"]
        if erros_data:
            df_err = pd.DataFrame(erros_data)
            nomes_erros = {
                "conta_sinal": "Conta / Sinal",
                "manipulacao_algebrica": "Manipulação Algébrica",
                "conceitual": "Erro Conceitual",
                "interpretacao": "Interpretação",
                "outro": "Outro"
            }
            df_err["tipo_formatado"] = df_err["tipo_erro"].map(lambda x: nomes_erros.get(x, x))

            fig_err = px.pie(
                df_err,
                names="tipo_formatado",
                values="quantidade",
                hole=0.45,
                color_discrete_sequence=["#ef4444", "#f97316", "#eab308", "#8b5cf6", "#64748b"]
            )
            fig_err.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=300
            )
            st.plotly_chart(fig_err, use_container_width=True)
        else:
            st.success("🎉 Nenhum erro registrado até o momento! Excelente desempenho.")

    with col_revisao:
        st.markdown("### ⏰ Próximas Revisões (SM-2)")
        con = pegar_conexao()
        cur = con.cursor()
        cur.execute("""
            SELECT 
                r.item_id as questao_id,
                q.materia,
                q.topico,
                r.intervalo_dias,
                r.repeticoes,
                r.proxima_revisao
            FROM revisao_espacada r
            JOIN questoes q ON r.item_id = q.id
            ORDER BY r.proxima_revisao ASC
            LIMIT 5
        """)
        revisoes = cur.fetchall()
        con.close()

        if revisoes:
            for rev in revisoes:
                st.markdown(
                    f"""
                    <div style="background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(128,128,128,0.2); border-radius: 8px; padding: 10px 14px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <b>Questão #{rev['questao_id']:02d}</b> • {rev['materia']} ({rev['topico']})
                            <div style="font-size: 0.8rem; color: #888;">Ciclo #{rev['repeticoes']} • Intervalo: {rev['intervalo_dias']} dia(s)</div>
                        </div>
                        <span style="background: rgba(99, 102, 241, 0.2); color: #6366f1; font-weight: 600; padding: 4px 10px; border-radius: 6px; font-size: 0.85rem;">
                            📅 {rev['proxima_revisao']}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.caption("Nenhuma questão agendada para repetição espaçada.")

    st.markdown("---")

    # 5. Histórico Recente de Resoluções
    st.markdown("### 📜 Histórico Recente de Resoluções")
    historico = obter_historico_tentativas(limite=20, aluno_id=aluno_id)
    if historico:
        itens_hist = []
        for h in historico:
            acertou_tag = "✅ Acertou" if h["acertou"] else "❌ Errou"
            mins = h["tempo_segundos"] // 60
            segs = h["tempo_segundos"] % 60
            tempo_str = f"{mins}m {segs:02d}s" if mins > 0 else f"{segs}s"

            tem_imagem = "📷 Sim" if dict(h).get("imagem_resolucao_path") else "-"
            itens_hist.append({
                "Data/Hora": h["data_hora"],
                "Questão": f"{h['materia']} ({h['topico']})",
                "Gabarito": h["gabarito"],
                "Resultado": acertou_tag,
                "Tempo": tempo_str,
                "Estratégia": h["estrategia_usada"] or "-",
                "Causa do Erro": h["tipo_erro"] if not h["acertou"] else "-",
                "Confiança": f"{h['confianca_aluno']}/5",
                "Rascunho": tem_imagem,
                "Anotações": h["anotacoes"] or ""
            })

        df_hist = pd.DataFrame(itens_hist)
        st.dataframe(df_hist, use_container_width=True)

        tentativas_com_imagem = [h for h in historico if dict(h).get("imagem_resolucao_path")]
        if tentativas_com_imagem:
            with st.expander("🖼️ Ver Rascunhos / Imagens de Resoluções Anteriores"):
                cols_img = st.columns(min(len(tentativas_com_imagem), 3))
                for idx_img, t_img in enumerate(tentativas_com_imagem[:6]):
                    with cols_img[idx_img % 3]:
                        st.caption(f"Questão #{t_img['topico']} • {t_img['data_hora']}")
                        st.image(t_img["imagem_resolucao_path"], use_container_width=True)
