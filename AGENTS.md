# Regras do Projeto MathAI

## 1. Versões e Modelos da API do Gemini
- **Modelos Primários Recomendados**:
  - `gemini-flash-lite-latest` (Padrão 1): Latência < 0.6s, 100% de estabilidade no Free Tier, suporte completo a Visão Multimodal (OCR de cadernos/provas) e `response_schema` (JSON).
  - `gemini-3.5-flash-lite` (Padrão 2): Altamente estável, excelente para avaliação matemática passo a passo e diagnósticos pedagógicos.
- **Modelos de Fallback**:
  - `gemini-3-flash-preview`: Estável, utilizado caso os modelos lite sofram indisponibilidade pontual.
  - `gemini-3.6-flash`: Utilizar apenas como fallback secundário devido a picos intermitentes de alta demanda.
- **Modelos Proibidos / Inoperantes**:
  - **NUNCA utilize** `gemini-1.5-*` (`gemini-1.5-pro`, `gemini-1.5-flash`) nem `gemini-2.5-*` (`gemini-2.5-flash`), pois estão descontinuados e retornam erro `404 NOT_FOUND`.
  - **NÃO utilize** `gemini-3.7-flash` ou `gemini-3.8-flash`, pois retornam `503 UNAVAILABLE` com alta frequência devido a sobrecarga nos servidores da Google.
  - **NÃO utilize** `gemini-pro-latest` como padrão no Free Tier, pois ele esgota a cota imediatamente com erro `429 RESOURCE_EXHAUSTED`.

## 2. Limites de Quota, Faturamento e Tratamento de Erros
- **Diferenciação de Códigos de Erro**:
  - `402 RESOURCE_EXHAUSTED` (`prepayment credits are depleted`): Ocorre quando a chave pertence a um projeto configurado em modo Pay-As-You-Go, mas o saldo pré-pago está zerado ($0.00). O sistema deve alertar o usuário para recarregar créditos no Google Cloud Billing ou alternar para um projeto puramente Free Tier no Google AI Studio.
  - `429 RESOURCE_EXHAUSTED`: Limite de requisições por minuto (RPM) ou diário (RPD) atingido. Recomenda-se aguardar ou alternar a chave.
  - `503 UNAVAILABLE`: Servidores Google temporariamente sobrecarregados. O cliente da aplicação (`src/ai/evaluator.py`) deve realizar fallback automático para os modelos `flash-lite`.
- **Processamento em Lote (Batch Scripts)**:
  - Scripts pesados de ingestão de banco de questões (`ingest_cg.py`, etc.) NÃO devem ser executados no Free Tier sem aviso prévio, pois consomem rapidamente o limite diário.

## 3. Web Scraping e Cloudflare
- Sites como o SSPM (Marinha Oficial) e PCI Concursos utilizam Cloudflare Turnstile, resultando em erros constantes de `403 Forbidden` ao tentar aplicar automação via scripts Python puros (`requests`/`BeautifulSoup`). Priorizar outras fontes de raspagem sem proteções anti-bot agressivas.

## 4. UI e Estilização (Streamlit/Frontend)
- **Modos Dark e Light**: Sempre preste atenção ao contraste e esquema de cores ao adicionar novos elementos na UI. Garanta que textos, fundos e itens selecionados não fiquem ilegíveis (ex: texto claro em fundo claro ou texto escuro em fundo escuro) dependendo do tema ativo pelo usuário. Utilize variáveis de tema responsivas ou cores neutras de bom contraste.
- **Responsividade e Modo Tablet**: Em telas médias e tablets, garanta que barras de navegação superior, numeração de questões e botões de ação não fiquem sobrepostos ou agrupados de forma truncada.

## 5. Alucinação de Subagentes em Tarefas Bloqueadas (Cloudflare)
- **Bloqueios Intransponíveis**: O Cloudflare Turnstile (usado em sites da Marinha/SSPM e PCI Concursos) é intransponível para robôs headless e subagentes nativos.
- **Prevenção de Alucinação**: Se um subagente for instruído a baixar arquivos desses sites, ele poderá **alucinar o sucesso**. Ele pode baixar a página HTML de bloqueio (403) e salvá-la como .pdf, ou simplesmente listar nomes de arquivos fictícios dizendo que o download terminou.
- **Protocolo**: NUNCA utilize subagentes para tentar burlar o Cloudflare e SEMPRE audite o tamanho/conteúdo dos arquivos baixados por scripts antes de considerar uma tarefa de extração concluída. Aceite a limitação técnica e direcione o usuário para o download manual.
