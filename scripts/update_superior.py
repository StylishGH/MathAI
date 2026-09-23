import re

with open('src/app/pages/perfil.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Add list of subjects
subj_list = """
MATERIAS_SUPERIOR = [
    "Cálculo 1",
    "Cálculo 2",
    "Cálculo 3",
    "Álgebra Linear",
    "Geometria Analítica",
    "Matemática Discreta",
    "Física 1"
]
"""
if "MATERIAS_SUPERIOR" not in content:
    content = content.replace("CONCURSOS_VESTIBULARES = [", subj_list + "\nCONCURSOS_VESTIBULARES = [")

# Find tem_foco_vestibular and add tem_foco_superior
content = content.replace(
    'tem_foco_vestibular = "enem_vestibular" in novos_motivos',
    'tem_foco_vestibular = "enem_vestibular" in novos_motivos\n        tem_foco_superior = "ensino_superior" in novos_motivos'
)

# Find the end of the if tem_foco_vestibular block to insert if tem_foco_superior
superior_block = """
        if tem_foco_superior:
            st.markdown(f\"\"\"
            <div style="margin-top: 10px; font-size: 0.88rem; font-weight: 700; color: {'#fbbf24' if is_dark else '#b45309'};">
                🎓 Foco no Ensino Superior (Matérias e Provas):
            </div>
            \"\"\", unsafe_allow_html=True)

            superior_defaults = [v for v in MATERIAS_SUPERIOR if any(f.lower() in v.lower() for f in foco_salvo)]
            sel_superior = st.multiselect(
                "Selecione as disciplinas da sua faculdade (ex: CEDERJ, USP, etc.)",
                options=MATERIAS_SUPERIOR,
                default=superior_defaults,
                key="perfil_sel_superior"
            )
            concursos_foco_selecionados.extend(sel_superior)
            
            # Se a faculdade não estiver salva em foco_salvo, a gente adiciona silenciosamente para o banco de questões poder filtrar
            if nova_faculdade and nova_faculdade != "Outra Faculdade" and not any(nova_faculdade in f for f in concursos_foco_selecionados):
                # Pega só a sigla (ex: "CEDERJ")
                sigla = nova_faculdade.split(" - ")[0]
                concursos_foco_selecionados.append(sigla)
"""

# Insert it right before the SAVE button line: # 💾 BOTÃO DE SALVAR
content = content.replace('      # 💾 BOTÃO DE SALVAR', superior_block + '\n      # 💾 BOTÃO DE SALVAR')

with open('src/app/pages/perfil.py', 'w', encoding='utf-8') as f:
    f.write(content)
