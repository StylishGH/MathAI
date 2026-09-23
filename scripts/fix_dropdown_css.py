import sys

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

css_fix = """
    /* Correção do texto escuro invisível no Multiselect e Selectbox */
    div[data-baseweb="select"] ul, 
    ul[role="listbox"],
    li[role="option"] {
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #334155 !important;
        color: #f59e0b !important;
    }
</style>"""

content = content.replace("</style>", css_fix)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
