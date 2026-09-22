"""
MathAI - Utilitário para Visualizar Usuários Cadastrados
Execute no terminal: python ver_usuarios.py
"""

import io
import sys
import sqlite3
from pathlib import Path

# Garante compatibilidade UTF-8 no Windows PowerShell / CMD
if isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.database.db import pegar_conexao, _obter_credenciais_turso

def listar():
    url, _ = _obter_credenciais_turso()
    origem = "Turso (Nuvem)" if url else "SQLite (Local)"

    con = pegar_conexao()
    cur = con.cursor()

    cur.execute("""
        SELECT id, nome, email, celular, cpf, cidade, estado, escolaridade, faculdade, curso, verificado, criado_em
        FROM usuarios
        ORDER BY id ASC
    """)
    usuarios = cur.fetchall()
    con.close()

    if not usuarios:
        print("[i] Nenhum usuario cadastrado no momento.")
        return

    print("\n" + "=" * 118)
    print(f"  MATHAI - USUARIOS CADASTRADOS (TOTAL: {len(usuarios)})  [Banco: {origem}]")
    print("=" * 118)
    print(f"{'ID':<4} | {'NOME':<25} | {'E-MAIL':<28} | {'CELULAR':<15} | {'CIDADE/UF':<12} | {'CRIADO EM':<16} | {'2FA'}")
    print("-" * 118)

    for u in usuarios:
        cid_uf = f"{u['cidade'] or '-'}/{u['estado'] or '-'}"
        if len(cid_uf) > 12:
            cid_uf = cid_uf[:10] + ".."
        status_2fa = "Ativo" if u["verificado"] == 1 else "Pendente"
        nome = (u["nome"] or "-")[:24]
        email = (u["email"] or "-")[:27]
        cel = (u["celular"] or "-")[:14]
        criado = (u["criado_em"] or "-")[:16]

        print(f"#{u['id']:<3} | {nome:<25} | {email:<28} | {cel:<15} | {cid_uf:<12} | {criado:<16} | {status_2fa}")

    print("=" * 118 + "\n")

if __name__ == "__main__":
    listar()
