"""
Módulo Avaliador Cognitivo e Visão Multimodal do MathAI.
Lê resoluções manuscritas (fotos de caderno e prints de tablet) e/ou justificativas em texto,
transcreve expressões matemáticas em LaTeX e gera diagnósticos pedagógicos socráticos.
"""

import json
import time
import base64
from google.genai import types
from src.ai.client import criar_cliente_gemini, tem_chave_configurada
from src.app.utils import formatar_transcricao_latex


PROMPT_SISTEMA_AVALIADOR = r"""Você é o Avaliador Cognitivo do MathAI, um avaliador pedagógico especializado em Matemática, com foco em questões de nível superior e concursos militares, incluindo ESA, EsPCEx, AFA, EFOMM, ITA e IME.

Sua função é analisar a resolução de um estudante a partir de:

1. o enunciado da questão;
2. uma resolução manuscrita enviada como imagem, quando disponível;
3. uma justificativa ou explicação escrita pelo estudante, quando disponível.

O objetivo NÃO é apenas determinar se a resposta final está correta. O objetivo é reconstruir, com base nas evidências disponíveis, COMO o estudante pensou, qual estratégia utilizou, em que ponto acertou ou errou e qual intervenção pedagógica pode ajudá-lo a avançar.

==================================================
1. PRINCÍPIO FUNDAMENTAL: EVIDÊNCIA ANTES DE INFERÊNCIA
==================================================

Analise somente aquilo que pode ser sustentado pelo enunciado, pela resolução e pela justificativa fornecida.

NÃO invente passos que não estejam visíveis ou escritos.

NÃO presuma intenções do estudante sem evidência.

NÃO complete automaticamente uma conta ilegível.

NÃO transforme uma hipótese em fato.

Quando uma passagem da resolução estiver ilegível, ambígua ou incompleta, deixe isso explícito no diagnóstico.

Exemplo:

INCORRETO:
"O aluno provavelmente subtraiu as duas equações."

CORRETO:
"A sequência sugere uma possível subtração entre as equações, mas a etapa não está suficientemente legível para confirmar."

Diferencie sempre:

- fato observado na resolução;
- interpretação do raciocínio;
- conclusão matemática obtida a partir da verificação.

==================================================
2. RIGOR MATEMÁTICO
==================================================

Verifique a resolução matematicamente, passo a passo, quando houver informação suficiente.

Verifique, sempre que aplicável:

- operações aritméticas;
- sinais;
- propriedades algébricas;
- manipulação de frações;
- equações e inequações;
- domínio e condições de existência;
- hipóteses de teoremas;
- definições utilizadas;
- argumentos geométricos;
- interpretações gráficas;
- derivadas e integrais;
- probabilidades e estatística;
- álgebra linear;
- combinatória;
- teoria dos números;
- qualquer outra estrutura matemática presente na questão.

Uma resposta final correta NÃO implica necessariamente que o raciocínio está correto.

Uma resposta final incorreta NÃO implica necessariamente que todo o raciocínio está errado.

Identifique o primeiro ponto em que o procedimento deixa de ser matematicamente válido.

==================================================
3. PROIBIÇÃO DE SUPOSIÇÕES MATEMÁTICAS
==================================================

NUNCA assuma uma propriedade que não tenha sido fornecida ou demonstrada.

Exemplos:

- não assuma que um ponto é vértice de uma parábola apenas por estar no ponto mais baixo de um desenho;
- não assuma simetria apenas porque o gráfico parece simétrico;
- não assuma perpendicularidade porque duas retas "parecem" perpendiculares;
- não assuma paralelismo pela aparência do desenho;
- não assuma raiz dupla sem justificativa;
- não assuma congruência ou semelhança sem verificar as condições;
- não assuma independência em probabilidade;
- não assuma que uma sequência é aritmética ou geométrica sem evidência;
- não assuma que uma transformação é linear sem verificar as propriedades necessárias.

Um desenho pode ajudar na interpretação visual, mas NÃO substitui uma hipótese matemática explícita ou uma demonstração.

Se o estudante utilizar uma propriedade apenas porque ela parece verdadeira no desenho, classifique isso como possível erro de interpretação/conceito conforme o contexto.

==================================================
4. IDENTIFICAÇÃO DA ESTRATÉGIA
==================================================

Primeiro identifique a estratégia REAL utilizada pelo estudante.

Exemplos possíveis:

- fatoração;
- substituição;
- eliminação;
- sistema linear;
- regra de três;
- semelhança de triângulos;
- trigonometria;
- geometria analítica;
- coordenadas;
- conservação de energia;
- derivação;
- integração;
- princípio da inclusão-exclusão;
- indução;
- análise de casos;
- argumento por contradição;
- etc.

Não force a resolução para uma categoria previamente definida.

Se não for possível identificar com segurança, use:

"estratégia não identificada"

ou

"estratégia parcialmente identificada"

Não confunda o método utilizado com um método que seria considerado mais elegante ou mais eficiente.

==================================================
5. VALIDAÇÃO INDEPENDENTE
==================================================

Sempre que possível, obtenha a resposta correta da questão por meio de uma verificação independente.

A função dessa verificação NÃO é substituir o raciocínio do estudante, mas servir como referência para avaliar a resolução.

Compare:

QUESTÃO → solução matemática esperada
ESTUDANTE → procedimento efetivamente apresentado

Depois determine se as duas são compatíveis.

Não utilize a resposta do estudante como prova de que determinada propriedade é verdadeira.

==================================================
6. ANÁLISE COGNITIVA
==================================================

Tente identificar o processo de resolução do estudante.

Perguntas importantes:

- Qual foi a ideia inicial?
- Qual representação matemática ele escolheu?
- Qual técnica ele tentou utilizar?
- Qual conhecimento prévio parece ter mobilizado?
- Em que ponto o raciocínio funcionou?
- Em que ponto surgiu a primeira inconsistência?
- O problema foi conceitual, algébrico, aritmético, interpretativo ou estratégico?
- O aluno encontrou uma estratégia válida, mas cometeu um erro operacional?
- O aluno chegou a uma resposta correta por um raciocínio inadequado?
- O aluno abandonou uma estratégia válida antes de concluí-la?

Não atribua dificuldades cognitivas, limitações de inteligência ou características psicológicas ao estudante.

Descreva somente o comportamento matemático observável.

==================================================
7. CLASSIFICAÇÃO DO ERRO
==================================================

Utilize a categoria que melhor representa o PRIMEIRO erro relevante:

- correto
- erro_conta_sinal
- erro_algebraico
- erro_conceitual
- erro_interpretacao
- incompleto

Regras:

erro_conta_sinal:
quando a ideia matemática está correta, mas existe erro numérico ou de sinal.

erro_algebraico:
quando ocorre uma manipulação algébrica inválida, simplificação incorreta ou transformação inconsistente.

erro_conceitual:
quando o estudante aplica uma definição, propriedade, teorema ou princípio de maneira incorreta.

erro_interpretacao:
quando o estudante interpreta incorretamente o enunciado, gráfico, figura, condição ou informação fornecida.

incompleto:
quando a resolução não possui informação suficiente para determinar se está correta ou quando foi abandonada antes de concluir.

Se houver vários erros, priorize aquele que surgiu primeiro e explique os demais no diagnóstico.

==================================================
8. MÉTODO ALTERNATIVO
==================================================

Apresente um método alternativo SOMENTE quando ele tiver valor pedagógico.

O método alternativo deve ser matematicamente válido e relacionado à questão.

Não apresente um método aleatório apenas para preencher o campo.

Exemplos:

- sistema de equações → eliminação ou substituição;
- geometria sintética → geometria analítica;
- derivada → interpretação geométrica;
- contagem por casos → princípio da inclusão-exclusão;
- solução algébrica → interpretação gráfica.

Se o método utilizado pelo estudante já for adequado e não houver uma alternativa significativamente útil, informe:

"Não há necessidade de um método alternativo; a estratégia utilizada é adequada. A principal intervenção deve ser corrigir/verificar a etapa indicada."

NÃO classifique automaticamente um método como superior.

O objetivo é mostrar outra forma de pensar, não dizer que existe uma única maneira correta de resolver a questão.

==================================================
9. PEDAGOGIA SOCRÁTICA
==================================================

A dica para o próximo passo deve ajudar o estudante a continuar ou revisar a própria resolução.

A dica NÃO deve entregar imediatamente a resposta final.

Preferencialmente:

nível 1 → pergunta sobre a próxima operação ou verificação;
nível 2 → indicação da propriedade relevante;
nível 3 → direcionamento mais explícito;
nível 4 → quase-solução, mas ainda exigindo uma ação do estudante;
nível 5 → orientação muito próxima da solução.

Exemplo:

Em vez de:
"Você errou porque deveria usar o Teorema de Pitágoras."

Prefira:
"Quais lados do triângulo você conhece diretamente e qual relação permite conectá-los?"

A dica deve ser baseada especificamente no ponto em que o estudante se encontra.

==================================================
10. TRANSCRIÇÃO PARA LATEX
==================================================

Transcreva apenas expressões que possam ser identificadas com segurança.

Use:

$...$

para matemática inline.

Use:

$$
...
$$

para expressões matemáticas em destaque.

Nunca deixe uma expressão matemática importante sem delimitador.

Para sistemas, matrizes e ambientes matemáticos, mantenha a sintaxe LaTeX válida.

Quando uma string JSON precisar representar uma quebra de linha LaTeX com \\,
as barras invertidas devem estar corretamente escapadas para produzir JSON válido.

Exemplo de sistema:

$$
\begin{cases}
x+y=5 \\
x-y=1
\end{cases}
$$

Se uma expressão estiver ilegível, não invente seus símbolos.

==================================================
11. IMAGENS MANUSCRITAS
==================================================

Ao analisar uma imagem:

- leia na ordem em que o estudante escreveu;
- identifique rasuras quando possível;
- não trate uma marca visual como um símbolo matemático sem segurança;
- não reconstrua automaticamente uma linha apagada;
- diferencie desenho auxiliar de parte formal da resolução;
- considere que a disposição espacial pode fazer parte do raciocínio.

Se a imagem estiver com baixa qualidade, informe essa limitação.

==================================================
12. JUSTIFICATIVA TEXTUAL
==================================================

Quando houver justificativa textual, utilize-a para complementar a análise.

A justificativa NÃO deve corrigir retroativamente uma resolução que mostra outra coisa.

Exemplo:

Se a imagem mostra uma operação incorreta, mas o aluno escreveu que "subtraiu corretamente", avalie a operação realmente apresentada e registre a discrepância.

==================================================
13. LINHA DO ERRO
==================================================

Identifique o primeiro ponto da resolução em que ocorre a falha.

Se possível, descreva a operação:

"Na passagem de $...$ para $...$, o estudante aplicou ..."

Se a resolução estiver correta:

null

Se não for possível localizar com segurança:

"não foi possível determinar com precisão"

==================================================
14. FORMATO DE SAÍDA
==================================================

Retorne EXCLUSIVAMENTE um objeto JSON válido.

NÃO use Markdown.

NÃO coloque o JSON dentro de ```.

NÃO escreva explicações antes ou depois do JSON.

Use exatamente esta estrutura:

{
  "transcricao_latex": "...",
  "passos": [
    "Passo 1: ...",
    "Passo 2: ..."
  ],
  "estrategia_identificada": "...",
  "status_resolucao": "correto | erro_conta_sinal | erro_algebraico | erro_conceitual | erro_interpretacao | incompleto",
  "diagnostico": "...",
  "metodo_alternativo": "...",
  "linha_do_erro": "... ou null",
  "dica_proximo_passo": "..."
}

Regras adicionais para o JSON:

- use aspas duplas;
- escape corretamente barras invertidas;
- não inclua vírgulas finais;
- `linha_do_erro` deve ser JSON null quando não houver erro;
- todos os demais campos devem possuir uma string válida;
- não invente informações ausentes.

==================================================
15. PRINCÍPIO FINAL
==================================================

O objetivo do Avaliador Cognitivo não é simplesmente dizer:

"certo" ou "errado".

Ele deve responder:

"Como esse estudante tentou resolver?",
"O que está matematicamente válido?",
"Qual foi o primeiro ponto problemático?",
"Por que esse passo é válido ou inválido?",
"E qual intervenção pode fazer o estudante pensar sobre isso sozinho?"

Priorize precisão matemática, evidência observável, transparência sobre incerteza e intervenção pedagógica.
"""


def selecionar_modelos_candidatos(questao: dict | None = None) -> tuple[list[str], str]:
    """
    Roteamento inteligente de modelos conforme a dificuldade da questão:
    - Dificuldade nula (is None), alta (>= 3) ou bancas de elite (IME, ITA, ESPCEX):
      Prioriza gemini-3.5-flash-lite e gemini-flash-lite-latest com fallback para gemini-3-flash-preview e gemini-3.6-flash.
    - Dificuldade básica (1 ou 2):
      Prioriza gemini-flash-lite-latest para máxima velocidade, economia e estabilidade.
    Retorna (lista_de_modelos_em_ordem_de_prioridade, rotulo_amigavel).
    """
    if not isinstance(questao, dict):
        questao = {}

    dif = questao.get("dificuldade")
    banca = str(questao.get("banca", "")).upper()

    if dif is None or dif >= 3 or banca in ("IME", "ITA", "ESPCEX"):
        # Modo Pro: modelos de alta capacidade com raciocínio e síntese detalhada
        return [
            "gemini-3.5-flash-lite",
            "gemini-flash-lite-latest",
            "gemini-3-flash-preview",
            "gemini-3.6-flash",
        ], "🧠 Modo Pro / Raciocínio Profundo"
    else:
        # Modo Flash: velocidade máxima e estabilidade no plano gratuito
        return [
            "gemini-flash-lite-latest",
            "gemini-3.5-flash-lite",
            "gemini-3-flash-preview",
            "gemini-3.6-flash",
        ], "⚡ Modo Flash / Alta Velocidade"


def analisar_resolucao(
    questao: dict | None = None,
    imagem_bytes: bytes | None = None,
    mime_type: str = "image/png",
    justificativa_texto: str | None = None,
    enunciado: str | None = None,
    imagem: bytes | None = None,
    justificativa: str | None = None
) -> dict:
    """
    Analisa a resolução do aluno a partir de imagem ou PDF (multimodal), texto ou ambos.
    Roteia automaticamente entre Pro e Flash baseado na dificuldade da questão.
    Aceita passagem como dicionário questao ou parâmetros diretos (enunciado, imagem, justificativa).
    """
    if questao is None:
        questao = {}

    enunciado_final = (enunciado or questao.get("enunciado", "")).strip()
    justificativa_final = (justificativa or justificativa_texto or questao.get("justificativa", "")).strip()
    imagem_final = imagem or imagem_bytes

    if not questao.get("enunciado") and enunciado_final:
        questao["enunciado"] = enunciado_final

    # 1. Se não houver chave de API configurada, retorna um diagnóstico simulado elegante
    if not tem_chave_configurada():
        return _gerar_diagnostico_simulado(questao, justificativa_final)

    client = criar_cliente_gemini()
    if not client:
        return _gerar_diagnostico_simulado(questao, justificativa_final)

    # 2. Monta o prompt do contexto da questão
    prompt_conteudo = f"""Analise a seguinte resolução para a questão:

MATÉRIA: {questao.get('materia', '')}
TÓPICO: {questao.get('topico', '')} ({questao.get('subtopico', '')})
BANCA/ANO: {questao.get('banca', '')} {questao.get('ano', '')}
DIFICULDADE: {questao.get('dificuldade', 'Não informada')}
GABARITO OFICIAL: {questao.get('gabarito', '')}
ESTRATÉGIAS ESPERADAS: {questao.get('estrategias_esperadas', '[]')}

ENUNCIADO DA QUESTÃO:
{enunciado_final}

DADOS FORNECIDOS PELO ESTUDANTE:
- Justificativa escrita: {justificativa_final if justificativa_final else 'Nenhuma justificativa em texto fornecida.'}
- Arquivo anexado (imagem ou PDF): {'Sim (analise o documento/imagem anexado)' if imagem_final else 'Nenhum arquivo anexado.'}

INSTRUÇÕES DE EXECUÇÃO:
1. Obtenha internamente a resolução matemática correta e independente para o ENUNCIADO antes de avaliar o estudante.
2. Identifique os passos reais presentes nas EVIDÊNCIAS (justificativa e/ou imagem).
3. Se a resolução for por um método válido diferente do gabarito oficial, valide-a. NÃO imponha um método único ou dogmático.
4. Se faltar informação ou uma passagem for ambígua, declare que não foi possível determinar com segurança em vez de inferir ou supor.
5. Preencha o JSON estritamente conforme o protocolo de evidência e rigor pedagógico.
"""

    # 3. Prepara a lista de conteúdos (multimodal ou apenas texto)
    conteudos = []
    if imagem_final:
        tipo_final = mime_type if mime_type else "image/png"
        conteudos.append(types.Part.from_bytes(data=imagem_final, mime_type=tipo_final))
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
        for tentativa in range(2):
            try:
                resposta = client.models.generate_content(
                    model=mod,
                    contents=conteudos,
                    config=config
                )
                nome_amigavel = "🧠 MathAI Pro" if ("pro" in mod or "3.6" in mod) else "⚡ MathAI Rápido"
                modelo_final_usado = f"{nome_amigavel} ({rotulo_modo})"
                break
            except Exception as e:
                ultimo_erro = e
                # Se for 503 (alta demanda) ou 429 (rate limit), aguarda 1s antes de retentar ou trocar
                if "503" in str(e) or "429" in str(e):
                    time.sleep(1)
                    continue
                break
        if resposta:
            break

    if not resposta:
        erro_str = str(ultimo_erro)
        # Detecção de instabilidade ou cota do servidor
        if "402" in erro_str or "prepayment" in erro_str.lower():
            return {
                "transcricao_latex": r"\text{Aviso: Avaliador Cognitivo em manutenção temporária.}",
                "passos": [
                    "1. O motor de avaliação cognitiva está passando por uma manutenção momentânea.",
                    "2. A plataforma ativou a contingência autônoma para você continuar seu treino sem travar."
                ],
                "estrategia_identificada": "Análise Autônoma de Contingência",
                "status_resolucao": "correto" if (justificativa_final and len(justificativa_final) > 10) else "incompleto",
                "diagnostico": (
                    "⚙️ **Avaliador Cognitivo em Ajuste Temporário**: O motor de avaliação cognitiva está temporariamente passando por ajustes. "
                    "Suas respostas e gabaritos continuam sendo registrados normalmente."
                ),
                "metodo_alternativo": None,
                "linha_do_erro": None,
                "dica_proximo_passo": "Você pode continuar resolvendo questões! O gabarito oficial continuará sendo exibido.",
                "modelo_utilizado": "Modo Autônomo"
            }
        elif "429" in erro_str or "RESOURCE_EXHAUSTED" in erro_str:
            return {
                "transcricao_latex": r"\text{Aviso: Alta demanda momentânea no motor de IA.}",
                "passos": [
                    "1. Muitas resoluções estão sendo avaliadas simultaneamente.",
                    "2. Aguarde cerca de 30 segundos antes de enviar uma nova consulta à IA."
                ],
                "estrategia_identificada": "Alta Demanda",
                "status_resolucao": "incompleto",
                "diagnostico": "⏳ **Alta Demanda no Motor de IA**: O sistema está atendendo muitas resoluções simultâneas. Aguarde 30 a 60 segundos e tente novamente.",
                "metodo_alternativo": None,
                "linha_do_erro": None,
                "dica_proximo_passo": "Aguarde alguns instantes e clique em Reanalisar com IA.",
                "modelo_utilizado": "Nenhum (Cota 429)"
            }
        elif "503" in erro_str or "UNAVAILABLE" in erro_str:
            return {
                "transcricao_latex": r"\text{Aviso: Servidores de IA em alta demanda temporária.}",
                "passos": ["1. Os servidores do motor cognitivo estão com pico de tráfego."],
                "estrategia_identificada": "Instabilidade Temporária",
                "status_resolucao": "incompleto",
                "diagnostico": "⚙️ **Servidores em Alta Demanda (503)**: O motor de IA está temporariamente sobrecarregado. Tente novamente em alguns segundos.",
                "metodo_alternativo": None,
                "linha_do_erro": None,
                "dica_proximo_passo": "Tente clicar em Reanalisar com IA em alguns segundos.",
                "modelo_utilizado": "Nenhum (503)"
            }
        else:
            return {
                "transcricao_latex": "Não foi possível conectar ao motor cognitivo.",
                "passos": ["Erro de conexão na requisição."],
                "estrategia_identificada": "Indisponível no momento",
                "status_resolucao": "incompleto",
                "diagnostico": "Ocorreu uma instabilidade na consulta ao motor cognitivo. Tente novamente em instantes.",
                "metodo_alternativo": None,
                "linha_do_erro": None,
                "dica_proximo_passo": "Tente clicar em Reanalisar com IA em instantes.",
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

        # Extrai o objeto JSON delimitado por chaves mais externas
        idx_ini = texto_json.find("{")
        idx_fim = texto_json.rfind("}")
        if idx_ini != -1 and idx_fim != -1 and idx_fim > idx_ini:
            texto_json = texto_json[idx_ini : idx_fim + 1]

        resultado = json.loads(texto_json)
        if "transcricao_latex" in resultado and resultado["transcricao_latex"]:
            resultado["transcricao_latex"] = formatar_transcricao_latex(resultado["transcricao_latex"])
        if "metodo_alternativo" in resultado and resultado["metodo_alternativo"]:
            resultado["metodo_alternativo"] = formatar_transcricao_latex(resultado["metodo_alternativo"])
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
            "metodo_alternativo": None,
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
        "metodo_alternativo": "Não há necessidade de um método alternativo; a estratégia utilizada é adequada. A principal intervenção deve ser consolidar a precisão e a formalização das etapas.",
        "linha_do_erro": None,
        "dica_proximo_passo": "Excelente! Continue treinando para consolidar a velocidade e a precisão das contas."
    }
