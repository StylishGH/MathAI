import sys

with open("src/app/pages/banco.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace bancas definition
content = content.replace(
    'bancas = ["Todas"] + sorted(list(set(q.get("banca", "") for q in questoes if q.get("banca"))))',
    'bancas_raw = sorted(list(set(str(q.get("banca", "")) for q in questoes if q.get("banca"))))'
)

# 2. Replace filters UI
old_ui = """    # 1. Barra de Filtros
    col_mat, col_banca, col_tipo, col_ano, col_busca = st.columns([1.6, 1.2, 1.2, 1.0, 2.0])

    with col_mat:
        materias = ["Todas"] + sorted(list(set(q.get("materia", "") for q in questoes if q.get("materia"))))
        sel_materia = st.selectbox("Matéria:", materias, key="banco_filtro_materia")

    with col_banca:
        sel_banca = st.selectbox("Banca:", bancas, key="banco_filtro_banca")

    with col_tipo:
        tipos = ["Todos", "Discursiva", "Objetiva"]
        sel_tipo = st.selectbox("Tipo:", tipos, key="banco_filtro_tipo")

    with col_ano:
        anos = ["Todos"] + sorted(list(set(str(q.get("ano", "")) for q in questoes if q.get("ano"))), reverse=True)
        sel_ano = st.selectbox("Ano:", anos, key="banco_filtro_ano")

    with col_busca:
        busca_termo = st.text_input("🔍 Buscar no enunciado / tópico:", key="banco_filtro_busca").strip().lower()

    # Verifica se algum filtro está ativo
    tem_filtro = (
        sel_materia != "Todas" or
        sel_banca != "Todas" or
        sel_tipo != "Todos" or
        sel_ano != "Todos" or
        bool(busca_termo)
    )"""

new_ui = """    # 1. Barra de Filtros
    col_mat, col_topico, col_banca = st.columns([1.5, 1.5, 1.5])
    with col_mat:
        materias = sorted(list(set(q.get("materia", "") for q in questoes if q.get("materia"))))
        sel_materias = st.multiselect("📚 Matéria(s):", options=materias, default=[], placeholder="Todas as Matérias", key="banco_filtro_materia")
    with col_topico:
        if sel_materias:
            topicos = sorted(list(set(q.get("topico", "") for q in questoes if q.get("topico") and q.get("materia") in sel_materias)))
        else:
            topicos = sorted(list(set(q.get("topico", "") for q in questoes if q.get("topico"))))
        sel_topicos = st.multiselect("📑 Tópico(s) / Subtópico:", options=topicos, default=[], placeholder="Todos os Tópicos", key="banco_filtro_topico")
    with col_banca:
        sel_bancas = st.multiselect("🏛️ Banca(s):", options=bancas_raw, default=[], placeholder="Todas as Bancas", key="banco_filtro_banca")

    col_tipo, col_ano, col_busca = st.columns([1, 1, 2.5])
    with col_tipo:
        tipos = ["Todos", "Discursiva", "Objetiva"]
        sel_tipo = st.selectbox("📝 Tipo:", tipos, key="banco_filtro_tipo")
    with col_ano:
        anos = ["Todos"] + sorted(list(set(str(q.get("ano", "")) for q in questoes if q.get("ano"))), reverse=True)
        sel_ano = st.selectbox("📅 Ano:", anos, key="banco_filtro_ano")
    with col_busca:
        busca_termo = st.text_input("🔍 Buscar texto (Enunciado/Assunto):", key="banco_filtro_busca").strip().lower()

    # Verifica se algum filtro está ativo
    tem_filtro = (
        bool(sel_materias) or
        bool(sel_topicos) or
        bool(sel_bancas) or
        sel_tipo != "Todos" or
        sel_ano != "Todos" or
        bool(busca_termo)
    )"""
content = content.replace(old_ui, new_ui)

# 3. Replace shortcuts
old_esa = """        def _aplicar_atalho_esa():
            st.session_state.banco_filtro_materia = "Todas"
            st.session_state.banco_filtro_banca = "ESA"
            st.session_state.banco_filtro_ano = "2026"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = False"""
new_esa = """        def _aplicar_atalho_esa():
            st.session_state.banco_filtro_materia = []
            st.session_state.banco_filtro_topico = []
            st.session_state.banco_filtro_banca = ["ESA"]
            st.session_state.banco_filtro_ano = "2026"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = False"""
content = content.replace(old_esa, new_esa)

old_geo = """        def _aplicar_atalho_geo(materia_alvo):
            st.session_state.banco_filtro_materia = materia_alvo
            st.session_state.banco_filtro_banca = "Todas"
            st.session_state.banco_filtro_ano = "Todos"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = False"""
new_geo = """        def _aplicar_atalho_geo(materia_alvo):
            st.session_state.banco_filtro_materia = [materia_alvo]
            st.session_state.banco_filtro_topico = []
            st.session_state.banco_filtro_banca = []
            st.session_state.banco_filtro_ano = "Todos"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = False"""
content = content.replace(old_geo, new_geo)

old_todas = """        def _aplicar_atalho_todas():
            st.session_state.banco_filtro_materia = "Todas"
            st.session_state.banco_filtro_banca = "Todas"
            st.session_state.banco_filtro_ano = "Todos"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = True"""
new_todas = """        def _aplicar_atalho_todas():
            st.session_state.banco_filtro_materia = []
            st.session_state.banco_filtro_topico = []
            st.session_state.banco_filtro_banca = []
            st.session_state.banco_filtro_ano = "Todos"
            st.session_state.banco_filtro_busca = ""
            st.session_state.banco_mostrar_todas = True"""
content = content.replace(old_todas, new_todas)

# 4. Replace apply filters
old_apply = """    # 3. Aplica os Filtros
    filtradas = questoes
    if sel_materia != "Todas":
        filtradas = [q for q in filtradas if q.get("materia") == sel_materia]
    if sel_banca != "Todas":
        filtradas = [q for q in filtradas if q.get("banca") == sel_banca]
    if sel_tipo != "Todos":
        filtradas = [q for q in filtradas if q.get("tipo", "objetiva").lower() == sel_tipo.lower()]
    if sel_ano != "Todos":
        filtradas = [q for q in filtradas if str(q.get("ano", "")) == sel_ano]
    if busca_termo:
        filtradas = [
            q for q in filtradas
            if busca_termo in q.get("enunciado", "").lower()
            or busca_termo in q.get("topico", "").lower()
            or busca_termo in str(q.get("subtopico", "")).lower()
        ]"""
new_apply = """    # 3. Aplica os Filtros
    filtradas = questoes
    if sel_materias:
        filtradas = [q for q in filtradas if q.get("materia") in sel_materias]
    if sel_topicos:
        filtradas = [q for q in filtradas if q.get("topico") in sel_topicos]
    if sel_bancas:
        filtradas = [q for q in filtradas if q.get("banca") in sel_bancas]
    if sel_tipo != "Todos":
        filtradas = [q for q in filtradas if q.get("tipo", "objetiva").lower() == sel_tipo.lower()]
    if sel_ano != "Todos":
        filtradas = [q for q in filtradas if str(q.get("ano", "")) == sel_ano]
    if busca_termo:
        filtradas = [
            q for q in filtradas
            if busca_termo in q.get("enunciado", "").lower()
            or busca_termo in q.get("topico", "").lower()
            or busca_termo in str(q.get("subtopico", "")).lower()
        ]"""
content = content.replace(old_apply, new_apply)

# 5. Replace state hashes
content = content.replace(
    'filtro_key_hash = f"{sel_materia}_{sel_banca}_{sel_ano}_{busca_termo}"',
    'filtro_key_hash = f"{sel_materias}_{sel_topicos}_{sel_bancas}_{sel_ano}_{busca_termo}"'
)

# 6. Replace List Name
content = content.replace(
    'nome_default_lista = f"Lista: {sel_materia if sel_materia != \'Todas\' else \'Matemática\'} ({qtd_selecionadas} Questões)"',
    'nome_materia = sel_materias[0] if len(sel_materias) == 1 else "Matemática"\n            nome_default_lista = f"Lista: {nome_materia} ({qtd_selecionadas} Questões)"'
)

with open("src/app/pages/banco.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done string replacements!")
