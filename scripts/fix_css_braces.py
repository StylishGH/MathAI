import sys

with open("app.py", "r", encoding="utf-8") as f:
    content = f.read()

bad_css = """    /* Correção do texto escuro invisível no Multiselect e Selectbox */
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
    }"""

good_css = """    /* Correção do texto escuro invisível no Multiselect e Selectbox */
    div[data-baseweb="select"] ul, 
    ul[role="listbox"],
    li[role="option"] {{
        background-color: #1e293b !important;
        color: #f8fafc !important;
    }}
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {{
        background-color: #334155 !important;
        color: #f59e0b !important;
    }}"""

# Try to revert whatever powershell did, just replace the general area
import re
# Find the start of the comment
start_idx = content.find("/* Correção do texto escuro invisível no Multiselect e Selectbox */")
if start_idx != -1:
    end_idx = content.find("</style>", start_idx)
    content = content[:start_idx] + good_css + "\n" + content[end_idx:]

with open("app.py", "w", encoding="utf-8") as f:
    f.write(content)
