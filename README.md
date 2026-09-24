<div align="center">
  <h1>MathAI 🧠📐</h1>
  <p>Uma IA que aprende como você aprende Matemática para ajudar você a aprender melhor.</p>
</div>

O **MathAI** é um projeto pessoal que combina Matemática, Ciência de Dados, Machine Learning e Inteligência Artificial para construir uma plataforma de aprendizagem matemática personalizada.

O projeto também funciona como um laboratório prático para estudar engenharia de dados, processamento de documentos, bancos de dados, integração com APIs de IA e modelagem de comportamento de usuários.

## 🎯 Objetivo

Construir um tutor adaptativo capaz de evoluir um modelo de cada aluno a partir de dados como:
- Questões resolvidas;
- Acertos e erros;
- Tempo de resolução;
- Estratégias utilizadas;
- Confiança;
- Justificativas;
- Resoluções manuscritas;
- Interações com dicas.

A visão de longo prazo é utilizar esses dados para recomendação personalizada, *Knowledge Tracing*, análise de resoluções e modelos próprios de Machine Learning.

## 🏗️ Visão Geral Técnica

Uma decisão importante do projeto foi separar tarefas determinísticas de tarefas que exigem interpretação. 
- **Python** é utilizado para extração, parsing, limpeza, normalização, deduplicação e processamento.
- **IA** é utilizada principalmente em tradução matemática, análise de resoluções, diagnóstico e geração de feedback.

**Fluxo da Arquitetura:**
`Datasets / PDFs / Notion` ➔ `Python / ETL` ➔ `Limpeza + Normalização` ➔ `IA (apenas para tarefas semânticas)` ➔ `Dados estruturados` ➔ `SQLite / Turso` ➔ `Streamlit` ➔ `IA + Analytics + ML`

## 🛠️ Principais Tecnologias (Stack)

`Python` · `Pandas` · `NumPy` · `SQLite` · `Turso` · `Streamlit` · `Gemini API` · `Hugging Face` · `LaTeX/KaTeX` · `Git/GitHub`

## ✨ Principais Funcionalidades Implementadas

- **Ingestão Robusta offline-first:** Processamento de PDFs e arquivos Markdown (Notion) de bancas como EFOMM, ESA e CEDERJ com extração via Regex e OCR.
- **Normalização Matemática:** IA atuando cirurgicamente apenas para consertar encodings e traduzir fórmulas para LaTeX impecável.
- **Banco de Dados Híbrido:** Sincronização entre SQLite local (ambiente de extração) e banco Turso na nuvem (ambiente de produção).
- **Separação Epistemológica:** Diferenciação arquitetural entre "dados observados" (fatos brutos do aluno) e "dados derivados" (diagnósticos gerados pela IA).
- **Integração Front-Back:** Plataforma em Streamlit com testes, feedbacks formativos e sistema de login/consentimento de privacidade.

## 📖 Documentação

Para explorar a fundo as decisões e a implementação técnica, consulte os documentos abaixo:

- [**Arquitetura do Sistema**](docs/architecture.md): Como o sistema foi pensado, modelo de dados e fluxo de uso.
- [**Pipeline de Dados**](docs/data-pipeline.md): O trajeto dos dados desde o PDF até a estruturação no banco.
- [**Desafios de Engenharia**](docs/engineering-challenges.md): Problemas reais enfrentados (Rate Limits, OCR, Schema, etc) e como foram solucionados.
- [**Roadmap**](docs/roadmap.md): O plano de evolução do projeto (ML, Recomendação, Modelagem, Produto).

---

### 💡 Motivação

O MathAI nasceu da interseção entre Matemática, minha área de formação, e Machine Learning, área que venho estudando. Em vez de estudar essas tecnologias apenas de forma teórica, decidi construir um sistema real para aprender através de problemas concretos de: **dados ➔ engenharia ➔ IA ➔ modelagem ➔ produto**.

### 👨‍💻 Autor
**Guilherme Henrique Mendes**  
Licenciando em Matemática e estudando Ciência de Dados, Machine Learning e Inteligência Artificial.  
🔗 [GitHub](https://github.com/StylishGH)
