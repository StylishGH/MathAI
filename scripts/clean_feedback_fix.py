import sys

with open("src/app/components/feedback_form.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if skip:
        if "st.rerun()" in line:
            skip = False
        continue

    # Remove immediate diagnosis saving
    if "# \U0001f4be Auto-salva o diagnóstico no banco imediatamente" in line or "# \ud83d\udcbe Auto-salva o diagnóstico no banco imediatamente" in line or "Auto-salva o diagnóstico no banco imediatamente" in line:
        skip = True
        continue

    # Fix fallback
    if 'aluno_id = st.session_state.get("aluno_id", 1)' in line:
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(f'{indent}aluno_id = st.session_state.get("aluno_id")\n')
        new_lines.append(f'{indent}if aluno_id is None:\n')
        new_lines.append(f'{indent}    raise RuntimeError("Aluno não autenticado.")\n')
        continue

    # Fix argument
    if 'aluno_id=st.session_state.get("aluno_id", 1)' in line:
        new_lines.append(line.replace('aluno_id=st.session_state.get("aluno_id", 1)', 'aluno_id=aluno_id'))
        continue
    
    # Check for "Salvar Tentativa e Atualizar Perfil" to inject aluno_id if needed
    if 'st.button' in line and "Salvar Tentativa e Atualizar Perfil" in line:
        new_lines.append(line)
        indent = line[:len(line) - len(line.lstrip())]
        new_lines.append(f'{indent}    aluno_id = st.session_state.get("aluno_id")\n')
        new_lines.append(f'{indent}    if aluno_id is None:\n')
        new_lines.append(f'{indent}        raise RuntimeError("Aluno não autenticado.")\n')
        continue

    new_lines.append(line)

with open("src/app/components/feedback_form.py", "w", encoding="utf-8") as f:
    f.writelines(new_lines)
