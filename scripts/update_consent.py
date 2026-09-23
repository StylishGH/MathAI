import sys
import re

with open("src/app/pages/perfil.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add the UI for consent
consent_ui = """    st.markdown("---")
    st.markdown("#### 🔒 Privacidade e Consentimento de Dados")
    st.markdown("<div style='font-size: 0.9em; color: #64748b; margin-bottom: 10px;'>Visando o futuro da plataforma, o MathAI separa estritamente o que são <b>dados observados</b> (suas resoluções, respostas e tempo) de <b>dados derivados</b> (diagnóstico da IA e estimativa de dificuldade). Precisamos do seu consentimento para armazenar e utilizar seus dados observados (de forma anônima) no treinamento das futuras IAs do projeto.</div>", unsafe_allow_html=True)
    consentimento_atual = bool(usuario.get('consentimento_dados', 0))
    novo_consentimento = st.checkbox(
        "Autorizo o armazenamento e o uso anônimo das minhas resoluções para desenvolvimento e treinamento do MathAI.", 
        value=consentimento_atual, 
        key="check_consentimento"
    )

    c_save_esq, c_save_btn, c_save_dir = st.columns([1, 2, 1])"""

content = content.replace("    c_save_esq, c_save_btn, c_save_dir = st.columns([1, 2, 1])", consent_ui)

# Update the SQL query in the save button logic
old_sql = """                    cursor.execute('''
                        UPDATE usuarios 
                        SET nome = ?, idade = ?, celular = ?, motivos = ?, 
                            cep = ?, logradouro = ?, numero = ?, bairro = ?, 
                            cidade = ?, estado = ?, escolaridade = ?, faculdade = ?, 
                            curso = ?, concursos_foco = ?
                        WHERE id = ?
                    ''', (
                        novo_nome, nova_idade, novo_celular, motivos_json,
                        novo_cep, novo_logradouro, novo_numero, novo_bairro,
                        nova_cidade, novo_estado, nova_escolaridade, nova_faculdade,
                        novo_curso, json.dumps(concursos_foco_selecionados),
                        usuario["id"]
                    ))"""

new_sql = """                    cursor.execute('''
                        UPDATE usuarios 
                        SET nome = ?, idade = ?, celular = ?, motivos = ?, 
                            cep = ?, logradouro = ?, numero = ?, bairro = ?, 
                            cidade = ?, estado = ?, escolaridade = ?, faculdade = ?, 
                            curso = ?, concursos_foco = ?, consentimento_dados = ?
                        WHERE id = ?
                    ''', (
                        novo_nome, nova_idade, novo_celular, motivos_json,
                        novo_cep, novo_logradouro, novo_numero, novo_bairro,
                        nova_cidade, novo_estado, nova_escolaridade, nova_faculdade,
                        novo_curso, json.dumps(concursos_foco_selecionados),
                        1 if novo_consentimento else 0,
                        usuario["id"]
                    ))"""
content = content.replace(old_sql, new_sql)

with open("src/app/pages/perfil.py", "w", encoding="utf-8") as f:
    f.write(content)

print("perfil.py updated!")
