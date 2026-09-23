import sys

with open("src/app/pages/perfil.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'st.session_state.usuario_logado["curso"] = novo_curso',
    'st.session_state.usuario_logado["curso"] = novo_curso\n                    st.session_state.usuario_logado["consentimento_dados"] = 1 if novo_consentimento else 0'
)

with open("src/app/pages/perfil.py", "w", encoding="utf-8") as f:
    f.write(content)
