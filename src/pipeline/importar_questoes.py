"""
Script de Ingestão e Tradução de Questões para o MathAI.
Lê dados brutos (ex: MathNet ou JSON), traduz com o Gemini preservando LaTeX,
evita duplicatas e insere no banco SQLite.
"""

import sys
from pathlib import Path

# Adiciona a raiz do projeto ao PATH
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db import pegar_conexao, inserir_questao
from src.ai.translator import traduzir_questao_matematica, gerar_hash_texto


def questao_ja_existe(con, hash_original: str, enunciado: str) -> bool:
    """Verifica no banco se a questão já foi inserida para evitar repetições."""
    cur = con.cursor()
    # Verifica por similaridade de enunciado
    cur.execute("SELECT id FROM questoes WHERE enunciado = ?", (enunciado,))
    if cur.fetchone():
        return True
    return False


def processar_e_inserir_questao(
    enunciado_original: str,
    gabarito_original: str = "",
    banca: str = "MathNet / MIT",
    ano: int = 2020,
    categoria: str = "Geometria"
):
    """
    Traduz uma questão de inglês para português via Gemini e insere no banco SQLite.
    """
    con = pegar_conexao()

    # 1. Tradução inteligente com Gemini
    print(f"🤖 Traduzindo questão via Gemini: {enunciado_original[:60]}...")
    dados_traduzidos = traduzir_questao_matematica(
        enunciado_original=enunciado_original,
        gabarito_original=gabarito_original,
        banca_original=banca,
        ano_original=ano,
        categoria_sugerida=categoria
    )

    if not dados_traduzidos:
        print("❌ Falha na tradução da questão.")
        con.close()
        return None

    enunciado_pt = dados_traduzidos.get("enunciado_pt")
    hash_orig = dados_traduzidos.get("hash_original")

    # 2. Verifica se já existe para não duplicar
    if questao_ja_existe(con, hash_orig, enunciado_pt):
        print("⚠️ Questão já cadastrada no banco! Pulando para evitar duplicata.")
        con.close()
        return None

    # 3. Insere no banco de dados SQLite
    novo_id = inserir_questao(
        materia=dados_traduzidos.get("materia", "Matemática"),
        topico=dados_traduzidos.get("topico", "Geral"),
        subtopico=dados_traduzidos.get("subtopico"),
        dificuldade=dados_traduzidos.get("dificuldade", 3),
        banca=dados_traduzidos.get("banca", banca),
        ano=dados_traduzidos.get("ano", ano),
        enunciado=enunciado_pt,
        gabarito=dados_traduzidos.get("gabarito", gabarito_original),
        estrategias_esperadas=dados_traduzidos.get("estrategias_esperadas", [])
    )

    con.close()
    print(f"✅ Questão #{novo_id} inserida com sucesso! [{dados_traduzidos.get('materia')} - {dados_traduzidos.get('topico')}]")
    return novo_id


if __name__ == "__main__":
    # Exemplo de teste com um problema clássico de olimpíada em inglês com LaTeX
    exemplo_problema_ingles = r"""
    Let $ABC$ be an acute triangle with circumcenter $O$. Let $D$ be the midpoint of $BC$.
    If $AD \perp BO$ and $\angle BAC = 60^\circ$, find the measure of $\angle ABC$ in degrees.
    """

    print("🚀 Testando pipeline de ingestão...")
    processar_e_inserir_questao(
        enunciado_original=exemplo_problema_ingles,
        gabarito_original="75",
        banca="Berkeley Math Circle",
        ano=2018,
        categoria="Geometria Plana"
    )
