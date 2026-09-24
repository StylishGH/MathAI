import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import os
import glob
import time
import json
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
client = genai.Client()
MODEL_ID = "gemini-3.5-flash-lite"

PROMPT_NOTION = """
Você é um professor de matemática e geometria especialista no material do CEDERJ.
A sua tarefa é encontrar exercícios/questões e extraí-los.
ATENÇÃO: O usuário quer testar especificamente disciplinas como Construções Geométricas, Lógica e Teoria dos Conjuntos, Cálculo e Álgebra Linear.
Portanto, EXTRAIA QUALQUER EXERCÍCIO que encontrar, mesmo que seja discursivo, passo a passo (ex: trace uma reta, use o compasso) ou demonstrações lógicas.

Regras:
1. ATENÇÃO MÁXIMA AO LATEX: Todas as equações e símbolos matemáticos DEVEM obrigatoriamente estar envolvidos por $$ ... $$ (para blocos) ou $ ... $ (para linha). Converta qualquer notação estranha para LaTeX. Se usar chaves no latex, escape-as.
2. Deduza a matéria exata pelo nome do arquivo ou contexto (ex: "Construções Geométricas", "Lógica e Teoria dos Conjuntos", "Cálculo 2").
3. Responda ESTRITAMENTE num array JSON com este formato:
[
  {
    "enunciado": "Texto da questão...",
    "alternativas": {"A": "...", "B": "..."}, // Se houver, se for discursiva deixe vazio
    "gabarito": "Letra correta OU resolução passo a passo/resposta final",
    "materia": "Construções Geométricas",
    "topico": "Geral",
    "banca": "CEDERJ",
    "ano": 2024
  }
]
Se não encontrar questões, retorne [].
"""

def salvar_no_banco(questoes):
    if not questoes:
        return
        
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.database.db import pegar_conexao
    
    con = pegar_conexao()
    inseridas = 0
    
    for q in questoes:
        enunciado = q.get("enunciado", "")
        
        # Concatena as alternativas no final do enunciado, se existirem
        alts = q.get("alternativas", {})
        if isinstance(alts, dict) and alts:
            alt_lines = []
            for k, v in alts.items():
                letra = k[-1].upper()
                if letra in ['1','2','3','4','5']: # Trata casos de (1), (2)
                    letra = chr(ord('A') + int(letra) - 1)
                alt_lines.append(f"({letra}) {v}")
            if alt_lines:
                enunciado += "\n\n" + "\n".join(alt_lines)
                
        gabarito = str(q.get("gabarito", ""))
        
        try:
            con.execute("""
                INSERT INTO questoes (banca, ano, materia, topico, enunciado, gabarito)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                q.get("banca", "CEDERJ"),
                q.get("ano", 2024),
                q.get("materia", "Matemática"),
                q.get("topico", "Geral"),
                enunciado,
                gabarito
            ))
            inseridas += 1
        except Exception as e:
            print(f"Erro ao inserir questao: {e}")
            
    con.commit()
    print(f"{inseridas} questoes alvo salvas diretamente no Turso!")


def processar_arquivos(md_files):
    chunks = []
    current_chunk = ""
    for f in md_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                texto = file.read()
                if len(texto) < 50: continue
                current_chunk += f"\n\n--- ARQUIVO: {f} ---\n\n" + texto
                if len(current_chunk) > 15000:  # Reduzi o chunk pra IA ler com mais calma
                    chunks.append(current_chunk)
                    current_chunk = ""
        except Exception:
            pass
    if current_chunk:
        chunks.append(current_chunk)

    print(f"Total de blocos gerados para os alvos: {len(chunks)}")
    total_extraidas = 0

    for idx, chunk in enumerate(chunks):
        print(f"Enviando bloco {idx+1}/{len(chunks)}...")
        try:
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[PROMPT_NOTION, chunk],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json"
                )
            )
            text_json = response.text.replace('\\\\', '\\\\\\\\')
            questoes = json.loads(text_json, strict=False)
            print(f"{len(questoes)} questoes extraidas deste bloco.")
            salvar_no_banco(questoes)
            total_extraidas += len(questoes)
        except Exception as e:
            print(f"Erro no bloco {idx+1}: {e}")
        
        if idx < len(chunks) - 1:
            time.sleep(5)

    print(f"\nIngestão Alvo concluida! Total salvas: {total_extraidas}")

if __name__ == "__main__":
    notion_dir = r"D:\Downloads\Notion"
    all_files = glob.glob(os.path.join(notion_dir, "**", "*.md"), recursive=True)
    
    # Filtra apenas os arquivos que pertencem as pastas ou conteudos alvos
    alvos = [
        'lgebra linear i', 'lgebra linear 1',
        'c\u00e1lculo i', 'c\u00e1lculo 1', 'c\u00e1lculo ii', 'c\u00e1lculo 2', 'c\u00e1lculo iii', 'c\u00e1lculo 3',
        'geometria plana',
        'geometria espacial',
        'constru\u00e7\u00f5es geom\u00e9tricas',
        'l\u00f3gica e teoria dos conjuntos',
        'geometria anal\u00edtica'
    ]
    
    import unicodedata
    def normalize(text):
        return unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8').lower()
    
    alvos_norm = [normalize(a) for a in alvos]
    
    filtered_files = []
    for f in all_files:
        f_norm = normalize(f)
        for a in alvos_norm:
            if a in f_norm:
                filtered_files.append(f)
                break
                
    print(f"Encontrados {len(filtered_files)} arquivos correspondentes aos alvos solicitados.")
    processar_arquivos(filtered_files)
