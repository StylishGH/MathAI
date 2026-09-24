# Desafios de Engenharia

Desenvolver a estrutura do MathAI e alimentar sua base de dados não foi algo trivial. O projeto enfrentou diversos problemas de integração e limite computacional de serviços externos. O foco desta seção é documentar os incidentes (e a resolução arquitetural) para mostrar como o projeto evoluiu para sua robustez atual.

## 01 — Limites de API e Retries (Erro 429)

* **Problema:** Ao transacionar lotes de questões extraídas via Python para que o Gemini as convertesse para LaTeX, começamos a receber constantes falhas do tipo `429 RESOURCE_EXHAUSTED`.
* **Diagnóstico:** O modelo `gemini-3.5-flash-lite` possui uma cota diária alta (1.500 RPD), porém, uma limitação aguda de RPM (Requests Per Minute). Como o script Python executava as chamadas via API de forma quase instântanea, o gargalo de **15 requisições por minuto** do *Free Tier* era atingido em menos de cinco segundos.
* **Solução e Resultado:** Implementamos empacotamento em *batches* (enviando 5 questões na mesma requisição) e aplicamos estratégias de `time.sleep` (delay de 5 a 20 segundos). Com isso, contornamos as janelas de bloqueio sem esgotar as cotas.

## 02 — Parsing Crítico: JSON + LaTeX

* **Problema:** Os retornos em JSON do LLM não conseguiam ser processados pelo sistema local (lançando erros como `Invalid \escape`).
* **Causa:** O modelo da IA inseria símbolos LaTeX nativos em strings do JSON, gerando barras invertidas não duplas. Por exemplo, `\frac` gerava a quebra porque `\f` é caracter inválido em JSON estrito (diferente de `\n`).
* **Solução:** Aplicamos `strict=False` na conversão do Python e inserimos expressões para sanitizar o bloco de resposta (`text_json.replace('\\\\', '\\\\\\\\')`) e proteger os símbolos da formatação LaTeX na estrutura de metadados.

## 03 — Inconsistências de Schema e Exceções Silenciosas

* **Problema:** Durante o processamento das provas do CEDERJ e primeiras execuções da EFOMM, embora as requisições consumissem tempo, absolutamente **0 questões** eram salvas no banco.
* **Investigação:** O log dos scripts suprimia as exceções em blocos `try/except`. Ao analisarmos as falhas brutas do SQLite (`OperationalError`), percebemos que o código tentava realizar inserções em uma coluna `alternativas`. Porém, o schema de banco moderno do app havia sido alterado e exigia o formato consolidado na string.
* **Correção:** Os scripts de ingestão foram reescritos. As alternativas (`(A), (B), (C)`) agora são concatenadas diretamente no corpo do campo `enunciado`.

## 04 — Desincronização: Local DB vs Turso Cloud

* **Problema:** Cerca de 200 novas questões haviam sido processadas com sucesso, mas o portal (Frontend no Streamlit) exibia instâncias com listas de olimpíadas aleatórias (*APMO, National XXX OMA*). Nenhuma das questões geradas localmente aparecia na interface.
* **Causa:** A aplicação web era orientada via LibSQL para o banco na nuvem (Turso DB), enquanto os extratores (ingestão) faziam chamadas *hardcoded* para o banco local (`data/mathai.db`). As lógicas estavam bifurcadas. O Turso havia sido poluído no passado por scripts de web-scraping brutos.
* **Arquitetura Corrigida:** Modificamos a conexão nos scripts de ingestão (CEDERJ) para apontar ao Turso e criamos um *sync worker* (`sync_to_turso.py`) que realizou a limpa nas anomalias da nuvem e replicou o espelho saudável e consistente validado no ambiente offline.

## 05 — OCR em PDFs Históricos (A Maldição Romana)

* **Problema:** Apesar do pipeline funcionar imaculadamente nas provas da EFOMM 2023-2026, as provas antigas (2018 a 2021) rendiam **0 extrações**.
* **Casos Encontrados:** Dois fatores surpreenderam:
  1. A prova do 1º Dia (Inglês) e 2º Dia (Matemática) dessas edições eram publicadas em um PDF aglutinado gigante. Como o Regex procurava os números `1 a 20`, as questões de inglês consumiam o sequenciamento.
  2. O software de OCR converteu o cabeçalho original ("1ª Questão") para padrões bizarros, gerando o infame "Ia Questão" (onde `1` foi lido como o número romano `I` maiúsculo).
* **Parser Final:** O Regex foi atualizado (`[0-9lI]{1,2}`) e implementou suporte a caracteres corrompidos (`l` ou `I` no lugar de `1`). Além disso, programou-se uma varredura semântica: a extração de questões só desperta quando o Python lê fisicamente a string "MATEMÁTICA" no PDF, blindando o banco de inglês e outras matérias não relacionadas.

## 06 — O Custoso (e Irreversível) Erro de Acreditar em LLMs (Ground Truth)

* **O Desafio:** A primeira intenção de uso para os LLMs no app consistia em solicitar resoluções, diagnósticos pedagógicos e classificações exatas das questões, armazenando esses resultados junto aos *logs* dos alunos.
* **Solução:** Transformamos isso num *princípio arquitetural*. Compreendemos a longo prazo o perigo disso: "A IA é uma ferramenta de anotação/análise e não *ground truth* (verdade absoluta)". Separamos a tabela de banco para que os dados baseados em evidência factual permaneçam imaculados para treinarmos nossos modelos de Machine Learning (Fases 4+ do projeto) em cima de certezas e fatos da vida real, relegando a inferência ruidosa da IA apenas à sugestões temporárias de apoio cognitivo.
