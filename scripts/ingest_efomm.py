import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import json
import sqlite3
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()
# Usando o modelo gratuito que aguenta o tranco
MODEL_ID = "gemini-1.5-flash"

DB_PATH = Path("C:/Users/Guilherme/Documents/MathAI/data/mathai.db")

PROMPT_EXTRA_EFOMM = """
Você é um especialista em processamento de provas militares e formatação LaTeX.
Sua tarefa é analisar este(s) arquivo(s) PDF contendo a prova da EFOMM e/ou gabaritos.

Extraia TODAS as questões de MATEMÁTICA.
Regras:
1. Ignore questões de Inglês, Física, Português, etc. Apenas Matemática.
2. O texto deve ser formatado em Markdown. ATENÇÃO MÁXIMA AO LATEX: Todas as equações, frações, matrizes e símbolos matemáticos DEVEM obrigatoriamente estar envolvidos por $$ ... $$ (para blocos) ou $ ... $ (para linha).
3. Se um gabarito foi fornecido, identifique a alternativa correta e inclua em "gabarito" (letra A, B, C, D ou E). Se não tiver o gabarito no PDF, deixe nulo.
4. As "alternativas" devem ser um dicionário onde a chave é a letra (A, B, C, D, E) e o valor é o texto da alternativa.

Responda ESTRITAMENTE em formato JSON com o seguinte schema:
[
  {
    "enunciado": "Texto da questão em markdown...",
    "alternativas": {"A": "...", "B": "...", "C": "...", "D": "...", "E": "..."},
    "gabarito": "A",
    "materia": "Matemática",
    "topico": "Tópico mais provável (ex: Geometria Analítica, Matrizes, Cálculo...)",
    "banca": "EFOMM",
    "ano": 2024
  }
]
Se não encontrar questões de matemática, retorne um array vazio [].
"""

def processar_pdfs(pdfs_paths):
    print(f"\nFazendo upload de {len(pdfs_paths)} arquivo(s) para o Gemini...")
    uploaded_files = []
    for pdf_path in pdfs_paths:
        print(f"   Upload: {os.path.basename(pdf_path)}...")
        uploaded = client.files.upload(file=pdf_path)
        uploaded_files.append(uploaded)
        # Pausa para não estourar os limites gratuitos de upload
        time.sleep(5)
    
    print("\nAnalisando e extraindo questoes (isso pode demorar um pouco)...")
    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[*uploaded_files, PROMPT_EXTRA_EFOMM],
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type="application/json"
            )
        )
        questoes = json.loads(response.text)
        print(f"Sucesso! {len(questoes)} questoes extraidas.")
        return questoes
    except Exception as e:
        print(f"Erro durante a geracao: {e}")
        return []
    finally:
        for uf in uploaded_files:
            client.files.delete(name=uf.name)

def salvar_no_banco(questoes):
    if not questoes:
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    inseridas = 0
    
    for q in questoes:
        alts_json = json.dumps(q.get("alternativas", {}), ensure_ascii=False)
        gabarito = q.get("gabarito")
        try:
            cursor.execute("""
                INSERT INTO questoes (banca, ano, materia, topico, enunciado, alternativas, gabarito)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                q.get("banca", "EFOMM"),
                q.get("ano", 2024),
                q.get("materia", "Matemática"),
                q.get("topico", "Geral"),
                q.get("enunciado", ""),
                alts_json,
                gabarito
            ))
            inseridas += 1
        except Exception as e:
            pass
            
    conn.commit()
    conn.close()
    print(f"{inseridas} questoes salvas no banco!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("pdfs", nargs='+', help="PDFs")
    args = parser.parse_args()
    
    extraidas = processar_pdfs(args.pdfs)
    salvar_no_banco(extraidas)
