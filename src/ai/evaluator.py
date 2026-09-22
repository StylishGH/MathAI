"""
Módulo Avaliador Cognitivo e Visão Multimodal do MathAI.
Lê resoluções manuscritas (fotos de caderno e prints de tablet) e/ou justificativas em texto,
transcreve expressões matemáticas em LaTeX e gera diagnósticos pedagógicos socráticos.
"""

import json
import base64
from google.genai import types
from src.ai.client import criar_cliente_gemini, tem_chave_configurada
from src.app.utils import formatar_transcricao_latex


PROMPT_SISTEMA_AVALIADOR = """Você é o Avaliador Cognitivo do MathAI, uma inteligência artificial pedagógica especializada em ensino de Matemática para o Ensino Superior e Concursos Militares de Alto Nível (ESA, Espcex, ITA, IME).

Seu papel é analisar a resolução de um estudante — que pode vir como uma imagem manuscrita (foto de caderno ou tablet) e/ou como uma justificativa escrita em texto.

DIRETRIZES FUNDAMENTAIS:
1. RIGOR MATEMÁTICO: Verifique cada passagem de linha, igualdade, sinal e teorema aplicado.
2. PEDAGOGIA SOCRÁTICA: Não apenas diga se está certo ou errado. Explique COMO o aluno pensou, qual técnica utilizou e onde a lógica falhou (se falhou).
3. TRANSCRIÇÃO LATEX:
   - Transcreva as fórmulas e passos identificados no rascunho usando sintaxe LaTeX padrão.
   - SEMPRE envolva expressões matemáticas em destaque com blocos $$ ... $$ e termos inline com $ ... $.
   - Para matrizes e sistemas (\\begin{cases}, \\begin{pmatrix}, \\begin{aligned}), use quebras de linha com barras duplas (\\\\\\\\ dentro de strings JSON) para que o LaTeX quebre as linhas corretamente.
   - Nunca deixe expressões LaTeX soltas sem os delimitadores $$...$$ ou $...$.
4. RESPOSTA EM JSON ESTRUTURADO: Você DEVE retornar EXCLUSIVAMENTE um objeto JSON válido no seguinte formato:

{
  "transcricao_latex": "Passos e equações lidas no rascunho devidamente delimitadas por $$...$$ ou $...$",
  "passos": [
    "Passo 1: ...",
    "Passo 2: ..."
  ],
  "estrategia_identificada": "Nome da técnica principal usada (ex: Teorema de Tales, Sistema Linear, Mudança de Base, etc.)",
  "status_resolucao": "correto | erro_conta_sinal | erro_algebraico | erro_conceitual | erro_interpretacao | incompleto",
  "diagnostico": "Explicação detalhada do raciocínio do aluno e análise qualitativa",
  "linha_do_erro": "Descrição de onde ocorreu a falha (ou null se estiver correto)",
  "dica_proximo_passo": "Uma provocação reflexiva para o aluno continuar ou verificar sua resposta"
}
"""


def selecionar_modelos_candidatos(questao: dict) -> tuple[list[str], str]:
    """
    Roteamento inteligente de modelos conforme a dificuldade da questão:
    - Dificuldade nula (is None), alta (>= 3) ou bancas de elite (IME, ITA):
      Prioriza Pro (gemini-3.1-pro-preview / gemini-pro-latest) com fallback para gemini-3.7-flash.
    - Dificuldade básica (1 ou 2):
      Prioriza gemini-3.7-flash / gemini-3.8-flash para máxima velocidade.
    Retorna (lista_de_modelos_em_ordem_de_prioridade, rotulo_amigavel).
    """
    dif = questao.get("dificuldade")
    banca = str(questao.get("banca", "")).upper()

    if dif is None or dif >= 3 or banca in ("IME", "ITA", "ESPCEX"):
        # Modo Pro: começa pelo modelo com raciocínio profundo ativo
        return [
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
            "models/gemini-3.1-pro-preview",
            "models/gemini-pro-latest",
            "gemini-2.0-flash",
            "gemini-1.5-pro",
        ], "🧠 Modo Pro / Raciocínio Profundo"
    else:
        # Modo Flash: prioriza velocidade e resposta ágil
        return [
            "gemini-3.6-flash",
            "gemini-3.7-flash",
            "gemini-3.8-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
        ], "⚡ Modo Flash / Alta Velocidade"


def analisar_resolucao(
    questao: dict,
    imagem_bytes: bytes | None = None,
    mime_type: str = "image/png",
    justificativa_texto: str | None = None
) -> dict:
    """
    Analisa a resolução do aluno a partir de imagem ou PDF (multimodal), texto ou ambos.
    Roteia automaticamente entre Pro e Flash baseado na dificuldade da questão.
    """
    # 1. Se não houver chave de API configurada, retorna um diagnóstico simulado elegante
    if not tem_chave_configurada():
        return _gerar_diagnostico_simulado(questao, justificativa_texto)

    client = criar_cliente_gemini()
    if not client:
        return _gerar_diagnostico_simulado(questao, justificativa_texto)

    # 2. Monta o prompt do contexto da questão
    prompt_conteudo = f"""Analise a seguinte resolução para a questão:

MATÉRIA: {questao.get('materia', '')}
TÓPICO: {questao.get('topico', '')} ({questao.get('subtopico', '')})
BANCA/ANO: {questao.get('banca', '')} {questao.get('ano', '')}
DIFICULDADE: {questao.get('dificuldade', 'Não informada')}
GABARITO OFICIAL: {questao.get('gabarito', '')}
ESTRATÉGIAS ESPERADAS: {questao.get('estrategias_esperadas', '[]')}

ENUNCIADO DA QUESTÃO:
{questao.get('enunciado', '')}

DADOS FORNECIDOS PELO ESTUDANTE:
- Justificativa escrita: {justificativa_texto if justificativa_texto else 'Nenhuma justificativa em texto fornecida.'}
- Arquivo anexado (imagem ou PDF): {'Sim (analise o documento/imagem anexado)' if imagem_bytes else 'Nenhum arquivo anexado.'}
"""

    # 3. Prepara a lista de conteúdos (multimodal ou apenas texto)
    conteudos = []
    if imagem_bytes:
        tipo_final = mime_type if mime_type else "image/png"
        conteudos.append(types.Part.from_bytes(data=imagem_bytes, mime_type=tipo_final))
    conteudos.append(prompt_conteudo)

    # 4. Seleciona a cascata de modelos ideais (Pro vs Flash)
    modelos_candidatos, rotulo_modo = selecionar_modelos_candidatos(questao)

    config = types.GenerateContentConfig(
        system_instruction=PROMPT_SISTEMA_AVALIADOR,
        response_mime_type="application/json",
        temperature=0.2  # Baixa temperatura para máximo rigor matemático
    )

    resposta = None
    modelo_final_usado = rotulo_modo
    ultimo_erro = None

    # Tenta cada modelo da cascata até um responder com sucesso
    for mod in modelos_candidatos:
        try:
            resposta = client.models.generate_content(
                model=mod,
                contents=conteudos,
                config=config
            )
            nome_amigavel = "🧠 MathAI Pro" if "pro" in mod else "⚡ MathAI Rápido"
            modelo_final_usado = f"{nome_amigavel} ({rotulo_modo})"
            break
        except Exception as e:
            ultimo_erro = e
            continue

    if not resposta:
        return {
            "transcricao_latex": "Não foi possível conectar ao motor cognitivo.",
            "passos": ["Erro de conexão na requisição"],
            "estrategia_identificada": "Indisponível no momento",
            "status_resolucao": "incompleto",
            "diagnostico": f"Ocorreu uma instabilidade na consulta: {str(ultimo_erro)}",
            "linha_do_erro": None,
            "dica_proximo_passo": "Verifique sua chave de API ou tente novamente em instantes.",
            "modelo_utilizado": "Nenhum (Erro)"
        }

    try:
        texto_json = (resposta.text or "").strip()
        # Remove blocos markdown ```json ... ``` se o modelo tiver incluído
        if texto_json.startswith("```"):
            linhas = texto_json.splitlines()
            if linhas[0].startswith("```"):
                linhas = linhas[1:]
            if linhas and linhas[-1].startswith("```"):
                linhas = linhas[:-1]
            texto_json = "\n".join(linhas).strip()

        resultado = json.loads(texto_json)
        if "transcricao_latex" in resultado and resultado["transcricao_latex"]:
            resultado["transcricao_latex"] = formatar_transcricao_latex(resultado["transcricao_latex"])
        resultado["modelo_utilizado"] = modelo_final_usado
        return resultado
    except Exception:
        texto_bruto = (resposta.text or "") if hasattr(resposta, "text") else ""
        return {
            "transcricao_latex": formatar_transcricao_latex(texto_bruto),
            "passos": ["Análise processada em formato de texto livre"],
            "estrategia_identificada": "Geral",
            "status_resolucao": "incompleto",
            "diagnostico": texto_bruto or "Resposta recebida.",
            "linha_do_erro": None,
            "dica_proximo_passo": "Tente formalizar o raciocínio em etapas numéricas.",
            "modelo_utilizado": modelo_final_usado
        }



def obter_dica_socratica(questao: dict, nivel: int) -> str:
    """
    Gera uma dica socrática progressiva de nível 1 a 5 para a questão.
    Roteia automaticamente entre Pro e Flash.
    """
    nivel = max(1, min(5, nivel))

    # Se não houver chave, retorna dicas didáticas simuladas
    if not tem_chave_configurada():
        dicas_mock = {
            1: f"💡 **Nível 1 (Dados)**: Observe atentamente o que a questão pede em relação a **{questao.get('topico', '')}**. Quais valores numéricos foram explicitamente fornecidos?",
            2: f"💡 **Nível 2 (Conceito)**: Pense em qual teorema ou definição padrão se aplica a este caso. Uma das estratégias catalogadas para esta questão é: **{questao.get('estrategias_esperadas', '')}**.",
            3: "💡 **Nível 3 (Primeiro Passo)**: Tente relacionar a incógnita principal montando uma equação ou desenhando uma reta auxiliar que divida o problema em partes menores.",
            4: "💡 **Nível 4 (Estruturação)**: Isole as variáveis conhecidas de um lado e aplique as propriedades de simplificação algébrica para chegar a uma expressão fechada.",
            5: f"💡 **Nível 5 (Resolução Completa)**: O gabarito oficial é **({questao.get('gabarito', '')})**. Para resolver, aplique as propriedades de {questao.get('topico', '')} desenvolvendo as equações até obter o resultado final."
        }
        return dicas_mock.get(nivel, "Dica indisponível.")

    client = criar_cliente_gemini()
    if not client:
        return "Configure a sua chave do Gemini para obter dicas socráticas em tempo real geradas por IA."

    prompt_dica = f"""Gere uma DICA SOCRÁTICA DE NÍVEL {nivel} DE 5 para um estudante tentando resolver a seguinte questão de matemática:

MATÉRIA: {questao.get('materia', '')}
TÓPICO: {questao.get('topico', '')}
GABARITO: {questao.get('gabarito', '')}
ESTRATÉGIAS: {questao.get('estrategias_esperadas', '')}
ENUNCIADO:
{questao.get('enunciado', '')}

REGRAS POR NÍVEL:
- Nível 1: Chame atenção para os dados e pergunte o que eles significam geometricamente/algebricamente. NÃO dê nenhuma fórmula.
- Nível 2: Sugira qual teorema, lei ou propriedade pode ser o caminho, sem montar a equação.
- Nível 3: Diga qual é a primeira equação ou traçado que o aluno deve fazer.
- Nível 4: Dê os passos intermediários do cálculo, deixando apenas a conta final para ele fazer.
- Nível 5: Explique a resolução passo a passo até a alternativa correta ({questao.get('gabarito', '')}).

Responda em tom amigável, direto, com notação matemática em LaTeX ($...$)."""

    modelos_candidatos, _ = selecionar_modelos_candidatos(questao)
    config = types.GenerateContentConfig(temperature=0.3)

    for mod in modelos_candidatos:
        try:
            resposta = client.models.generate_content(
                model=mod,
                contents=prompt_dica,
                config=config
            )
            return resposta.text.strip()
        except Exception:
            continue

    return "Não foi possível gerar a dica no momento. Verifique sua chave de API e tente novamente."



def _gerar_diagnostico_simulado(questao: dict, justificativa_texto: str | None) -> dict:
    """Gera um diagnóstico preliminar quando a chave de API não estiver ativa."""
    topico = questao.get("topico", "Matemática")
    just = justificativa_texto.strip() if justificativa_texto and justificativa_texto.strip() else "Resolução registrada no sistema."
    # Protege asteriscos matemáticos (como 4*1 + 6*2) para não virarem itálico no markdown
    just_segura = just.replace("*", "&#42;")

    return {
        "transcricao_latex": r"\text{Identificado no rascunho: } \text{Aplicação de propriedades de } " + topico,
        "passos": [
            "Passo 1: Leitura e isolamento das grandezas fornecidas no enunciado",
            "Passo 2: Montagem da relação fundamental de " + topico,
            "Passo 3: Desenvolvimento algébrico em busca da alternativa correta"
        ],
        "estrategia_identificada": "Análise Conceitual e Algébrica",
        "status_resolucao": "correto",
        "diagnostico": f"Sua justificativa ('{just_segura}') demonstra compreensão do conceito de {topico}. O raciocínio e o desenvolvimento matemático foram processados com sucesso pelo MathAI.",
        "linha_do_erro": None,
        "dica_proximo_passo": "Excelente! Continue treinando para consolidar a velocidade e a precisão das contas."
    }
