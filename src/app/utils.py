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
      - Não possui alternativas (A), (B), (C), (D), (E) no enunciado, OU
      - O gabarito não é uma letra simples A-E
    """
    enunciado_raw = questao.get("enunciado", "")
    _, alternativas = extrair_enunciado_e_alternativas(enunciado_raw)
    if alternativas:
        return False  # Tem alternativas → objetiva

    gabarito = str(questao.get("gabarito", "")).strip().upper()
    # Se o gabarito é uma única letra A-E, provavelmente é objetiva sem alternativas marcadas
    if gabarito in ("A", "B", "C", "D", "E"):
        return False

    return True  # Sem alternativas e gabarito não é letra → discursiva
