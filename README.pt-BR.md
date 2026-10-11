<div align="center">
  <h1>Lemmas 📐</h1>
  <p><strong>Aprendizagem adaptativa construída em torno dos dados.</strong></p>
  <p>Uma plataforma de aprendizagem matemática que explora a interseção entre Engenharia de Dados, Ciência de Dados e IA aplicada.</p>
  <p><strong>🇧🇷 Português (Brasil)</strong> &nbsp;|&nbsp; <a href="./README.md">🇺🇸 English</a></p>
  <p><a href="https://lemmas-ochre.vercel.app/dashboard"><strong>🚀 Acesse o Lemmas ao vivo</strong></a></p>
  <p>
    <img src="https://img.shields.io/badge/Next.js-16-000000?logo=next.js" alt="Next.js 16" />
    <img src="https://img.shields.io/badge/FastAPI-API%20REST-009688?logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase" alt="Supabase / PostgreSQL" />
    <img src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python" alt="Python" />
    <img src="https://img.shields.io/badge/Status-Em%20desenvolvimento-yellow" alt="Em desenvolvimento" />
  </p>
</div>

---

## Por que o Lemmas?

O que uma plataforma de aprendizagem poderia descobrir se tratasse o processo de aprendizagem do aluno como dados estruturados, em vez de registrar apenas acertos e erros?

Dois alunos podem errar a mesma questão por motivos diferentes. Um pode não compreender o conceito; outro pode compreendê-lo, mas cometer um erro algébrico. Um sistema adaptativo precisa preservar a resolução realmente enviada, distingui-la da interpretação gerada por IA e permitir que o feedback ou a revisão humana corrijam essa interpretação.

O princípio central é:

> **Dado observado ≠ interpretação da IA ≠ dado validado.**

O Lemmas é um produto em evolução e um projeto prático de engenharia. O código atual se concentra em uma arquitetura web/API modular e em fluxos de matemática apoiados por IA. Persistência confiável, datasets analíticos curados e modelos preditivos avaliados são objetivos de engenharia — não resultados que afirmamos já estarem concluídos.

## Foco de engenharia

- **Engenharia de Dados:** entradas estruturadas na API, hashes de integridade, schemas explícitos e separação entre a resolução original e as avaliações derivadas.
- **Ciência de Dados:** um domínio para investigar erros recorrentes, evolução da aprendizagem, retenção e recomendação de exercícios, quando houver dados adequados, consentidos e validados.
- **Engenharia de IA:** serviços modulares do MathAI para tutoria, avaliação cognitiva, recomendação e fluxos de imagem/transcrição, com provedores configuráveis.
- **Engenharia de Software:** frontend Next.js, backend FastAPI, configuração por variáveis de ambiente e testes de arquitetura com pytest.

## Arquitetura do sistema

As interações do aluno passam pelo frontend Next.js até um backend FastAPI modular. O backend oferece fluxos de autenticação, exercícios, tentativas, feedback, tutoria e flashcards. Os serviços MathAI utilizam provedores de modelos configuráveis, enquanto o feedback do aluno e a validação humana podem acrescentar contexto às avaliações geradas.

A integração com Supabase/PostgreSQL existe no código, mas nem todas as rotas persistem no banco ainda. Alguns handlers continuam utilizando armazenamento em memória. Essa distinção é importante para a confiabilidade e está documentada abaixo.

## O que já está implementado?

### API e contratos de dados

A aplicação FastAPI inclui rotas modulares para autenticação, exercícios, tentativas, feedback, tutoria e flashcards. Schemas Pydantic definem os contratos de entrada e saída. O repositório também inclui testes automatizados para partes da arquitetura do backend.

### Integridade e proveniência

O registro de tentativas calcula um hash SHA-256 determinístico da entrada original. Os modelos de domínio e os testes de arquitetura expressam a separação entre:

| Camada | Significado |
|---|---|
| **Dados observados** | A resolução enviada pelo aluno e os metadados da interação |
| **Interpretação da IA** | Uma avaliação gerada pelo modelo, como uma classificação de erro ou sugestão de próximo passo |
| **Dados validados** | Feedback ou correção revisada por uma pessoa e associada à avaliação |

A intenção é preservar evidências e permitir reavaliações futuras, sem tratar automaticamente inferências do modelo como verdade de referência.

### Serviços do MathAI

O backend possui serviços separados para dicas socráticas, avaliação cognitiva, recomendação e fluxos de visão/transcrição. O código está preparado para trabalhar com provedores diretos como Google Gemini, NVIDIA e DeepSeek; o 9Router é uma opção de roteamento.

Essas integrações colocam a saída dos modelos dentro dos fluxos da aplicação. Isso **não** significa que o Lemmas já treinou seu próprio modelo fundacional ou demonstrou o desempenho preditivo de um modelo de ML próprio.

### Aprendizagem e revisão

O código inclui endpoints de feedback do aluno e validação humana, fluxos de flashcards e exportação para Anki. O agendador atual de repetição espaçada é um **protótipo simplificado inspirado no FSRS**; seus parâmetros e comportamento precisam de validação antes de sustentar alegações de produção sobre previsão de retenção.

## Roadmap de Engenharia de Dados

O fluxo de dados pretendido prioriza a rastreabilidade:

1. **Capturar:** preservar a submissão original e os metadados relevantes da interação.
2. **Validar:** verificar schemas e qualidade antes de utilizar os dados em etapas posteriores.
3. **Interpretar:** armazenar avaliações da IA separadas da resolução original.
4. **Revisar:** coletar feedback do aluno e, quando disponível, validação especializada.
5. **Preparar datasets:** definir consentimento, proveniência, deduplicação e regras de qualidade antes de análises ou treinamento.

As prioridades incluem persistência durável para os eventos relevantes, migrações explícitas de banco, validação reproduzível e testes consistentes. São problemas reais de uma plataforma de dados, não apenas a integração de uma API de IA.

## Oportunidades de Ciência de Dados

O Lemmas oferece um domínio prático para perguntas futuras que podem ser testadas:

- É possível classificar padrões de erros recorrentes melhor do que um baseline simples baseado em regras?
- Quais estratégias de recomendação de exercícios melhoram o engajamento ou os resultados de aprendizagem?
- Até que ponto um modelo consegue estimar quando um conceito deveria ser revisado?
- Como os provedores de IA se comparam em correção matemática, latência e custo para diferentes tarefas?

O processo planejado é definir objetivos mensuráveis, estabelecer baselines, construir um dataset limpo, evitar vazamento de dados entre treinamento e avaliação e reportar métricas adequadas. Classificação pode utilizar precisão, revocação e F1; recomendações baseadas em ranking podem utilizar Recall@K ou NDCG@K.

**Neste estágio, não afirmamos que exista um modelo de ML próprio treinado ou resultado preditivo validado.** O foco é construir uma base confiável de produto e dados para que os experimentos possam ser realizados com responsabilidade.

## Tecnologias

| Área | Tecnologias |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | Python, FastAPI, Pydantic |
| Integração de dados | Cliente Supabase / PostgreSQL |
| Integrações de IA | Google Gemini, NVIDIA, DeepSeek; 9Router opcional |
| Fluxos de aprendizagem | Tutoria socrática, avaliação, flashcards e agendador simplificado de repetição espaçada |
| Qualidade | Testes de arquitetura e API com pytest |

## Executar localmente

### 1. Clonar o repositório

    git clone https://github.com/StylishGH/LemmaS.git
    cd LemmaS

### 2. Preparar o backend

    cd backend
    python -m venv .venv

Ative o ambiente virtual:

    # Linux / macOS
    source .venv/bin/activate

    # Windows PowerShell
    .venv\Scripts\Activate.ps1

Instale as dependências:

    pip install -r requirements.txt

Use o arquivo .env.example da raiz como referência para criar um .env local. Configure apenas as credenciais necessárias às integrações que pretende utilizar. Nunca envie segredos ao GitHub.

Inicie a API dentro do diretório backend:

    uvicorn app.main:app --reload

A API deverá ficar disponível em http://localhost:8000. A documentação interativa fica habilitada quando a configuração DEBUG do backend está ativada.

### 3. Executar o frontend

Em outro terminal:

    cd frontend
    npm install
    npm run dev

O servidor de desenvolvimento normalmente funciona em http://localhost:3000. Configure localmente as variáveis de ambiente necessárias antes de utilizar funcionalidades que dependem de serviços externos.

## Status atual e limitações

**Status do projeto: em desenvolvimento.** O repositório contém fluxos implementados de API e MathAI, mas capacidades importantes da plataforma de dados ainda precisam de trabalho de engenharia.

- **Persistência:** rotas de tentativas, feedback e flashcards ainda utilizam armazenamento em memória em partes do backend. Esses registros não são duráveis após reiniciar o processo. A integração com Supabase existe, mas ainda não substituiu todos esses armazenamentos.
- **Machine Learning:** treinamento de modelos, avaliação offline sistemática e monitoramento em produção são etapas futuras. O projeto não afirma ter um modelo preditivo próprio implantado.
- **Repetição espaçada:** o agendador atual utiliza lógica simplificada e ilustrativa; precisa ser validado antes de sustentar conclusões científicas sobre retenção.
- **Governança de dados:** qualquer uso futuro de registros de estudantes para análise ou desenvolvimento de modelos deverá respeitar consentimento, privacidade, minimização de dados e as exigências aplicáveis de proteção de dados.

Essas limitações fazem parte do roadmap: primeiro estabelecer contratos e persistência confiáveis; depois construir datasets curados e avaliar abordagens analíticas.

## Roadmap

- [ ] Substituir armazenamentos em memória por persistência durável onde necessário.
- [ ] Fortalecer os testes automatizados e a reprodutibilidade do desenvolvimento.
- [ ] Definir schemas versionados e verificações de qualidade para eventos de aprendizagem.
- [ ] Construir análises exploratórias com dados consentidos e validados.
- [ ] Estabelecer baselines e avaliar modelos de recomendação ou retenção.
- [ ] Acompanhar qualidade, latência e custo dos modelos por tipo de tarefa.

## Sobre o projeto

O Lemmas está sendo desenvolvido por **Guilherme Henrique Mendes**, estudante de Matemática interessado em Engenharia de Dados, Ciência de Dados e IA aplicada.

- [GitHub](https://github.com/StylishGH)
- [LinkedIn](https://linkedin.com/in/ghmendes02)
- [Contato](mailto:ghmendes@id.uff.br)

---

*Lemmas é a plataforma de aprendizagem. MathAI é a camada de inteligência especializada que está sendo desenvolvida para apoiá-la.*
