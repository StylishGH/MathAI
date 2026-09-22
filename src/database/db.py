"""
Gerenciador de Banco de Dados SQLite do MathAI.
Fase 0 (V0) - Fundação de Dados
"""

# Escreva aqui a sua conexão com o SQLite, inicialização do schema e funções de query!

import sqlite3
from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Caminho absoluto do arquivo de banco de dados na raiz do projeto

DB_PATH = BASE_DIR / "data" / "mathai.db"

#Lugar onde está as instruções de como montar o banco de dados
SCHEMA_PATH = BASE_DIR / "src" / "database" / "schema.sql"


def pegar_conexao():
    #verificação e criação da pasta data
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(DB_PATH)
    con.execute('PRAGMA foreign_keys = ON;')

    con.row_factory = sqlite3.Row

    return con

def init_db():
    con = pegar_conexao() 
    with open(SCHEMA_PATH,'r',encoding='utf-8') as f:
        schema_sql = f.read()
    con.executescript(schema_sql) 
    con.commit()
    con.close()

def _classificar_tipo(enunciado: str, gabarito: str) -> str:
    """Classifica automaticamente a questão como 'objetiva' ou 'discursiva'."""
    import re
    tem_alternativas = bool(re.search(r'(?m)^\(([A-E])\)\s*(.+)$', enunciado or ""))
    gabarito_e_letra = str(gabarito or "").strip().upper() in ("A", "B", "C", "D", "E")
    return "objetiva" if (tem_alternativas or gabarito_e_letra) else "discursiva"


def inserir_questao(
    materia,
    topico,
    enunciado,
    gabarito,
    subtopico=None,
    dificuldade=None,
    banca=None,
    ano=None,
    estrategias_esperadas=None,
    figura_path=None,
    tipo=None,          # 'objetiva' | 'discursiva' | None (auto-classifica)
):
    """Insere uma nova questão no banco de dados e retorna seu ID."""
    con = pegar_conexao()
    cur = con.cursor()

    # Se estratégias vier como lista (ex: ['Tales', 'Semelhança']), converte para texto JSON:
    if isinstance(estrategias_esperadas, list):
        estrategias_esperadas = json.dumps(estrategias_esperadas, ensure_ascii=False)

    # Auto-classifica se tipo não for informado
    if tipo not in ("objetiva", "discursiva"):
        tipo = _classificar_tipo(enunciado, gabarito)

    sql = """
        INSERT INTO questoes (
            materia,
            topico,
            subtopico,
            dificuldade,
            banca,
            ano,
            enunciado,
            figura_path,
            gabarito,
            estrategias_esperadas,
            tipo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    cur.execute(sql, (
        materia,
        topico,
        subtopico,
        dificuldade,
        banca,
        ano,
        enunciado,
        figura_path,
        gabarito,
        estrategias_esperadas,
        tipo,
    ))

    con.commit()
    novo_id = cur.lastrowid
    con.close()

    return novo_id


def listar_questoes():
    """Retorna todas as questões cadastradas no banco."""
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT * FROM questoes")
    questoes = cur.fetchall()
    con.close()
    return questoes

def buscar_questao_por_id(questao_id):
    """Busca e retorna uma única questão pelo seu ID."""
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT * FROM questoes WHERE id = ?", (questao_id,))
    questao = cur.fetchone()
    con.close()
    return questao


def limpar_questoes():
    """Apaga todas as questões e reseta o contador de IDs para 1."""
    con = pegar_conexao()
    con.execute("DELETE FROM questoes;")
    con.execute("DELETE FROM sqlite_sequence WHERE name = 'questoes';")
    con.commit()
    con.close()
    print("Tabela 'questoes' limpa e ID resetado com sucesso!")


def excluir_questao(questao_id, reordenar=True):
    """
    Apaga uma questão específica pelo ID e ajusta o contador do SQLite.
    Se reordenar=True, diminui em 1 os IDs das questões que vinham depois.
    """
    con = pegar_conexao()
    cur = con.cursor()
    
    # 1. Deleta a questão
    cur.execute("DELETE FROM questoes WHERE id = ?", (questao_id,))
    
    # 2. Se for para fechar o 'buraco' na fila de IDs:
    if reordenar:
        cur.execute("UPDATE questoes SET id = id - 1 WHERE id > ?", (questao_id,))
    
    # 3. Sincroniza o contador autoincrement com o maior ID restante
    cur.execute("""
        UPDATE sqlite_sequence 
        SET seq = (SELECT COALESCE(MAX(id), 0) FROM questoes) 
        WHERE name = 'questoes'
    """)
    con.commit()
    con.close()
    print(f"Questão {questao_id} excluída e sequência de IDs recalculada com sucesso!")





if __name__ == "__main__":
    init_db()
    print("Módulo db.py executado diretamente. Banco verificado.")
