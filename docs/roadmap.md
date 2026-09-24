# MathAI — Roadmap 🚧

O desenvolvimento do MathAI está organizado em etapas. A prioridade fundamental foi estipulada em construir uma base confiável de dados e infraestrutura antes de avançar para modelos estocásticos mais sofisticados de Machine Learning e sistemas preditivos.

**Legenda:**
- 🟢 Implementado
- 🟡 Em desenvolvimento / Refinamento
- 🟠 Objetivo futuro (Médio prazo)
- 🔴 Objetivo futuro (Longo prazo)
- 🔵 Produto Final

---

## 🟢 Fase 1 — Fundação (Dados e Infraestrutura)
A base tecnológica que sustenta o sistema.
- [x] Estrutura relacional do banco
- [x] SQLite (Local Staging)
- [x] Turso (Cloud Database)
- [x] Modelagem multiusuário e Autenticação
- [x] Banco de questões
- [x] Registro de tentativas
- [x] Perfil de desempenho por tópico
- [x] Repetição espaçada
- [x] Estrutura de consentimento (LGPD)

## 🟢 Fase 2 — Ingestão e ETL (Construção do acervo)
O pipeline híbrido (Offline-First) de mineração de documentos.
- [x] Ingestão de MathNet
- [x] Ingestão de EFOMM
- [x] Ingestão de ESA
- [x] Ingestão de CEDERJ (Notion)
- [x] Ingestão de ENEM
- [x] Parsers para diferentes formatos (Regex / MuPDF)
- [x] Extração de texto e Extração de imagens
- [x] Normalização de metadados
- [x] Processamento cirúrgico de LaTeX via IA
- [x] Deduplicação
- [x] **Melhorias de Pipeline:**
  - [x] Pipeline totalmente resumível
  - [x] Sistema de retry/backoff
  - [x] Validação automática
  - [ ] Monitoramento contínuo de falhas
  - [ ] Melhor estimativa de dificuldade nativa

## 🟡 Fase 3 — Dados de Aprendizagem
A consolidação de instrumentação do aluno e o comportamento da plataforma.
- **Implementado:**
  - Registro de tentativas, Acerto/erro
  - Tempo de resolução e Confiança
  - Resolução em texto / Justificativa
  - Registro de dicas e IA semântica
- **Próximos passos (Em progresso):**
  - Melhorar taxonomia de erros e classificação de estratégias
  - Criar métricas temporais em dashboard avançado para o aluno
  - Separar permanentemente dados observados e anotações derivadas
  - Criar dataset analítico exportável para a Fase 4 (ML)

## 🟠 Fase 4 — Machine Learning
**Objetivo principal:** Construir modelos capazes de estimar desempenho a partir do histórico do aluno ($P(\text{acerto}\mid\text{aluno},\text{questão},\text{contexto})$).
- [ ] Baseline estatístico
- [ ] Logistic Regression
- [ ] Random Forest / Gradient Boosting / XGBoost
- [ ] Validação temporal
- [ ] Feature engineering
- [ ] Análise de importância das variáveis

## 🟠 Fase 5 — Modelo do Aluno
Evoluir de métricas simples para uma representação dinâmica e tridimensional do conhecimento matemático do estudante.
- [ ] *Knowledge Tracing* (Rastreamento do Conhecimento)
- [ ] Estimativa de domínio por tópico
- [ ] Modelagem estatística da dificuldade das questões (Item Response Theory)
- [ ] Evolução temporal do conhecimento
- [ ] Perfil matemático e de aprendizagem

## 🟠 Fase 6 — Recomendação Adaptativa
Utilizar a inferência do Modelo do Aluno (Fase 5) para decidir o próximo conteúdo ou questão na interface.
- **Fluxo Almejado:** `Histórico ➔ Modelo ➔ Estado Atual ➔ Sistema de Recomendação ➔ Próxima Questão`
- [ ] Recomendação baseada em regras vs ML
- [ ] Políticas de *Exploration vs. Exploitation* (Contextual Bandits)
- [ ] Personalização de revisões

## 🔴 Fase 7 — IA Multimodal
Expandir radicalmente a análise de resoluções discursivas (substituindo limitações do formato puramente objetivo).
- [ ] Upload de resolução (Imagem escrita à mão / Caderno)
- [ ] Análise multimodal e Transcrição LaTeX
- [ ] Identificação estruturada de etapas
- [ ] Diagnóstico localizado preciso do erro e análise metodológica
- [ ] Dicas Socráticas iterativas (Chat)

## 🔴 Fase 8 — Tutor Adaptativo
Integrar e aglutinar os componentes e bancos num único Tutor Autônomo capaz de modular o tipo de intervenção.
- **Modos de operação futuros:**
  - Aprender
  - Praticar
  - Corrigir (Entender meus erros)
  - Reaprender
  - Expandir

## 🔵 Fase 9 — Produto
Transformar toda a infraestrutura acadêmica/laboratorial em uma plataforma comercial EdTech escalável.
- [ ] Trilhas personalizadas (Videoaulas, PDFs, Flashcards)
- [ ] Conteúdo dinamicamente recomendado
- [ ] Sistema de contas e sincronização avançada
- [ ] Infraestrutura em nuvem escalável

---

## 🧭 Princípios Essenciais do Roadmap

Nenhuma meta sobrepõe estas diretrizes básicas no repositório do MathAI:
1. **Dados antes de modelos sofisticados:** Antes de aplicar modelos complexos, é necessário possuir dados inquestionáveis.
2. **Determinístico antes de IA:** O que pode ser resolvido com Regex, não exige custo e latência de IA.
3. **Evidência antes de interpretação:** Dados observados e factuais não se misturam com inferências da IA.
4. **Validação antes de complexidade:** Um modelo avançado não é automaticamente melhor que um condicional (`if/else`) certeiro.
5. **Aprender construindo:** Cada etapa funciona como uma lição prática nas engenharias do projeto.
