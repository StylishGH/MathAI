import os
import glob
import time
import subprocess

efomm_dir = r"C:\Users\Guilherme\Downloads\EFOMM"
script_path = r"C:\Users\Guilherme\Documents\MathAI\scripts\ingest_efomm.py"

pairs = [
    (["PROVA-BRANCA-2-DIA-2026.pdf", "2026 - EFOMM - GABARITO DEFINITIVO.pdf"], 2026),
    (["2-DIA-AZUL_2-2024.pdf", "GABARITO-DEFINITIVO-2024.pdf"], 2024),
    (["provas-anteriores-efomm-2021-2022.pdf", "GABARITO-DEFINITIVO-EFOMM-2022.pdf"], 2022)
]

processed_files = set()
commands = []

for pair, year in pairs:
    full_paths = [os.path.join(efomm_dir, f) for f in pair if os.path.exists(os.path.join(efomm_dir, f))]
    if full_paths:
        commands.append(full_paths)
        processed_files.update(pair)

all_pdfs = glob.glob(os.path.join(efomm_dir, "*.pdf"))
for pdf in all_pdfs:
    basename = os.path.basename(pdf)
    if basename not in processed_files and "GABARITO" not in basename.upper():
        commands.append([pdf])

print(f"Total batches to process: {len(commands)}")

for idx, cmd_args in enumerate(commands):
    print(f"\n--- Batch {idx+1}/{len(commands)} ---")
    run_args = ["python", script_path] + cmd_args
    try:
        subprocess.run(run_args, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erro no batch {idx+1}: {e}")
    
    if idx < len(commands) - 1:
        print("Dormindo 35s para respeitar limites do plano gratuito...")
        time.sleep(35)

print("\nIngestao EFOMM concluida!")
