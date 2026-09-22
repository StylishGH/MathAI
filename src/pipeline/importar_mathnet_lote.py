"""
Script para importar um lote inicial de questões do MathNet (Hugging Face)
para o banco de dados do MathAI (SQLite) com tradução automática via Gemini.
"""

import sys
import os
from pathlib import Path

# Adiciona raiz do projeto ao path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db import pegar_conexao, inserir_questao
from src.ai.translator import traduzir_questao_matematica
from src.ai.client import tem_chave_configurada


def importar_lote_mathnet(qtd=5, apenas_com_figura=True):
    """
    Importa um pequeno lote de questões do dataset MathNet para testar.
    """
    if not tem_chave_configurada():
        print("\n❌ ATENÇÃO: Chave do Gemini não configurada!")
        print("Crie um arquivo .env na raiz do projeto com:")
        print("GEMINI_API_KEY=sua_chave_aqui")
        print("Ou defina a variável de ambiente GEMINI_API_KEY.\n")
        return

    try:
        from datasets import load_dataset
    except ImportError:
        print("❌ Biblioteca 'datasets' não encontrada. Instale com: pip install datasets")
        return

    print(f"📥 Carregando dataset MathNet da Hugging Face...")
    # Carrega split de treino
    ds = load_dataset("ShadenA/MathNet", split="train")

    con = pegar_conexao()
    cur = con.cursor()

    pasta_uploads = BASE_DIR / "data" / "uploads"
    pasta_uploads.mkdir(parents=True, exist_ok=True)

    inseridas = 0
    print(f"\n🔍 Buscando {qtd} questões para traduzir e inserir...\n")

    for i, row in enumerate(ds):
        if inseridas >= qtd:
            break

        tem_imagem = bool(row.get("images") and len(row["images"]) > 0)

        # Se pedimos apenas com figura e a questão não tem, pula
        if apenas_com_figura and not tem_imagem:
            continue

        enunciado_original = row.get("problem_markdown", "").strip()
        if not enunciado_original:
            continue

        # Verifica se já existe por enunciado original ou título
        cur.execute("SELECT id FROM questoes WHERE enunciado LIKE ?", (f"%{enunciado_original[:50]}%",))
        if cur.fetchone():
            print(f"⏩ Questão #{row.get('id', i)} já existente no banco. Pulando...")
            continue

        print(f"--- Processando Questão {inseridas + 1}/{qtd} ---")
        print(f"Origem: {row.get('competition', 'N/A')} | País: {row.get('country', 'N/A')}")
        print(f"Enunciado original: {enunciado_original[:80]}...")

        # 1. Salvar figura (se houver)
        caminho_figura_relativo = None
        if tem_imagem:
            nome_img = f"mathnet_{row.get('id', i)}.png"
            caminho_img_disco = pasta_uploads / nome_img
            row["images"][0].save(caminho_img_disco)
            caminho_figura_relativo = f"data/uploads/{nome_img}"
            print(f"🖼️ Figura salva em: {caminho_figura_relativo}")

        # 2. Traduzir e estruturar com Gemini
        print("🤖 Traduzindo via Gemini preservando LaTeX...")
        ano_val = row.get("year")
        ano_int = int(ano_val) if str(ano_val).isdigit() else None

        dados = traduzir_questao_matematica(
            enunciado_original=enunciado_original,
            gabarito_original=str(row.get("final_answer", "")),
            banca_original=str(row.get("competition", "Olimpíada")),
            ano_original=ano_int,
            categoria_sugerida=str(row.get("topics_flat", "Matemática"))
        )

        if not dados:
            print("⚠️ Falha na tradução da questão. Pulando...")
            continue

        # 3. Inserir no banco
        novo_id = inserir_questao(
            materia=dados.get("materia", "Matemática"),
            topico=dados.get("topico", "Geral"),
            subtopico=dados.get("subtopico"),
            dificuldade=dados.get("dificuldade", 3),
            banca=dados.get("banca", row.get("competition")),
            ano=dados.get("ano", ano_int),
            enunciado=dados.get("enunciado_pt", enunciado_original),
            gabarito=dados.get("gabarito", str(row.get("final_answer", ""))),
            estrategias_esperadas=dados.get("estrategias_esperadas", []),
            figura_path=caminho_figura_relativo
        )

        print(f"✅ Inserida no banco como ID #{novo_id} [{dados.get('materia')} - {dados.get('topico')}]\n")
        inseridas += 1

    con.close()
    print(f"🎉 Processo concluído! {inseridas} novas questões foram inseridas no MathAI.")


if __name__ == "__main__":
    # Importa 5 questões (priorizando as que têm imagens para testar o visualizador)
    importar_lote_mathnet(qtd=5, apenas_com_figura=True)
