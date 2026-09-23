import os
import sys
from pathlib import Path
import json

# Adiciona raiz ao path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.database.db import pegar_conexao
from src.ai.client import criar_cliente_gemini

def limpar_mathml():
    conn = pegar_conexao()
    questoes = conn.execute("SELECT id, enunciado FROM questoes WHERE enunciado LIKE '%<math%'").fetchall()
    
    if not questoes:
        print("Nenhuma questão com MathML encontrada.")
        return

    print(f"Encontradas {len(questoes)} questões com MathML.")
    client = criar_cliente_gemini()
    if not client:
        print("Erro: Chave do Gemini não configurada.")
        return

    from google.genai import types

    prompt = """Você é um assistente de limpeza de dados matemáticos.
Sua tarefa é ler um texto que contém marcações MathML (tags <math xmlns="http://www.w3.org/1998/Math/MathML">...</math>) e substituir TODO o conteúdo dessas tags pelas respectivas expressões equivalentes em LaTeX puro cercado por cifrões duplos ($$...$$ ou single $...$ dependendo de como preferir, use apenas o formato MathJax/KaTeX que o markdown entenda).
Importante:
1. MANTENHA TODO o resto do texto absolutamente idêntico. Não resuma, não mude as palavras.
2. Não adicione textos extras, blocos markdown, ou explicações. Apenas retorne o texto corrigido.
3. Garanta que todas as opções de resposta (A, B, C, D, E) sejam preservadas e o LaTeX esteja correto.
"""

    for q in questoes:
        q_id = q["id"]
        enunciado = q["enunciado"]
        
        print(f"Processando questão {q_id}...")
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=enunciado,
                config=types.GenerateContentConfig(
                    system_instruction=prompt,
                    temperature=0.0
                )
            )
            novo_enunciado = response.text.strip()
            
            # Atualiza o banco
            conn.execute("UPDATE questoes SET enunciado = ? WHERE id = ?", (novo_enunciado, q_id))
            conn.commit()
            print(f"Questão {q_id} atualizada com sucesso.")
            
        except Exception as e:
            print(f"Erro na questão {q_id}: {e}")

    print("Limpeza concluída.")

if __name__ == "__main__":
    limpar_mathml()
