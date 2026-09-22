"""
Utilitários de formatação e parsing para o MathAI.
"""

import re


def extrair_enunciado_e_alternativas(texto: str):
    """
    Separa o texto do enunciado das alternativas de múltipla escolha (A, B, C, D, E).
    Retorna uma tupla: (enunciado_limpo, dict_alternativas)
    Exemplo:
        enunciado_limpo: "A robótica tem se tornado... igual a:"
        dict_alternativas: {'A': '32', 'B': '34', 'C': '36', 'D': '38', 'E': '40'}
    """
    if not texto:
        return "", {}

    # Encontra todas as linhas que iniciam com (A), (B), (C), (D), (E)
    padrao = r'(?m)^\(([A-E])\)\s*(.+)$'
    matches = list(re.finditer(padrao, texto))

    if len(matches) >= 2:
        primeiro_match = matches[0]
        corpo = texto[:primeiro_match.start()].rstrip()
        alternativas = {m.group(1): m.group(2).strip() for m in matches}
        return corpo, alternativas

    return texto, {}


def corrigir_latex(texto: str) -> str:
    """
    Corrige bugs comuns de formatação LaTeX no banco de questões.
    Exemplos:
        '8imes8'   -> '8\\times 8'
        '3imes5'   -> '3\\times 5'
        'cdot'     -> '\\cdot'  (se aparecer sem backslash)
        'sqrt'     -> '\\sqrt'  (se aparecer sem backslash)
    """
    if not texto:
        return texto

    # Corrige "Nimes M" → "N\times M" (número/letra + imes + número/letra)
    # Cobre casos como: 8imes8, 3imes5, aimes b, etc.
    texto = re.sub(r'(\w)imes(\w)', r'\1\\times \2', texto)

    # Corrige comandos LaTeX sem backslash comuns dentro de $...$
    # Apenas dentro de contextos matemáticos (entre $ ou $$)
    def fix_math_block(m):
        bloco = m.group(0)
        # Comandos sem backslash que precisam de backslash
        bloco = re.sub(r'(?<!\\)\b(cdot|leq|geq|neq|approx|infty|pi|alpha|beta|gamma|delta|theta|lambda|mu|sigma|sqrt|frac|sum|int|lim)\b', r'\\\1', bloco)
        return bloco

    # Aplica correção dentro de blocos $...$ e $$...$$
    texto = re.sub(r'\$\$[\s\S]*?\$\$', fix_math_block, texto)
    texto = re.sub(r'\$[^\$\n]+?\$', fix_math_block, texto)

    return texto


def e_questao_discursiva(questao: dict) -> bool:
    """
    Detecta se a questão é discursiva (aberta / de prova).
    Uma questão é discursiva se:
      - O campo 'tipo' for explicitamente 'discursiva', OU
      - Não possui alternativas (A), (B), (C), (D), (E) no enunciado, E o gabarito não é uma letra simples A-E
    """
    tipo = str(questao.get("tipo", "")).strip().lower()
    if tipo == "discursiva":
        return True
    if tipo == "objetiva":
        return False

    enunciado_raw = questao.get("enunciado", "")
    _, alternativas = extrair_enunciado_e_alternativas(enunciado_raw)
    if alternativas:
        return False  # Tem alternativas → objetiva

    gabarito = str(questao.get("gabarito", "")).strip().upper()
    # Se o gabarito é uma única letra A-E, provavelmente é objetiva sem alternativas marcadas
    if gabarito in ("A", "B", "C", "D", "E"):
        return False

    return True  # Sem alternativas e gabarito não é letra → discursiva


def fix_latex_row_breaks(latex_str: str) -> str:
    r"""
    Substitui quebras de linha com barra simples (\ ) por barra dupla (\\ )
    dentro de ambientes LaTeX como cases, pmatrix, matrix, aligned, etc.
    Isso previne que linhas de sistemas ou matrizes fiquem coladas em uma só linha
    quando o JSON da IA decodifica '\\' como '\'.
    """
    env_pattern = r'(\\begin\{(?:cases|matrix|pmatrix|bmatrix|vmatrix|Vmatrix|aligned|align\*?|array)\})([\s\S]*?)(\\end\{(?:cases|matrix|pmatrix|bmatrix|vmatrix|Vmatrix|aligned|align\*?|array)\})'

    def repl_env(match):
        start = match.group(1)
        body = match.group(2)
        end = match.group(3)
        # Substitui barra invertida isolada seguida de espaço, quebra de linha ou número
        body = re.sub(r'(?<!\\)\\(?:\s+|\n|(?=[0-9]))', r'\\\\ ', body)
        return f"{start}{body}{end}"

    return re.sub(env_pattern, repl_env, latex_str)


def has_natural_language(text: str) -> bool:
    """Detecta se há palavras em linguagem natural (português/inglês) no texto."""
    cleaned = re.sub(r'\\[a-zA-Z]+(\{[^}]*\})?', ' ', text)
    cleaned = re.sub(r'\{(?:cases|matrix|pmatrix|bmatrix|vmatrix|Vmatrix|aligned|align\*?|array)\}', ' ', cleaned)
    cleaned = re.sub(r'[{}\[\]()_^\d\s+\-*=<>|/\\,.;:&!~]', ' ', cleaned)

    words = [w for w in cleaned.split() if len(w) > 2]
    termos_math = {
        'sin', 'cos', 'tan', 'cot', 'sec', 'csc', 'sen', 'tg', 'cotg',
        'log', 'ln', 'exp', 'det', 'dim', 'ker', 'gcd', 'mdc', 'mmc',
        'max', 'min', 'mod', 'lim', 'sup', 'inf', 'arg', 'deg'
    }
    palavras_reais = [w for w in words if w.lower() not in termos_math]
    return len(palavras_reais) > 0


def is_math_line(text: str) -> bool:
    """Verifica se uma linha isolada é uma fórmula matemática."""
    t = text.strip()
    if not t:
        return False
    if has_natural_language(t):
        return False
    if any(k in t for k in [r'\begin{', r'\end{', r'\pmatrix', r'\cases', r'\matrix', r'\aligned', r'\implies', r'\frac', r'\sqrt', '^', '_', '=', '<', '>']):
        return True
    return False


def formatar_transcricao_latex(transcricao: str) -> str:
    """
    Formata o texto de transcrição OCR para renderização impecável no Streamlit st.markdown.
    - Corrige quebras de linha em ambientes matriciais/sistemas (ex: \\begin{cases}).
    - Garante que blocos matemáticos estejam devidamente delimitados por $$...$$ para ativação do KaTeX.
    - Preserva texto explicativo ou comentários em linguagem natural sem quebrar a tipografia.
    """
    if not transcricao or not isinstance(transcricao, str):
        return ""

    texto = fix_latex_row_breaks(transcricao.strip())

    # Se já estiver completamente envolvido por $$ ou $$, ou se já tiver delimitadores
    if texto.startswith("$$") and texto.endswith("$$"):
        return texto

    # Protege ambientes como \begin{cases}...\end{cases} substituindo por placeholders temporários
    env_regex = r'(\\begin\{(?:cases|matrix|pmatrix|bmatrix|vmatrix|Vmatrix|aligned|align\*?|array)\}[\s\S]*?\\end\{(?:cases|matrix|pmatrix|bmatrix|vmatrix|Vmatrix|aligned|align\*?|array)\})'
    placeholders = {}

    def store_env(m):
        key = f"__MATH_ENV_{len(placeholders)}__"
        placeholders[key] = m.group(0)
        return key

    texto_masked = re.sub(env_regex, store_env, texto)

    # Processa linha a linha
    linhas = texto_masked.splitlines()
    novas_linhas = []

    for l in linhas:
        l_trim = l.strip()
        if not l_trim:
            novas_linhas.append("")
            continue

        # Se já tem $ ou $$ ou sintaxe markdown
        if l_trim.startswith("$$") or l_trim.startswith("$") or l_trim.startswith("#") or l_trim.startswith("- ") or l_trim.startswith("* "):
            novas_linhas.append(l)
            continue

        # Se a linha contém um placeholder de ambiente
        contains_placeholder = any(k in l_trim for k in placeholders)
        if contains_placeholder:
            for k, val in placeholders.items():
                l_trim = l_trim.replace(k, val)
            if not has_natural_language(l_trim):
                novas_linhas.append(f"$${l_trim}$$")
            else:
                novas_linhas.append(l_trim)
            continue

        # Se for uma linha puramente matemática
        if is_math_line(l_trim):
            novas_linhas.append(f"$${l_trim}$$")
        else:
            novas_linhas.append(l)

    # Restaura qualquer placeholder que ainda reste
    resultado = "\n".join(novas_linhas)
    for k, val in placeholders.items():
        resultado = resultado.replace(k, val)

    resultado = re.sub(r'\n{3,}', '\n\n', resultado)
    return resultado.strip()


