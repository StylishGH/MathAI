import sys

with open("src/app/pages/banco.py", "r", encoding="utf-8") as f:
    content = f.read()

# Fix the broken backslashes and the sel_banca issue
content = content.replace(r"sel_bancas\[0\]", "sel_bancas[0]")
content = content.replace("sel_banca if sel_banca != 'Todas' else 'Personalizado'", "sel_bancas[0] if len(sel_bancas) == 1 else 'Personalizado'")

with open("src/app/pages/banco.py", "w", encoding="utf-8") as f:
    f.write(content)
