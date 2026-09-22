"""
Script de Ingestão e Tradução Paralela para o MathAI.
Processa questões do MathNet em duas vias concorrentes:
  1. Worker Texto: Tradução acelerada de questões puramente textuais com Gemini 3.8 Flash.
  2. Worker Multimodal: Extração de figuras, upload em disco e tradução visual com Gemini 3.8 Flash.
"""

import io
import sys
import argparse
import threading
from pathlib import Path

# Suporte pleno a UTF-8 e emojis no terminal Windows
if sys.platform == "win32":
    try:
        if isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import pandas as pd
from tqdm import tqdm

# Garante que a raiz do projeto esteja no PATH
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(BASE_DIR))

from src.database.db import pegar_conexao, inserir_questao
from src.ai.translator import traduzir_questao_matematica
from src.ai.client import tem_chave_configurada

DATA_DIR = BASE_DIR / "data"
UPLOADS_DIR = DATA_DIR / "uploads"
PATH_SEM_IMAGEM = DATA_DIR / "mathnet_sem_imagem.parquet"
PATH_COM_IMAGEM = DATA_DIR / "mathnet_com_imagem.parquet"

# Lock para gravação atômica concorrente no SQLite
db_lock = threading.Lock()


def inicializar_ambiente_db():
    """Ativa modo WAL e timeout estendido no SQLite para alta concorrência."""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    con = pegar_conexao()
    con.execute("PRAGMA journal_mode = WAL;")
    con.execute("PRAGMA busy_timeout = 30000;")
    con.commit()
    con.close()


def carregar_mathnet_ids_processados() -> set[str]:
    """Retorna todos os IDs do MathNet que já foram importados com sucesso para o banco."""
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS mathnet_ingestao (
            mathnet_id TEXT PRIMARY KEY,
            questao_id INTEGER,
            tipo_ingestao TEXT,
            data_importacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("SELECT mathnet_id FROM mathnet_ingestao")
    processados = set(str(r[0]) for r in cur.fetchall() if r[0])

    try:
        cur.execute("SELECT mathnet_id FROM questoes WHERE mathnet_id IS NOT NULL")
        for r in cur.fetchall():
            if r[0]:
                processados.add(str(r[0]))
    except Exception:
        pass

    con.close()
    return processados


def carregar_enunciados_existentes() -> set[str]:
    """Carrega os primeiros 60 caracteres de enunciados já no banco para deduplicação secundária."""
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT enunciado FROM questoes")
    existentes = set()
    for row in cur.fetchall():
        txt = (row["enunciado"] or "").strip().lower()
        if len(txt) >= 30:
            existentes.add(txt[:50])
    con.close()
    return existentes


def limpar_campo_texto(valor, padrao: str = "") -> str:
    """Extrai texto seguro mesmo se for lista, numpy array, None ou NaN."""
    if valor is None:
        return padrao
    import numpy as np
    if isinstance(valor, (list, tuple, np.ndarray)):
        return ", ".join(str(x) for x in valor[:2]) if len(valor) > 0 else padrao
    try:
        if pd.isna(valor):
            return padrao
    except Exception:
        pass
    val_str = str(valor).strip()
    return padrao if val_str.lower() in ("nan", "none", "null") else val_str


def limpar_ano(valor) -> int | None:
    """Extrai ano numérico de forma segura."""
    if pd.isna(valor):
        return None
    val_str = str(valor).strip()
    if val_str.isdigit():
        return int(val_str)
    import re
    match = re.search(r"\b(19\d{2}|20\d{2})\b", val_str)
    return int(match.group(1)) if match else None


def extrair_item_imagem(item) -> tuple[bytes | None, str, str]:
    """Extrai bytes e formato de um item de imagem (dict ou PIL Image)."""
    if not item:
        return None, "image/png", "png"
    raw_bytes = None
    if isinstance(item, dict) and "bytes" in item:
        raw_bytes = item["bytes"]
    elif hasattr(item, "save"):
        buf = io.BytesIO()
        item.save(buf, format="PNG")
        raw_bytes = buf.getvalue()
    if not raw_bytes:
        return None, "image/png", "png"
    if raw_bytes.startswith(b"\xff\xd8"):
        return raw_bytes, "image/jpeg", "jpg"
    return raw_bytes, "image/png", "png"


def extrair_e_salvar_imagens_questao(images_field, enunciado: str, qid: str) -> tuple[bytes | None, str, str, str | None]:
    """
    Extrai e salva em disco todas as imagens pertencentes ao enunciado da questão.
    Retorna (primeira_img_bytes, mime_type, ext, caminhos_relativos_str).
    """
    if images_field is None or len(images_field) == 0:
        return None, "image/png", "png", None

    import re
    # Detecta quais imagens são mencionadas no enunciado (ex: attached_image_1.png, attached_image_2.png)
    indices_enunciado = []
    matches = re.findall(r'attached_image_(\d+)\.png', enunciado or "")
    if matches:
        for m in matches:
            idx = int(m) - 1
            if 0 <= idx < len(images_field) and idx not in indices_enunciado:
                indices_enunciado.append(idx)

    if not indices_enunciado:
        indices_enunciado = [0]

    caminhos_salvos = []
    primeiro_bytes, primeiro_mime, primeiro_ext = None, "image/png", "png"

    for num_ordem, idx in enumerate(indices_enunciado, start=1):
        raw_b, mime, ext = extrair_item_imagem(images_field[idx])
        if not raw_b:
            continue
        if primeiro_bytes is None:
            primeiro_bytes, primeiro_mime, primeiro_ext = raw_b, mime, ext

        sufixo = f"_{num_ordem}" if len(indices_enunciado) > 1 else ""
        nome_arq = f"mathnet_{qid}{sufixo}.{ext}"
        caminho_disco = UPLOADS_DIR / nome_arq
        caminho_disco.write_bytes(raw_b)
        caminhos_salvos.append(f"data/uploads/{nome_arq}")

    caminho_final = ",".join(caminhos_salvos) if caminhos_salvos else None
    return primeiro_bytes, primeiro_mime, primeiro_ext, caminho_final



# ==============================================================================
# WORKER 1: Questões de Texto Puro (Sem Imagem)
# ==============================================================================
def processar_lote_texto(df_amostra: pd.DataFrame, enunciados_existentes: set[str], stats: dict):
    for _, row in tqdm(df_amostra.iterrows(), total=len(df_amostra), desc="📄 Worker Texto", position=0):
        try:
            enunciado_orig = str(row.get("enunciado", "")).strip()
            if not enunciado_orig:
                continue

            # Deduplicação ultrarrápida em memória
            chave_dedup = enunciado_orig[:50].lower()
            if chave_dedup in enunciados_existentes:
                stats["texto_duplicadas"] += 1
                continue

            ano_int = limpar_ano(row.get("ano"))
            gabarito_limpo = limpar_campo_texto(row.get("gabarito"), padrao="")
            banca_limpa = limpar_campo_texto(row.get("banca")) or limpar_campo_texto(row.get("competition"), padrao="Internacional")
            topico_sug = limpar_campo_texto(row.get("topico"), padrao="Geral")

            # Tradução e categorização via Gemini
            dados = traduzir_questao_matematica(
                enunciado_original=enunciado_orig,
                gabarito_original=gabarito_limpo,
                banca_original=banca_limpa,
                ano_original=ano_int,
                categoria_sugerida=topico_sug,
                imagem_bytes=None
            )

            if not dados:
                stats["texto_erros"] += 1
                continue

            enunciado_pt = dados.get("enunciado_pt", enunciado_orig)
            import re
            enunciado_pt = re.sub(r'!\[.*?\]\(.*?\)', '', enunciado_pt).strip()

            # Inserção atômica com lock no SQLite
            with db_lock:
                inserir_questao(
                    materia=dados.get("materia", "Matemática"),
                    topico=dados.get("topico", "Geral"),
                    subtopico=dados.get("subtopico"),
                    dificuldade=dados.get("dificuldade", 3),
                    banca=dados.get("banca", banca_limpa),
                    ano=dados.get("ano", ano_int),
                    enunciado=enunciado_pt,
                    gabarito=dados.get("gabarito", gabarito_limpo),
                    estrategias_esperadas=dados.get("estrategias_esperadas", []),
                    figura_path=None,
                    tipo=row.get("tipo", "discursiva"),
                    mathnet_id=row.get("id")
                )
                enunciados_existentes.add(chave_dedup)
                enunciados_existentes.add(enunciado_pt[:50].lower())
                stats["texto_sucesso"] += 1

        except Exception as e:
            stats["texto_erros"] += 1
            print(f"\n❌ [Texto] Erro no ID {row.get('id')}: {e}")


# ==============================================================================
# WORKER 2: Questões com Figura / Diagrama (Multimodal)
# ==============================================================================
def processar_lote_imagem(df_amostra: pd.DataFrame, enunciados_existentes: set[str], stats: dict):
    for _, row in tqdm(df_amostra.iterrows(), total=len(df_amostra), desc="🖼️ Worker Imagem", position=1):
        try:
            enunciado_orig = str(row.get("enunciado", "")).strip()
            if not enunciado_orig:
                continue

            # Deduplicação ultrarrápida em memória
            chave_dedup = enunciado_orig[:50].lower()
            if chave_dedup in enunciados_existentes:
                stats["img_duplicadas"] += 1
                continue

            # 1. Extração e gravação da(s) imagem(ns) física(s) em disco
            qid = str(row.get("id") or "tmp")
            raw_bytes, mime_type, ext, caminho_figura_relativo = extrair_e_salvar_imagens_questao(
                row.get("images"), enunciado_orig, qid
            )

            ano_int = limpar_ano(row.get("ano"))
            gabarito_limpo = limpar_campo_texto(row.get("gabarito"), padrao="")
            banca_limpa = limpar_campo_texto(row.get("banca")) or limpar_campo_texto(row.get("competition"), padrao="Internacional")
            topico_sug = limpar_campo_texto(row.get("topico"), padrao="Geometria")

            # 2. Tradução multimodal (Gemini recebe enunciado + imagem)
            dados = traduzir_questao_matematica(
                enunciado_original=enunciado_orig,
                gabarito_original=gabarito_limpo,
                banca_original=banca_limpa,
                ano_original=ano_int,
                categoria_sugerida=topico_sug,
                imagem_bytes=raw_bytes,
                mime_type=mime_type
            )

            if not dados:
                stats["img_erros"] += 1
                continue

            import re
            enunciado_pt = dados.get("enunciado_pt", enunciado_orig)
            enunciado_pt = re.sub(r'!\[.*?\]\(.*?\)', '', enunciado_pt).strip()


            # Inserção atômica com lock no SQLite
            with db_lock:
                inserir_questao(
                    materia=dados.get("materia", "Geometria"),
                    topico=dados.get("topico", "Geral"),
                    subtopico=dados.get("subtopico"),
                    dificuldade=dados.get("dificuldade", 3),
                    banca=dados.get("banca", banca_limpa),
                    ano=dados.get("ano", ano_int),
                    enunciado=enunciado_pt,
                    gabarito=dados.get("gabarito", gabarito_limpo),
                    estrategias_esperadas=dados.get("estrategias_esperadas", []),
                    figura_path=caminho_figura_relativo,
                    tipo=row.get("tipo", "discursiva"),
                    mathnet_id=row.get("id")
                )
                enunciados_existentes.add(chave_dedup)
                enunciados_existentes.add(enunciado_pt[:50].lower())
                stats["img_sucesso"] += 1

        except Exception as e:
            stats["img_erros"] += 1
            print(f"\n❌ [Imagem] Erro no ID {row.get('id')}: {e}")


# ==============================================================================
# ORQUESTRADOR PRINCIPAL
# ==============================================================================
def iniciar_ingestao_paralela(
    limite_texto: int = 20,
    limite_imagem: int = 20,
    apenas_texto: bool = False,
    apenas_imagem: bool = False
):
    """Dispara os dois pipelines simultâneos garantindo que questões já inseridas nunca sejam repetidas."""
    if not tem_chave_configurada():
        print("❌ Chave de API do Gemini não configurada! Verifique seu arquivo .env.")
        return

    inicializar_ambiente_db()
    ids_mathnet_processados = carregar_mathnet_ids_processados()
    enunciados_existentes = carregar_enunciados_existentes()

    print("=" * 70)
    print("🚀 MATHAI — INGESTÃO PARALELA MULTIMODAL (RESUMÍVEL)")
    print("=" * 70)
    print(f"📦 Questões do MathNet já importadas no SQLite: {len(ids_mathnet_processados)}")

    stats = {
        "texto_sucesso": 0, "texto_duplicadas": 0, "texto_erros": 0,
        "img_sucesso": 0, "img_duplicadas": 0, "img_erros": 0
    }

    threads = []

    # Carrega base de texto se solicitado
    if not apenas_imagem and PATH_SEM_IMAGEM.exists() and limite_texto > 0:
        print(f"📂 Carregando base de texto: {PATH_SEM_IMAGEM.name}...")
        df_sem = pd.read_parquet(PATH_SEM_IMAGEM)
        df_sem_pendentes = df_sem[~df_sem['id'].astype(str).isin(ids_mathnet_processados)]
        df_amostra_texto = df_sem_pendentes.head(limite_texto)
        print(f"📄 Questões pendentes de texto: {len(df_sem_pendentes):,} (separadas as próximas {len(df_amostra_texto)})")

        if len(df_amostra_texto) > 0:
            t_texto = threading.Thread(
                target=processar_lote_texto,
                args=(df_amostra_texto, enunciados_existentes, stats),
                name="Worker-Texto"
            )
            threads.append(t_texto)
    elif not apenas_imagem and not PATH_SEM_IMAGEM.exists():
        print(f"⚠️ Arquivo {PATH_SEM_IMAGEM} não encontrado!")

    # Carrega base de imagem se solicitado
    if not apenas_texto and PATH_COM_IMAGEM.exists() and limite_imagem > 0:
        print(f"📂 Carregando base multimodal: {PATH_COM_IMAGEM.name}...")
        df_com = pd.read_parquet(PATH_COM_IMAGEM)
        df_com_pendentes = df_com[~df_com['id'].astype(str).isin(ids_mathnet_processados)]
        df_amostra_img = df_com_pendentes.head(limite_imagem)
        print(f"🖼️ Questões pendentes com imagem: {len(df_com_pendentes):,} (separadas as próximas {len(df_amostra_img)})")

        if len(df_amostra_img) > 0:
            t_img = threading.Thread(
                target=processar_lote_imagem,
                args=(df_amostra_img, enunciados_existentes, stats),
                name="Worker-Imagem"
            )
            threads.append(t_img)
    elif not apenas_texto and not PATH_COM_IMAGEM.exists():
        print(f"⚠️ Arquivo {PATH_COM_IMAGEM} não encontrado!")

    if not threads:
        print("Nenhum worker configurado para execução.")
        return

    print("\n⚡ Iniciando processamento concorrente dos Geminis...\n")
    for t in threads:
        t.start()

    for t in threads:
        t.join()

    print("\n" + "=" * 70)
    print("🏁 INGESTÃO FINALIZADA!")
    print("=" * 70)
    print(f"📄 Worker Texto:  {stats['texto_sucesso']} inseridas | {stats['texto_duplicadas']} duplicadas | {stats['texto_erros']} erros")
    print(f"🖼️ Worker Imagem: {stats['img_sucesso']} inseridas | {stats['img_duplicadas']} duplicadas | {stats['img_erros']} erros")
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingestão paralela de questões no MathAI.")
    parser.add_argument("--limite-texto", type=int, default=20, help="Quantidade de questões sem imagem a processar (padrão: 20)")
    parser.add_argument("--limite-imagem", type=int, default=20, help="Quantidade de questões com imagem a processar (padrão: 20)")
    parser.add_argument("--todas", action="store_true", help="Processar todo o acervo sem limites")
    parser.add_argument("--apenas-texto", action="store_true", help="Executar apenas o worker de texto")
    parser.add_argument("--apenas-imagem", action="store_true", help="Executar apenas o worker com imagem")

    args = parser.parse_args()

    lim_txt = 999999 if args.todas else args.limite_texto
    lim_img = 999999 if args.todas else args.limite_imagem

    iniciar_ingestao_paralela(
        limite_texto=lim_txt,
        limite_imagem=lim_img,
        apenas_texto=args.apenas_texto,
        apenas_imagem=args.apenas_imagem
    )
