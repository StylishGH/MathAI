import sys

with open("src/app/pages/banco.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('if sel_banca == "ESA" and qtd_selecionadas == 12:', 'if "ESA" in sel_bancas and len(sel_bancas) == 1 and qtd_selecionadas == 12:')

with open("src/app/pages/banco.py", "w", encoding="utf-8") as f:
    f.write(content)
