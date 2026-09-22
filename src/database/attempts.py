"""
Módulo de registro e análise de tentativas de resolução do MathAI.
Fase 1 (V1) - Rastreamento Cognitivo e Métricas do Estudante.
"""

from datetime import datetime, timedelta
import json
from src.database.db import pegar_conexao


def registrar_tentativa(
    questao_id: int,
    tempo_segundos: int,
    acertou: bool,
    aluno_id: str = "default",
    estrategia_usada: str | None = None,
    tipo_erro: str = "nenhum",
    confianca_aluno: int = 3,
    anotacoes: str | None = None,
    imagem_resolucao_path: str | None = None
) -> int:
    """
    Registra uma nova sessão de resolução na tabela 'tentativas'
    e atualiza as métricas agregadas do estudante (perfil_aluno_topico)
    e o agendamento de repetição espaçada (SM-2).
    """
    con = pegar_conexao()
    cur = con.cursor()

    # Migração automática: adiciona aluno_id se não existir ainda (banco antigo)
    try:
        cur.execute("ALTER TABLE tentativas ADD COLUMN aluno_id TEXT NOT NULL DEFAULT 'default'")
        con.commit()
    except Exception:
        pass  # Coluna já existe

    acertou_int = 1 if acertou else 0

    # 1. Inserir na tabela tentativas
    sql_tentativa = """
        INSERT INTO tentativas (
            questao_id, aluno_id, tempo_segundos, acertou, estrategia_usada,
            tipo_erro, confianca_aluno, anotacoes, imagem_resolucao_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur.execute(sql_tentativa, (
        questao_id, aluno_id, tempo_segundos, acertou_int, estrategia_usada,
        tipo_erro, confianca_aluno, anotacoes, imagem_resolucao_path
    ))
    tentativa_id = cur.lastrowid

    # 2. Buscar metadados da questão para atualizar perfil
    cur.execute("SELECT materia, topico FROM questoes WHERE id = ?", (questao_id,))
    q_meta = cur.fetchone()
    if q_meta:
        materia, topico = q_meta["materia"], q_meta["topico"]

        # Busca perfil atual do tópico
        cur.execute("SELECT * FROM perfil_aluno_topico WHERE materia = ? AND topico = ?", (materia, topico))
        perfil = cur.fetchone()

        if perfil:
            novo_total = perfil["total_tentativas"] + 1
            novo_acertos = perfil["total_acertos"] + acertou_int
            novo_tempo_medio = (
                (perfil["tempo_medio_segundos"] * perfil["total_tentativas"]) + tempo_segundos
            ) / novo_total

            cur.execute("""
                UPDATE perfil_aluno_topico 
                SET total_tentativas = ?, total_acertos = ?, tempo_medio_segundos = ?, atualizado_em = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (novo_total, novo_acertos, novo_tempo_medio, perfil["id"]))
        else:
            cur.execute("""
                INSERT INTO perfil_aluno_topico (
                    materia, topico, total_tentativas, total_acertos, tempo_medio_segundos, estrategia_favorita
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (materia, topico, 1, acertou_int, float(tempo_segundos), estrategia_usada))

    # 3. Atualizar Repetição Espaçada (SM-2 simplificado)
    cur.execute(
        "SELECT * FROM revisao_espacada WHERE item_tipo = 'questao' AND item_id = ?",
        (questao_id,)
    )
    rev = cur.fetchone()

    if acertou:
        repeticoes = (rev["repeticoes"] + 1) if rev else 1
        if repeticoes == 1:
            intervalo = 1
        elif repeticoes == 2:
            intervalo = 3
        else:
            fator = rev["fator_facilidade"] if rev else 2.5
            intervalo = int((rev["intervalo_dias"] if rev else 3) * fator)
    else:
        repeticoes = 0
        intervalo = 1

    proxima_data = (datetime.now() + timedelta(days=intervalo)).strftime("%Y-%m-%d")

    if rev:
        cur.execute("""
            UPDATE revisao_espacada
            SET intervalo_dias = ?, repeticoes = ?, proxima_revisao = ?, ultima_revisao = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (intervalo, repeticoes, proxima_data, rev["id"]))
    else:
        cur.execute("""
            INSERT INTO revisao_espacada (
                item_tipo, item_id, intervalo_dias, repeticoes, proxima_revisao
            ) VALUES ('questao', ?, ?, ?, ?)
        """, (questao_id, intervalo, repeticoes, proxima_data))

    con.commit()
    con.close()
    return tentativa_id


def obter_historico_tentativas(limite: int = 50, aluno_id: str | None = None):
    """Retorna as últimas tentativas com informações da questão associada."""
    con = pegar_conexao()
    cur = con.cursor()
    if aluno_id:
        cur.execute("""
            SELECT 
                t.id, t.data_hora, t.tempo_segundos, t.acertou, t.estrategia_usada, 
                t.tipo_erro, t.confianca_aluno, t.anotacoes, t.imagem_resolucao_path,
                q.materia, q.topico, q.banca, q.ano, q.enunciado, q.gabarito
            FROM tentativas t
            JOIN questoes q ON t.questao_id = q.id
            WHERE t.aluno_id = ?
            ORDER BY t.data_hora DESC
            LIMIT ?
        """, (aluno_id, limite))
    else:
        cur.execute("""
            SELECT 
                t.id, t.data_hora, t.tempo_segundos, t.acertou, t.estrategia_usada, 
                t.tipo_erro, t.confianca_aluno, t.anotacoes, t.imagem_resolucao_path,
                q.materia, q.topico, q.banca, q.ano, q.enunciado, q.gabarito
            FROM tentativas t
            JOIN questoes q ON t.questao_id = q.id
            ORDER BY t.data_hora DESC
            LIMIT ?
        """, (limite,))
    historico = cur.fetchall()
    con.close()
    return historico


def obter_metricas_estudante(aluno_id: str | None = None):
    """
    Agrega dados de tentativas para alimentar o Dashboard do Estudante:
    - Métricas gerais (total, acertos, taxa, tempo médio)
    - Desempenho por matéria (para gráfico radar)
    - Distribuição de estratégias usadas
    - Distribuição de erros
    """
    con = pegar_conexao()
    cur = con.cursor()

    # 1. Totais Gerais
    if aluno_id:
        cur.execute("""
            SELECT 
                COUNT(*) as total_resolvidas,
                COALESCE(SUM(acertou), 0) as total_acertos,
                COALESCE(AVG(tempo_segundos), 0) as tempo_medio
            FROM tentativas
            WHERE aluno_id = ?
        """, (aluno_id,))
    else:
        cur.execute("""
            SELECT 
                COUNT(*) as total_resolvidas,
                COALESCE(SUM(acertou), 0) as total_acertos,
                COALESCE(AVG(tempo_segundos), 0) as tempo_medio
            FROM tentativas
        """)
    geral = cur.fetchone()

    total_resolvidas = geral["total_resolvidas"] if geral else 0
    total_acertos = geral["total_acertos"] if geral else 0
    tempo_medio = round(geral["tempo_medio"], 1) if geral and geral["tempo_medio"] else 0.0
    taxa_acerto = round((total_acertos / total_resolvidas * 100), 1) if total_resolvidas > 0 else 0.0

    # 2. Desempenho por Matéria
    if aluno_id:
        cur.execute("""
            SELECT 
                q.materia,
                COUNT(t.id) as tentativas,
                SUM(t.acertou) as acertos,
                ROUND(AVG(t.acertou) * 100, 1) as taxa_acerto,
                ROUND(AVG(t.tempo_segundos), 1) as tempo_medio
            FROM tentativas t
            JOIN questoes q ON t.questao_id = q.id
            WHERE t.aluno_id = ?
            GROUP BY q.materia
        """, (aluno_id,))
    else:
        cur.execute("""
            SELECT 
                q.materia,
                COUNT(t.id) as tentativas,
                SUM(t.acertou) as acertos,
                ROUND(AVG(t.acertou) * 100, 1) as taxa_acerto,
                ROUND(AVG(t.tempo_segundos), 1) as tempo_medio
            FROM tentativas t
            JOIN questoes q ON t.questao_id = q.id
            GROUP BY q.materia
        """)
    materias = cur.fetchall()

    # 3. Distribuição de Estratégias
    if aluno_id:
        cur.execute("""
            SELECT 
                estrategia_usada,
                COUNT(*) as quantidade,
                SUM(acertou) as acertos
            FROM tentativas
            WHERE aluno_id = ? AND estrategia_usada IS NOT NULL AND estrategia_usada != ''
            GROUP BY estrategia_usada
            ORDER BY quantidade DESC
        """, (aluno_id,))
    else:
        cur.execute("""
            SELECT 
                estrategia_usada,
                COUNT(*) as quantidade,
                SUM(acertou) as acertos
            FROM tentativas
            WHERE estrategia_usada IS NOT NULL AND estrategia_usada != ''
            GROUP BY estrategia_usada
            ORDER BY quantidade DESC
        """)
    estrategias = cur.fetchall()

    # 4. Distribuição de Erros (quando errou)
    if aluno_id:
        cur.execute("""
            SELECT 
                tipo_erro,
                COUNT(*) as quantidade
            FROM tentativas
            WHERE aluno_id = ? AND acertou = 0 AND tipo_erro != 'nenhum'
            GROUP BY tipo_erro
            ORDER BY quantidade DESC
        """, (aluno_id,))
    else:
        cur.execute("""
            SELECT 
                tipo_erro,
                COUNT(*) as quantidade
            FROM tentativas
            WHERE acertou = 0 AND tipo_erro != 'nenhum'
            GROUP BY tipo_erro
            ORDER BY quantidade DESC
        """)
    erros = cur.fetchall()

    con.close()

    return {
        "total_resolvidas": total_resolvidas,
        "total_acertos": total_acertos,
        "taxa_acerto": taxa_acerto,
        "tempo_medio": tempo_medio,
        "materias": [dict(m) for m in materias],
        "estrategias": [dict(e) for e in estrategias],
        "erros": [dict(err) for err in erros]
    }


def salvar_diagnostico_ia(
    questao_id: int,
    diagnostico_dict: dict,
    aluno_id: str = "default",
    tentativa_id: int | None = None,
    imagem_path: str | None = None,
    justificativa_texto: str | None = None
) -> int:
    """
    Salva a análise de raciocínio gerada pelo Gemini na tabela 'diagnosticos_ia'.
    Isso constrói o dataset para o futuro modelo local em PyTorch.
    """
    con = pegar_conexao()
    cur = con.cursor()

    # Garante que a tabela exista e tenha as colunas novas (migração automática)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS diagnosticos_ia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tentativa_id INTEGER,
            questao_id INTEGER NOT NULL,
            aluno_id TEXT NOT NULL DEFAULT 'default',
            modelo_gemini TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            imagem_path TEXT,
            justificativa_texto TEXT,
            transcricao_latex TEXT,
            passos_json TEXT,
            estrategia_identificada TEXT,
            status_resolucao TEXT,
            diagnostico TEXT,
            linha_do_erro TEXT,
            dica_proximo_passo TEXT,
            FOREIGN KEY (questao_id) REFERENCES questoes (id) ON DELETE CASCADE,
            FOREIGN KEY (tentativa_id) REFERENCES tentativas (id) ON DELETE SET NULL
        )
    """)
    for col, coldef in [("aluno_id", "TEXT NOT NULL DEFAULT 'default'"), ("modelo_gemini", "TEXT")]:
        try:
            cur.execute(f"ALTER TABLE diagnosticos_ia ADD COLUMN {col} {coldef}")
            con.commit()
        except Exception:
            pass  # Já existe

    passos_json = json.dumps(diagnostico_dict.get("passos", []), ensure_ascii=False)

    sql = """
        INSERT INTO diagnosticos_ia (
            tentativa_id, questao_id, aluno_id, modelo_gemini,
            imagem_path, justificativa_texto,
            transcricao_latex, passos_json, estrategia_identificada,
            status_resolucao, diagnostico, linha_do_erro, dica_proximo_passo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cur.execute(sql, (
        tentativa_id,
        questao_id,
        aluno_id,
        diagnostico_dict.get("modelo_utilizado"),
        imagem_path,
        justificativa_texto,
        diagnostico_dict.get("transcricao_latex"),
        passos_json,
        diagnostico_dict.get("estrategia_identificada"),
        diagnostico_dict.get("status_resolucao"),
        diagnostico_dict.get("diagnostico"),
        diagnostico_dict.get("linha_do_erro"),
        diagnostico_dict.get("dica_proximo_passo")
    ))
    diag_id = cur.lastrowid
    con.commit()
    con.close()
    return diag_id


def registrar_dica_socratica(
    questao_id: int,
    nivel_dica: int,
    texto_dica: str,
    modelo_gemini: str = "",
    aluno_id: str = "default"
) -> None:
    """
    Registra cada pedido de dica socrática no banco.
    Gera dados sobre o padrão de dependência de ajuda do aluno.
    """
    con = pegar_conexao()
    cur = con.cursor()
    # Cria tabela se não existir (banco antigo)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS log_dicas_socraticas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            questao_id INTEGER NOT NULL,
            aluno_id TEXT NOT NULL DEFAULT 'default',
            nivel_dica INTEGER NOT NULL,
            texto_dica TEXT,
            modelo_gemini TEXT,
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute(
        "INSERT INTO log_dicas_socraticas (questao_id, aluno_id, nivel_dica, texto_dica, modelo_gemini) VALUES (?,?,?,?,?)",
        (questao_id, aluno_id, nivel_dica, texto_dica, modelo_gemini)
    )
    con.commit()
    con.close()
