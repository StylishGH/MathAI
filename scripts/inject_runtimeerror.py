import sys

with open("src/app/components/feedback_form.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'if st.button("💾 Salvar Tentativa e Atualizar Perfil"',
    'if st.button("💾 Salvar Tentativa e Atualizar Perfil"'
)

# wait, I don't know the exact emojis on the button due to encoding issues in terminal output!
# I will just regex replace the next line.
import re

content = re.sub(
    r'(# Junta justificativa inicial com anotações de reflexão)',
    r'aluno_id = st.session_state.get("aluno_id")\n                if aluno_id is None:\n                    raise RuntimeError("Aluno não autenticado.")\n\n                \g<1>',
    content
)

with open("src/app/components/feedback_form.py", "w", encoding="utf-8") as f:
    f.write(content)
