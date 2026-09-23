"""
Módulo de Tradução e Normalização Matemática via Google Gemini.
Especializado em traduzir problemas de matemática preservando 100% da sintaxe LaTeX,
estruturando os metadados (matéria, tópico, dificuldade 1-5, estratégias) e gerando hashes para deduplicação.
"""

import json
import hashlib
from google.genai import types
from src.ai.client import criar_cliente_gemini, tem_chave_configurada


PROMPT_SISTEMA_TRADUTOR = """Você é um Tradutor e Curador Especialista em Matemática Olímpica e Acadêmica do MathAI.
Sua missão é traduzir enunciados matemáticos de outras línguas (principalmente Inglês) para Português Brasileiro formal e natural.

DIRETRIZES CRÍTICAS:
1. PRESERVAÇÃO DE LATEX: NUNCA altere comandos ou fórmulas LaTeX ($...$ ou $$...$$). Não mude nomes de variáveis, matrizes ou notações (ex: \\frac, \\sqrt, \\alpha, \\mathbb{R}).
2. TERMINOLOGIA BRASILEIRA: Use os termos matemáticos formais adotados no Brasil (ex: "right triangle" -> "triângulo retângulo", "coprime" -> "primos entre si", "slope" -> "coeficiente angular").
3. ESTRUTURAÇÃO: Categorize a matéria em: 'Geometria Plana', 'Geometria Espacial', 'Álgebra', 'Teoria dos Números', 'Combinatória' ou 'Cálculo'.
4. DIFICULDADE (1 a 5):
   - 1: Fácil / Ensino Fundamental / Base ESA
   - 2: Médio / Ensino Médio / ENEM / EEAR
   - 3: Difícil / Vestibular Tradicional (FUVEST) / AFA
   - 4: Muito Difícil / Olimpíada Nacional / ITA / IME
   - 5: Extremo / Desafio Internacional / IMO / Putnam
5. RESPOSTA EM JSON: Retorne EXCLUSIVAMENTE um objeto JSON válido.
"""


def gerar_hash_texto(texto: str) -> str:
    """Gera um hash MD5 único a partir do texto limpo para evitar duplicatas no banco."""
    texto_limpo = " ".join(texto.strip().lower().split())
    return hashlib.md5(texto_limpo.encode("utf-8")).hexdigest()


def traduzir_questao_matematica(
    enunciado_original: str,
    gabarito_original: str | None = None,
    banca_original: str | None = None,
    ano_original: int | None = None,
    categoria_sugerida: str | None = None,
    imagem_bytes: bytes | None = None,
    mime_type: str = "image/png"
) -> dict | None:
    """
    Traduz um enunciado matemático usando o Gemini, preservando o LaTeX
    e gerando a estrutura completa pronta para inserção no banco de dados.
    Suporta modo multimodal quando imagem_bytes é fornecido.
    """
    if not tem_chave_configurada():
        raise RuntimeError("Chave de API do Gemini não configurada! Adicione sua chave no .env ou na barra lateral.")

    client = criar_cliente_gemini()
    if not client:
        raise RuntimeError("Não foi possível inicializar o cliente do Gemini.")

    hash_id = gerar_hash_texto(enunciado_original)

    instrucao_imagem = ""
    if imagem_bytes:
        instrucao_imagem = """
NOTA SOBRE A IMAGEM ANEXADA:
A questão possui uma figura/diagrama anexada. Analise a figura e garanta que a tradução em português
mantenha total coerência com as letras dos vértices (A, B, C...), ângulos, coordenadas cartesianas,
medidas e anotações visuais presentes na imagem. Se o texto em inglês fizer menções como "in the figure below",
traduza naturalmente como "na figura abaixo" ou "na figura a seguir".
"""

    prompt_usuario = f"""Traduza e estruture a seguinte questão de matemática para o formato padrão do MathAI:
{instrucao_imagem}
ENUNCIADO ORIGINAL:
{enunciado_original}

GABARITO ORIGINAL: {gabarito_original if gabarito_original else 'Não fornecido (indique ou deduza se possível)'}
BANCA/ORIGEM: {banca_original if banca_original else 'Desconhecida'}
ANO: {ano_original if ano_original else 'null'}
CATEGORIA INFORMADA: {categoria_sugerida if categoria_sugerida else 'Detectar automaticamente'}

Retorne no formato JSON:
{{
  "materia": "Geometria Plana | Álgebra | Teoria dos Números | etc",
  "topico": "Tópico específico (ex: Semelhança de Triângulos, Equações Diofantinas)",
  "subtopico": "Subtópico ou Teorema específico (ou null)",
  "dificuldade": 1 a 5,
  "enunciado_pt": "Enunciado perfeitamente traduzido em português com LaTeX $...$ intacto",
  "gabarito": "Gabarito final ou expressão esperada",
  "estrategias_esperadas": ["Estratégia 1", "Estratégia 2"],
  "banca": "{banca_original or 'Internacional'}",
  "ano": {ano_original or 'null'}
}}
"""

    conteudos = []
    if imagem_bytes:
        tipo_final = mime_type if mime_type else "image/png"
        conteudos.append(types.Part.from_bytes(data=imagem_bytes, mime_type=tipo_final))
    conteudos.append(prompt_usuario)

    config = types.GenerateContentConfig(
        system_instruction=PROMPT_SISTEMA_TRADUTOR,
        response_mime_type="application/json",
        temperature=0.2  # Baixa temperatura para manter a fidelidade matemática
    )

    # Modelos recomendados em ordem de preferência (ativos na API)
    modelos = [
        "models/gemini-3.6-flash",
        "models/gemini-3.7-flash",
        "models/gemini-3.8-flash",
        "models/gemini-3.5-flash",
        "models/gemini-3.1-flash-lite"
    ]

    resposta = None
    max_tentativas = 3

    for tentativa in range(1, max_tentativas + 1):
        for mod in modelos:
            try:
                resposta = client.models.generate_content(
                    model=mod,
                    contents=conteudos,
                    config=config
                )
                if resposta and resposta.text:
                    break
            except Exception as e:
                erro_str = str(e).lower()
                # Se for erro de cota/limite de requisições, aguarda antes de tentar novamente
                if "429" in erro_str or "resource_exhausted" in erro_str or "quota" in erro_str:
                    tempo_espera = 25 * tentativa
                    print(f"\n⏳ Limite de requisições atingido. Aguardando {tempo_espera}s para a API liberar...")
                    import time
                    time.sleep(tempo_espera)
                continue

        if resposta and resposta.text:
            break

    if not resposta or not resposta.text:
        return None

    try:
        dados = json.loads(resposta.text.strip())
        dados["hash_original"] = hash_id
        return dados
    except json.JSONDecodeError:
        return None

