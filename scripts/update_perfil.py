import re

with open('src/app/pages/perfil.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Only replace in the FACULDADES_BRASIL list definition
content = re.sub(
    r'(FACULDADES_BRASIL = \[.*?)("Outra Faculdade / Universidade"\n\])',
    r'\1"CEDERJ - Consórcio Cederj",\n    \2',
    content,
    flags=re.DOTALL
)

motivo_target = '"enem_vestibular": "📝 ENEM / Vestibular",'
motivo_replacement = '"enem_vestibular": "📝 ENEM / Vestibular",\n    "ensino_superior": "🎓 Provas de Faculdade (Cálculo 3, Álgebra Linear, EPs...)",'
content = content.replace(motivo_target, motivo_replacement)

with open('src/app/pages/perfil.py', 'w', encoding='utf-8') as f:
    f.write(content)
