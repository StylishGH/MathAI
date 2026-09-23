import sys

with open("src/database/attempts.py", "r", encoding="utf-8") as f:
    content = f.read()

bad_sig = """def registrar_dica_socratica(
    questao_id: int,
    nivel_dica: int,
    texto_dica: str,
    modelo_gemini: str = "",
    aluno_id: int
)"""

good_sig = """def registrar_dica_socratica(
    questao_id: int,
    aluno_id: int,
    nivel_dica: int,
    texto_dica: str,
    modelo_gemini: str = ""
)"""

content = content.replace(bad_sig, good_sig)

with open("src/database/attempts.py", "w", encoding="utf-8") as f:
    f.write(content)
