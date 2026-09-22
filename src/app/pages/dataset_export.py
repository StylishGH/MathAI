import json
import io
import streamlit as st
from src.database.db import pegar_conexao


def _carregar_dados_dataset(aluno_id=None):
    con = pegar_conexao()
    cur = con.cursor()
    try:
        sql = '''
            SELECT
                d.id AS diag_id, d.aluno_id, d.criado_em, d.modelo_gemini,
                d.justificativa_texto, d.transcricao_latex, d.passos_json,
                d.estrategia_identificada, d.status_resolucao, d.diagnostico,
                d.linha_do_erro, d.dica_proximo_passo, d.imagem_path,
                q.materia, q.topico, q.subtopico, q.banca, q.ano,
                q.dificuldade, q.enunciado, q.gabarito, q.estrategias_esperadas,
                t.acertou, t.tempo_segundos, t.estrategia_usada,
                t.tipo_erro, t.confianca_aluno
            FROM diagnosticos_ia d
            JOIN questoes q ON d.questao_id = q.id
            LEFT JOIN tentativas t ON d.tentativa_id = t.id
        '''
        params = []
        if aluno_id and aluno_id != 'Todos':
            sql += ' WHERE d.aluno_id = ?'
            params.append(aluno_id)
        sql += ' ORDER BY d.criado_em DESC'
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        st.error(f'Erro ao carregar dataset: {e}')
        return []
    finally:
        con.close()


def _carregar_log_dicas(aluno_id=None):
    con = pegar_conexao()
    cur = con.cursor()
    try:
        sql = '''
            SELECT l.*, q.topico, q.materia
            FROM log_dicas_socraticas l
            JOIN questoes q ON l.questao_id = q.id
        '''
        params = []
        if aluno_id and aluno_id != 'Todos':
            sql += ' WHERE l.aluno_id = ?'
            params.append(aluno_id)
        sql += ' ORDER BY l.criado_em DESC'
        cur.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        con.close()


def _para_json_treino(rows):
    resultado = []
    for r in rows:
        try:
            passos = json.loads(r.get('passos_json') or '[]')
        except Exception:
            passos = []
        entrada = {
            'questao_enunciado': r.get('enunciado', ''),
            'materia': r.get('materia', ''), 'topico': r.get('topico', ''),
            'subtopico': r.get('subtopico', ''), 'banca': r.get('banca', ''),
            'ano': r.get('ano'), 'dificuldade': r.get('dificuldade'),
            'gabarito': r.get('gabarito', ''),
            'estrategias_esperadas': r.get('estrategias_esperadas', ''),
            'justificativa_aluno': r.get('justificativa_texto', ''),
            'imagem_path': r.get('imagem_path', ''),
        }
        saida = {
            'transcricao_latex': r.get('transcricao_latex', ''),
            'passos': passos,
            'estrategia_identificada': r.get('estrategia_identificada', ''),
            'status_resolucao': r.get('status_resolucao', ''),
            'diagnostico': r.get('diagnostico', ''),
            'linha_do_erro': r.get('linha_do_erro'),
            'dica_proximo_passo': r.get('dica_proximo_passo', ''),
        }
        meta = {
            'aluno_id': r.get('aluno_id', 'default'),
            'modelo_gemini': r.get('modelo_gemini', ''),
            'acertou': bool(r.get('acertou')) if r.get('acertou') is not None else None,
            'tempo_segundos': r.get('tempo_segundos'),
            'estrategia_usada_pelo_aluno': r.get('estrategia_usada'),
            'tipo_erro': r.get('tipo_erro'),
            'confianca_aluno': r.get('confianca_aluno'),
            'criado_em': r.get('criado_em', ''),
        }
        resultado.append({'input': entrada, 'output': saida, 'metadados': meta})
    return resultado


def _listar_alunos():
    con = pegar_conexao()
    cur = con.cursor()
    try:
        cur.execute('SELECT DISTINCT aluno_id FROM diagnosticos_ia ORDER BY aluno_id')
        return [r['aluno_id'] for r in cur.fetchall()]
    except Exception:
        return []
    finally:
        con.close()


def show():
    st.markdown('## 🧠 Dataset & Treino da IA')
    st.caption(
        'Cada análise do Gemini + resposta do aluno = 1 exemplo de treino para o futuro modelo próprio. '
        'Exporte os dados para fine-tuning quando tiver amostras suficientes.'
    )

    con = pegar_conexao()
    cur = con.cursor()
    try:
        cur.execute('SELECT COUNT(*) as n FROM diagnosticos_ia')
        total_diag = cur.fetchone()['n']
        cur.execute('SELECT COUNT(*) as n FROM log_dicas_socraticas')
        total_dicas = cur.fetchone()['n']
        cur.execute('SELECT COUNT(DISTINCT aluno_id) as n FROM diagnosticos_ia')
        total_alunos = cur.fetchone()['n']
        cur.execute('SELECT COUNT(DISTINCT aluno_id) as n FROM tentativas')
        total_alunos_tent = cur.fetchone()['n']
    except Exception:
        total_diag = total_dicas = total_alunos = total_alunos_tent = 0
    finally:
        con.close()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric('📦 Análises IA Coletadas', total_diag, help='Exemplos de treino prontos')
    col2.metric('💡 Pedidos de Dica', total_dicas, help='Dados de comportamento de estudo')
    col3.metric('👤 Alunos (Diagnósticos)', total_alunos)
    col4.metric('👥 Alunos (Tentativas)', total_alunos_tent)

    st.markdown('---')

    aluno_filtro = st.selectbox(
        'Filtrar por aluno:',
        options=['Todos'] + _listar_alunos(),
        key='dataset_filtro_aluno'
    )
    aluno_sel = None if aluno_filtro == 'Todos' else aluno_filtro

    st.markdown('### 📊 Diagnósticos Coletados (Análises do Gemini)')
    rows = _carregar_dados_dataset(aluno_sel)

    if not rows:
        st.info('Nenhum diagnóstico coletado ainda. Use \"Analisar Rascunho com IA\" em alguma questão!')
    else:
        preview_cols = ['aluno_id', 'materia', 'topico', 'status_resolucao', 'estrategia_identificada', 'criado_em']
        preview = [{k: r.get(k, '') for k in preview_cols} for r in rows]
        st.dataframe(preview, use_container_width=True, height=280)

        st.markdown('---')
        st.markdown('### ⬇️ Exportar Dataset')

        col_j, col_c = st.columns(2)
        with col_j:
            json_treino = _para_json_treino(rows)
            json_bytes = json.dumps(json_treino, ensure_ascii=False, indent=2).encode('utf-8')
            st.download_button(
                label=f'⬇️ Baixar JSON ({len(rows)} amostras)',
                data=json_bytes,
                file_name='mathai_dataset_treino.json',
                mime='application/json',
                use_container_width=True,
                help='Formato pronto para fine-tuning (input/output/metadados)'
            )
        with col_c:
            import csv
            buf = io.StringIO()
            campos_csv = [
                'aluno_id', 'materia', 'topico', 'banca', 'dificuldade',
                'status_resolucao', 'estrategia_identificada',
                'justificativa_texto', 'transcricao_latex', 'diagnostico',
                'acertou', 'tempo_segundos', 'confianca_aluno', 'criado_em'
            ]
            writer = csv.DictWriter(buf, fieldnames=campos_csv, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(rows)
            st.download_button(
                label=f'⬇️ Baixar CSV ({len(rows)} linhas)',
                data=buf.getvalue().encode('utf-8'),
                file_name='mathai_dataset.csv',
                mime='text/csv',
                use_container_width=True,
                help='Para análise no Excel ou Google Colab'
            )

    st.markdown('---')
    st.markdown('### 💡 Log de Dicas Socráticas (Comportamento de Estudo)')
    dicas = _carregar_log_dicas(aluno_sel)
    if not dicas:
        st.info('Nenhuma dica socrática pedida ainda.')
    else:
        preview_dicas = [
            {'aluno': r.get('aluno_id'), 'materia': r.get('materia'),
             'topico': r.get('topico'), 'nivel': r.get('nivel_dica'),
             'data': str(r.get('criado_em', ''))[:16]}
            for r in dicas
        ]
        st.dataframe(preview_dicas, use_container_width=True, height=200)
        dicas_json = json.dumps(dicas, ensure_ascii=False, indent=2).encode('utf-8')
        st.download_button(
            '⬇️ Baixar Log de Dicas (JSON)',
            data=dicas_json,
            file_name='mathai_log_dicas.json',
            mime='application/json'
        )
