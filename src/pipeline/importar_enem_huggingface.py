"""
Pipeline de Importação Automática de Questões do ENEM via Hugging Face.
Puxa questões estruturadas do ENEM (2009 a 2024), baixa figuras para data/uploads/
e insere no banco de dados do MathAI (Turso / SQLite).
"""

import io
import os
import sys
import urllib.request
from pathlib import Path
from typing import Optional

# UTF-8 no terminal Windows
if sys.platform == "win32":
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if isinstance(sys.stderr, io.TextIOWrapper):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Raiz do projeto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db import pegar_conexao
from datasets import load_dataset


def importar_enem_2024(con=None) -> int:
    """Importa as 45 questões de Matemática do ENEM 2024 com figuras."""
    print("\n📦 Carregando ENEM 2024 do dataset 'maritaca-ai/enem'...")
    ds = load_dataset("maritaca-ai/enem")
    
    pasta_uploads = BASE_DIR / "data" / "uploads"
    pasta_uploads.mkdir(parents=True, exist_ok=True)

    fechar_con = False
    if con is None:
        con = pegar_conexao()
        fechar_con = True

    cur = con.cursor()
    inseridas = 0

    math_qs = [q for q in ds["train"] if int(q["id"].split("_")[1]) >= 136]
    print(f"🔍 Encontradas {len(math_qs)} questões de Matemática no ENEM 2024.")

    for q in math_qs:
        num = q["id"].split("_")[1]
        enunciado = q.get("question", "").strip()
        alternativas = q.get("alternatives", [])
        gabarito = str(q.get("label", "")).strip().upper()
        figures = q.get("figures", [])

        # Formata alternativas (A), (B), etc.
        texto_completo = enunciado
        letras = ["A", "B", "C", "D", "E"]
        if alternativas and len(alternativas) >= 2:
            texto_completo += "\n\n"
            for i, alt in enumerate(alternativas[:5]):
                texto_completo += f"({letras[i]}) {alt}\n"

        # Verifica duplicata
        cur.execute("SELECT id FROM questoes WHERE banca = 'ENEM' AND ano = 2024 AND enunciado LIKE ? LIMIT 1", (f"%{enunciado[:80]}%",))
        if cur.fetchone():
            continue

        # Baixa figura se existir
        figura_path: Optional[str] = None
        if figures:
            fig_url = figures[0]
            nome_arq = f"enem_2024_q{num}.png"
            caminho_local = pasta_uploads / nome_arq
            try:
                if not caminho_local.exists():
                    urllib.request.urlretrieve(fig_url, caminho_local)
                figura_path = f"data/uploads/{nome_arq}"
            except Exception as e:
                print(f"⚠️ Não foi possível baixar a figura de q{num}: {e}")

        try:
            cur.execute("""
                INSERT INTO questoes (
                    materia, topico, enunciado, gabarito, dificuldade,
                    banca, ano, figura_path, tipo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Matemática", "ENEM", texto_completo, gabarito, 3,
                "ENEM", 2024, figura_path, "objetiva"
            ))
            inseridas += 1
        except Exception as e:
            print(f"Erro ao inserir q{num}: {e}")

    con.commit()
    print(f"✅ ENEM 2024: {inseridas} questões novas inseridas com sucesso!")
    if fechar_con:
        con.close()
    return inseridas


def importar_enem_historico(con=None, max_questoes: int = 300) -> int:
    """Importa questões de Matemática do ENEM (2009 a 2023) do 'nicholasKluge/enem_challenge'."""
    print("\n📦 Carregando histórico do ENEM (2009 a 2023) do 'nicholasKluge/enem_challenge'...")
    ds = load_dataset("nicholasKluge/enem_challenge")

    fechar_con = False
    if con is None:
        con = pegar_conexao()
        fechar_con = True

    cur = con.cursor()
    inseridas = 0

    math_qs = [
        q for q in ds["train"]
        if q.get("question_number") is not None
        and q["question_number"] >= 136
        and not q.get("nullified", False)
    ]
    print(f"🔍 Encontradas {len(math_qs)} questões de Matemática no histórico.")

    for q in math_qs:
        if inseridas >= max_questoes:
            break

        ano_str = str(q.get("exam_year", "")).strip()
        ano = int(ano_str) if ano_str.isdigit() else 2023
        num = q.get("question_number", 0)
        enunciado = str(q.get("question", "")).strip()
        choices = q.get("choices", {})
        gabarito = str(q.get("answerKey", "")).strip().upper()

        textos_alt = choices.get("text", [])
        labels_alt = choices.get("label", [])

        texto_completo = enunciado
        if textos_alt and labels_alt:
            texto_completo += "\n\n"
            for lbl, txt in zip(labels_alt, textos_alt):
                texto_completo += f"({lbl}) {txt.strip()}\n"

        # Verifica duplicata
        cur.execute("SELECT id FROM questoes WHERE banca = 'ENEM' AND ano = ? AND enunciado LIKE ? LIMIT 1", (ano, f"%{enunciado[:80]}%",))
        if cur.fetchone():
            continue

        try:
            cur.execute("""
                INSERT INTO questoes (
                    materia, topico, enunciado, gabarito, dificuldade,
                    banca, ano, figura_path, tipo
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Matemática", "ENEM", texto_completo, gabarito, 3,
                "ENEM", ano, None, "objetiva"
            ))
            inseridas += 1
        except Exception as e:
            print(f"Erro ao inserir questão {ano} #{num}: {e}")

    con.commit()
    print(f"✅ Histórico ENEM: {inseridas} questões novas inseridas com sucesso!")
    if fechar_con:
        con.close()
    return inseridas


def rodar_importacao_completa():
    print("=" * 70)
    print("🚀 MATHAI - IMPORTAÇÃO DE QUESTÕES DO ENEM EM LOTE")
    print("=" * 70)
    con = pegar_conexao()
    total_2024 = importar_enem_2024(con)
    total_hist = importar_enem_historico(con, max_questoes=300)
    con.close()
    print("\n" + "=" * 70)
    print(f"🎉 FINALIZADO! Total de {total_2024 + total_hist} novas questões inseridas no banco!")
    print("=" * 70)


if __name__ == "__main__":
    rodar_importacao_completa()
