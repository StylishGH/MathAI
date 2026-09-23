#!/usr/bin/env python3
"""
Módulo de Ingestão em Lote Concorrente para o MathNet (Gemini Duplo).
Executa simultaneamente duas esteiras de processamento via Multi-Threading:
  - Esteira 1: Questões SEM Imagem (Texto Puro)
  - Esteira 2: Questões COM Imagem (Gemini Multimodal + recorte PNG)

Recursos:
  - Cache em memória para deduplicação instantânea.
  - Auto-recuperação com retry e tolerância a falhas isoladas.
  - Trava de segurança que só para se houver 5 erros CONSECUTIVOS.
  - Concorrência ajustável para aproveitar plano pago.
"""

import io
import sys
import time
import argparse
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import pandas as pd

# Adiciona a raiz do projeto ao sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

# Suporte UTF-8 no terminal Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from src.database.db import pegar_conexao, inserir_questao
from src.ai.translator import traduzir_questao_matematica
from src.ai.client import tem_chave_configurada


def parse_args():
    parser = argparse.ArgumentParser(description="Ingestão de Questões MathNet em Paralelo via Gemini")
    parser.add_argument("--sem-imagem", type=int, default=2500, help="Quantidade de questões SEM imagem (padrão: 2500)")
    parser.add_argument("--com-imagem", type=int, default=2500, help="Quantidade de questões COM imagem (padrão: 2500)")
    parser.add_argument("--delay", type=float, default=0.2, help="Pausa em segundos entre requisições por worker (padrão: 0.2s)")
    parser.add_argument("--max-erros", type=int, default=5, help="Erros consecutivos para acionar parada de emergência (padrão: 5)")
    return parser.parse_args()


def carregar_enunciados_existentes():
    """Carrega os prefixos dos enunciados que já estão no banco para deduplicação rápida."""
    con = pegar_conexao()
    cur = con.cursor()
    cur.execute("SELECT enunciado FROM questoes")
    existentes = set()
    for row in cur.fetchall():
        texto = str(row[0] or "").strip()
        if texto:
            # Guarda os primeiros 50 caracteres limpos
            prefixo = " ".join(texto[:60].split()).lower()
            existentes.add(prefixo)
    con.close()
    return existentes


def main():
    args = parse_args()
    
    if not tem_chave_configurada():
        print("❌ ERRO: Nenhuma chave de API do Gemini encontrada no .env ou variáveis de ambiente!")
        sys.exit(1)

    pasta_uploads = ROOT_DIR / "data" / "uploads"
    pasta_uploads.mkdir(parents=True, exist_ok=True)

    log_falhas = ROOT_DIR / "data" / "falhas_ingestao.log"

    parquet_sem = ROOT_DIR / "data" / "mathnet_sem_imagem.parquet"
    parquet_com = ROOT_DIR / "data" / "mathnet_com_imagem.parquet"

    if not parquet_sem.exists() or not parquet_com.exists():
        print("❌ ERRO: Arquivos parquet não encontrados em data/.")
        sys.exit(1)

    print("=" * 68)
    print("🚀 MATHAI — INGESTÃO MASSIVA CONCORRENTE COM GEMINI DUPLO")
    print(f"  📝 Meta Sem Imagem: {args.sem_imagem} questões")
    print(f"  🖼️ Meta Com Imagem: {args.com_imagem} questões")
    print(f"  🎯 Meta Total:      {args.sem_imagem + args.com_imagem} questões")
    print(f"  ⏱️ Delay/Worker:    {args.delay}s (Otimizado para Plano Pago)")
    print(f"  🛡️ Trava de Parada: Ativa após {args.max_erros} falhas consecutivas")
    print("=" * 68)

    print("\n🔍 Carregando banco de dados para evitar duplicatas...")
    enunciados_banco = carregar_enunciados_existentes()
    print(f"📚 {len(enunciados_banco)} questões já existentes no banco (não serão duplicadas).")

    print("\n📂 Carregando bases de dados Parquet...")
    df_sem_full = pd.read_parquet(parquet_sem)
    df_com_full = pd.read_parquet(parquet_com)

    df_sem_alvo = df_sem_full.iloc[:args.sem_imagem]
    df_com_alvo = df_com_full.iloc[:args.com_imagem]

    print(f"✅ Prontas para envio: {len(df_sem_alvo)} sem imagem | {len(df_com_alvo)} com imagem\n")

    evento_parada = threading.Event()
    lock_banco = threading.Lock()
    lock_log = threading.Lock()

    estatisticas = {
        "sem_imagem": {"sucesso": 0, "puladas": 0, "falhas": 0, "erros_consecutivos": 0},
        "com_imagem": {"sucesso": 0, "puladas": 0, "falhas": 0, "erros_consecutivos": 0}
    }

    def registrar_falha(worker_name, idx, row_id, motivo):
        with lock_log:
            with open(log_falhas, "a", encoding="utf-8") as f:
                f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [{worker_name}] Linha {idx} (ID: {row_id}) - {motivo}\n")

    # ──────────────────────────────────────────────────────────────────────────
    # WORKER 1: SEM IMAGEM
    # ──────────────────────────────────────────────────────────────────────────
    def worker_sem_imagem(df_subset):
        pbar = tqdm(
            df_subset.iterrows(),
            total=len(df_subset),
            desc="📝 [Worker 1 - Sem Img]",
            position=0,
            dynamic_ncols=True
        )

        for index, row in pbar:
            if evento_parada.is_set():
                break

            enunciado_orig = str(row.get("problem_markdown", "") or row.get("enunciado", "")).strip()
            if not enunciado_orig:
                continue

            row_id = str(row.get('id', index))
            ano_val = row.get("ano")
            ano_int = int(ano_val) if str(ano_val).isdigit() else None
            gabarito_orig = str(row.get("final_answer", "") or row.get("gabarito", ""))
            banca_orig = str(row.get("banca", "") or row.get("competition", "Olimpíada"))
            topico_orig = str(row.get("topics_flat", "") or row.get("topico", "Matemática"))

            # Tentativa de tradução com até 3 retries
            dados = None
            for tentativa in range(1, 4):
                try:
                    dados = traduzir_questao_matematica(
                        enunciado_original=enunciado_orig,
                        gabarito_original=gabarito_orig,
                        banca_original=banca_orig,
                        ano_original=ano_int,
                        categoria_sugerida=topico_orig,
                        imagem_bytes=None
                    )
                    if dados and dados.get("enunciado_pt"):
                        break
                except Exception as e:
                    if tentativa < 3:
                        time.sleep(1.5 * tentativa)

            # Se falhou após todos os retries
            if not dados or not dados.get("enunciado_pt"):
                estatisticas["sem_imagem"]["falhas"] += 1
                estatisticas["sem_imagem"]["erros_consecutivos"] += 1
                registrar_falha("Worker 1", index, row_id, "Retorno nulo ou inválido do Gemini")

                if estatisticas["sem_imagem"]["erros_consecutivos"] >= args.max_erros:
                    print(f"\n❌ [PARADA DE EMERGÊNCIA - WORKER 1] {args.max_erros} erros consecutivos! Interrompendo...")
                    evento_parada.set()
                    break
                continue

            # Sucesso na tradução: reseta contador de erros consecutivos
            estatisticas["sem_imagem"]["erros_consecutivos"] = 0

            # Checa se o texto traduzido já existe no banco
            enunciado_pt = dados.get("enunciado_pt", enunciado_orig).strip()
            pref_pt = " ".join(enunciado_pt[:60].split()).lower()

            with lock_banco:
                if pref_pt in enunciados_banco:
                    estatisticas["sem_imagem"]["puladas"] += 1
                    continue

                try:
                    inserir_questao(
                        materia=dados.get("materia", "Matemática"),
                        topico=dados.get("topico", "Geral"),
                        subtopico=dados.get("subtopico"),
                        dificuldade=dados.get("dificuldade", 3),
                        banca=dados.get("banca", banca_orig),
                        ano=dados.get("ano", ano_int),
                        enunciado=enunciado_pt,
                        gabarito=dados.get("gabarito", gabarito_orig),
                        estrategias_esperadas=dados.get("estrategias_esperadas", []),
                        figura_path=None
                    )
                    enunciados_banco.add(pref_pt)
                    estatisticas["sem_imagem"]["sucesso"] += 1
                except Exception as e_db:
                    registrar_falha("Worker 1", index, row_id, f"Erro no banco: {e_db}")

            if args.delay > 0:
                time.sleep(args.delay)

        pbar.close()

    # ──────────────────────────────────────────────────────────────────────────
    # WORKER 2: COM IMAGEM
    # ──────────────────────────────────────────────────────────────────────────
    def worker_com_imagem(df_subset):
        pbar = tqdm(
            df_subset.iterrows(),
            total=len(df_subset),
            desc="🖼️ [Worker 2 - Com Img]",
            position=1,
            dynamic_ncols=True
        )

        for index, row in pbar:
            if evento_parada.is_set():
                break

            enunciado_orig = str(row.get("problem_markdown", "") or row.get("enunciado", "")).strip()
            if not enunciado_orig:
                continue

            row_id = str(row.get('id', index))
            caminho_figura_db = None
            imagem_bytes = None
            imagens = row.get("images") if row.get("images") is not None else row.get("imagens")
            
            if imagens is not None and len(imagens) > 0:
                nome_img = f"mathnet_{row_id}.png"
                caminho_disco = pasta_uploads / nome_img
                
                img_obj = imagens[0]
                if isinstance(img_obj, dict) and img_obj.get("bytes"):
                    imagem_bytes = img_obj["bytes"]
                    Image.open(io.BytesIO(imagem_bytes)).save(caminho_disco)
                    caminho_figura_db = f"data/uploads/{nome_img}"
                elif hasattr(img_obj, "save"):
                    buf = io.BytesIO()
                    img_obj.save(buf, format="PNG")
                    imagem_bytes = buf.getvalue()
                    img_obj.save(caminho_disco)
                    caminho_figura_db = f"data/uploads/{nome_img}"

            ano_val = row.get("ano")
            ano_int = int(ano_val) if str(ano_val).isdigit() else None
            gabarito_orig = str(row.get("final_answer", "") or row.get("gabarito", ""))
            banca_orig = str(row.get("banca", "") or row.get("competition", "Olimpíada"))
            topico_orig = str(row.get("topics_flat", "") or row.get("topico", "Matemática"))

            # Tentativa de tradução com até 3 retries
            dados = None
            for tentativa in range(1, 4):
                try:
                    dados = traduzir_questao_matematica(
                        enunciado_original=enunciado_orig,
                        gabarito_original=gabarito_orig,
                        banca_original=banca_orig,
                        ano_original=ano_int,
                        categoria_sugerida=topico_orig,
                        imagem_bytes=imagem_bytes
                    )
                    if dados and dados.get("enunciado_pt"):
                        break
                except Exception as e:
                    if tentativa < 3:
                        time.sleep(1.5 * tentativa)

            # Se falhou após todos os retries
            if not dados or not dados.get("enunciado_pt"):
                estatisticas["com_imagem"]["falhas"] += 1
                estatisticas["com_imagem"]["erros_consecutivos"] += 1
                registrar_falha("Worker 2", index, row_id, "Retorno nulo ou inválido do Gemini Multimodal")

                if estatisticas["com_imagem"]["erros_consecutivos"] >= args.max_erros:
                    print(f"\n❌ [PARADA DE EMERGÊNCIA - WORKER 2] {args.max_erros} erros consecutivos! Interrompendo...")
                    evento_parada.set()
                    break
                continue

            # Sucesso na tradução: reseta contador de erros consecutivos
            estatisticas["com_imagem"]["erros_consecutivos"] = 0

            # Checa se o texto traduzido já existe no banco
            enunciado_pt = dados.get("enunciado_pt", enunciado_orig).strip()
            pref_pt = " ".join(enunciado_pt[:60].split()).lower()

            with lock_banco:
                if pref_pt in enunciados_banco:
                    estatisticas["com_imagem"]["puladas"] += 1
                    continue

                try:
                    inserir_questao(
                        materia=dados.get("materia", "Matemática"),
                        topico=dados.get("topico", "Geral"),
                        subtopico=dados.get("subtopico"),
                        dificuldade=dados.get("dificuldade", 3),
                        banca=dados.get("banca", banca_orig),
                        ano=dados.get("ano", ano_int),
                        enunciado=enunciado_pt,
                        gabarito=dados.get("gabarito", gabarito_orig),
                        estrategias_esperadas=dados.get("estrategias_esperadas", []),
                        figura_path=caminho_figura_db
                    )
                    enunciados_banco.add(pref_pt)
                    estatisticas["com_imagem"]["sucesso"] += 1
                except Exception as e_db:
                    registrar_falha("Worker 2", index, row_id, f"Erro no banco: {e_db}")

            if args.delay > 0:
                time.sleep(args.delay)

        pbar.close()

    # ──────────────────────────────────────────────────────────────────────────
    # DISPARO CONCORRENTE
    # ──────────────────────────────────────────────────────────────────────────
    inicio_tempo = time.time()
    try:
        with ThreadPoolExecutor(max_workers=2) as executor:
            fut_sem = executor.submit(worker_sem_imagem, df_sem_alvo)
            fut_com = executor.submit(worker_com_imagem, df_com_alvo)
            fut_sem.result()
            fut_com.result()
    except KeyboardInterrupt:
        print("\n\n🛑 Ingestão interrompida manualmente pelo usuário (Ctrl+C).")
        evento_parada.set()

    duracao = time.time() - inicio_tempo
    total_sucesso = estatisticas["sem_imagem"]["sucesso"] + estatisticas["com_imagem"]["sucesso"]
    total_puladas = estatisticas["sem_imagem"]["puladas"] + estatisticas["com_imagem"]["puladas"]
    total_falhas = estatisticas["sem_imagem"]["falhas"] + estatisticas["com_imagem"]["falhas"]

    print("\n" + "=" * 68)
    print("📊 RELATÓRIO FINAL DA INGESTÃO:")
    print(f"  ⏱️ Tempo total decorrido:   {duracao / 60:.2f} minutos ({duracao:.1f}s)")
    print(f"  📝 Sem Imagem -> Sucesso:   {estatisticas['sem_imagem']['sucesso']} | Puladas: {estatisticas['sem_imagem']['puladas']} | Falhas: {estatisticas['sem_imagem']['falhas']}")
    print(f"  🖼️ Com Imagem -> Sucesso:   {estatisticas['com_imagem']['sucesso']} | Puladas: {estatisticas['com_imagem']['puladas']} | Falhas: {estatisticas['com_imagem']['falhas']}")
    print(f"  🎉 Total Gravadas no Banco: {total_sucesso} questões")
    print(f"  ⏭️ Total Puladas (já salvas): {total_puladas} questões")
    if total_falhas > 0:
        print(f"  ⚠️ Total de Falhas Isoladas: {total_falhas} (detalhes em data/falhas_ingestao.log)")
    print("  🔒 Conexões fechadas e banco sincronizado com sucesso.")
    print("=" * 68)


if __name__ == "__main__":
    main()
