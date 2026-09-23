import re

with open('src/app/pages/perfil.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace MOTIVOS_OPCOES using regex to match the variable
pattern = r'(MOTIVOS_OPCOES = \{)(.*?)(\})'
def replacer(match):
    inner = match.group(2)
    # Add ensino_superior after enem_vestibular
    inner = re.sub(
        r'("enem_vestibular": ".*?",)',
        r'\1\n    "ensino_superior": "🎓 Provas de Faculdade (Cálculo 3, Álgebra Linear, EPs...)",',
        inner
    )
    return match.group(1) + inner + match.group(3)

content = re.sub(pattern, replacer, content, flags=re.DOTALL)

with open('src/app/pages/perfil.py', 'w', encoding='utf-8') as f:
    f.write(content)
