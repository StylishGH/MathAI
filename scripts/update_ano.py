import sys

with open("src/app/pages/banco.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update UI
old_ano_ui = """    with col_ano:
        anos = ["Todos"] + sorted(list(set(str(q.get("ano", "")) for q in questoes if q.get("ano"))), reverse=True)
        sel_ano = st.selectbox("📅 Ano:", anos, key="banco_filtro_ano")"""
new_ano_ui = """    with col_ano:
        anos = sorted(list(set(str(q.get("ano", "")) for q in questoes if q.get("ano"))), reverse=True)
        sel_anos = st.multiselect("📅 Ano(s):", options=anos, default=[], placeholder="Todos os Anos", key="banco_filtro_ano")"""
content = content.replace(old_ano_ui, new_ano_ui)

# 2. Update filter check
old_check = """    tem_filtro = (
        bool(sel_materias) or
        bool(sel_topicos) or
        bool(sel_bancas) or
        sel_tipo != "Todos" or
        sel_ano != "Todos" or
        bool(busca_termo)
    )"""
new_check = """    tem_filtro = (
        bool(sel_materias) or
        bool(sel_topicos) or
        bool(sel_bancas) or
        sel_tipo != "Todos" or
        bool(sel_anos) or
        bool(busca_termo)
    )"""
content = content.replace(old_check, new_check)

# 3. Update Shortcuts
old_esa = """            st.session_state.banco_filtro_banca = ["ESA"]
            st.session_state.banco_filtro_ano = "2026"
"""
new_esa = """            st.session_state.banco_filtro_banca = ["ESA"]
            st.session_state.banco_filtro_ano = ["2026"]
"""
content = content.replace(old_esa, new_esa)

old_geo = """            st.session_state.banco_filtro_banca = []
            st.session_state.banco_filtro_ano = "Todos"
"""
new_geo = """            st.session_state.banco_filtro_banca = []
            st.session_state.banco_filtro_ano = []
"""
content = content.replace(old_geo, new_geo)

old_todas = """            st.session_state.banco_filtro_banca = []
            st.session_state.banco_filtro_ano = "Todos"
"""
new_todas = """            st.session_state.banco_filtro_banca = []
            st.session_state.banco_filtro_ano = []
"""
content = content.replace(old_todas, new_todas)

# 4. Update Filtering
old_apply = """    if sel_ano != "Todos":
        filtradas = [q for q in filtradas if str(q.get("ano", "")) == sel_ano]"""
new_apply = """    if sel_anos:
        filtradas = [q for q in filtradas if str(q.get("ano", "")) in sel_anos]"""
content = content.replace(old_apply, new_apply)

# 5. Update hash
old_hash = """filtro_key_hash = f"{sel_materias}_{sel_topicos}_{sel_bancas}_{sel_ano}_{busca_termo}\""""
new_hash = """filtro_key_hash = f"{sel_materias}_{sel_topicos}_{sel_bancas}_{sel_anos}_{busca_termo}\""""
content = content.replace(old_hash, new_hash)

with open("src/app/pages/banco.py", "w", encoding="utf-8") as f:
    f.write(content)

print("Done updating anos to multiselect!")
