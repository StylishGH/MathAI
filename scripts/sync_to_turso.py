import sqlite3
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.database.db import pegar_conexao, inserir_questao, TursoConnection

def sync_to_turso():
    # 1. Limpar as Olimpíadas do Turso (Deixar só EFOMM e ESA se houver)
    print("Conectando ao Turso...")
    con_turso = pegar_conexao()
    
    if not isinstance(con_turso, TursoConnection):
        print("Erro: A conexão retornada não é do Turso! Verifique o .env")
        return
        
    print("Limpando bancos indesejados no Turso...")
    con_turso.execute("DELETE FROM questoes WHERE banca NOT IN ('EFOMM', 'ESA')")
    
    # Verifica o que tem no Turso no momento
    cur = con_turso.execute("SELECT banca, COUNT(*) FROM questoes GROUP BY banca")
    print("Atual estado do Turso:", cur.fetchall())
    
    # 2. Conectar ao SQLite Local para pegar as questões da EFOMM e ESA
    print("\nConectando ao SQLite Local...")
    con_local = sqlite3.connect("data/mathai.db")
    cur_local = con_local.cursor()
    
    # Extrai todas as questões do local
    cur_local.execute("SELECT banca, ano, materia, topico, enunciado, gabarito, subtopico FROM questoes")
    questoes_locais = cur_local.fetchall()
    print(f"Encontradas {len(questoes_locais)} questões no SQLite local.")
    
    # Como não sabemos o que já tem no Turso, é mais seguro apagar tudo e reenviar o espelho do local
    print("Limpando Turso para espelhamento exato...")
    con_turso.execute("DELETE FROM questoes;")
    
    print("Sincronizando questoes para o Turso...")
    for q in questoes_locais:
        banca, ano, materia, topico, enunciado, gabarito, subtopico = q
        
        # Como o Turso HTTP usa uma API diferente, é mais seguro rodar o INSERT direto aqui
        con_turso.execute("""
            INSERT INTO questoes (banca, ano, materia, topico, enunciado, gabarito, subtopico)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (banca, ano, materia, topico, enunciado, gabarito, subtopico))
        
    cur = con_turso.execute("SELECT banca, COUNT(*) FROM questoes GROUP BY banca")
    print("Novo estado do Turso:", cur.fetchall())
    print("Sincronização concluída com sucesso!")
    
if __name__ == "__main__":
    sync_to_turso()
