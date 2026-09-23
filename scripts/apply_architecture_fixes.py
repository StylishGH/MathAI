import sys
import re

# 1. Update attempts.py function signatures and fallback usages
with open("src/database/attempts.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("aluno_id: int = 1,", "aluno_id: int,")
content = content.replace("aluno_id: int = 1\n)", "aluno_id: int\n)")
content = content.replace("aluno_id: int = 1", "aluno_id: int")

with open("src/database/attempts.py", "w", encoding="utf-8") as f:
    f.write(content)

# 2. Update feedback_form.py
with open("src/app/components/feedback_form.py", "r", encoding="utf-8") as f:
    content = f.read()

# Remove the immediate diagnosis saving
block_to_remove = """                        # 💾 Auto-salva o diagnóstico no banco imediatamente
                        aluno_id = st.session_state.get("aluno_id", 1)
                        salvar_diagnostico_ia(
                            questao_id=q_id,
                            diagnostico_dict=diag,
                            aluno_id=aluno_id,
                            imagem_path=st.session_state.get(f"nome_resolucao_{q_id}"),
                            justificativa_texto=txt_just
                        )"""
content = content.replace(block_to_remove, "")

# Fix aluno_id fallbacks
fallback_code = """aluno_id=st.session_state.get("aluno_id", 1)"""
safe_code = """aluno_id=st.session_state.get("aluno_id")"""
content = content.replace(fallback_code, safe_code)
content = content.replace('aluno_id = st.session_state.get("aluno_id", 1)', 
                          'aluno_id = st.session_state.get("aluno_id")\n                if aluno_id is None:\n                    raise RuntimeError("Aluno não autenticado.")')

with open("src/app/components/feedback_form.py", "w", encoding="utf-8") as f:
    f.write(content)

# 3. Update resolver.py
with open("src/app/pages/resolver.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace('aluno_id = st.session_state.get("aluno_id", 1)',
                          'aluno_id = st.session_state.get("aluno_id")\n    if aluno_id is None:\n        raise RuntimeError("Aluno não autenticado.")')

with open("src/app/pages/resolver.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Updates completed.")
