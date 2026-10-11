<div align="center">
  <h1>Lemmas 📐</h1>
  <p><strong>Adaptive learning, built around data.</strong></p>
  <p>An adaptive mathematics learning platform exploring Data Engineering, Data Science, and Applied AI.</p>
  <p><a href="./README.pt-BR.md">🇧🇷 Português (Brasil)</a> &nbsp;|&nbsp; <strong>🇺🇸 English</strong></p>
  <p><a href="https://lemmas-ochre.vercel.app/dashboard"><strong>🚀 Try Lemmas live</strong></a></p>
  <p>
    <img src="https://img.shields.io/badge/Next.js-16-000000?logo=next.js" alt="Next.js 16" />
    <img src="https://img.shields.io/badge/FastAPI-REST%20API-009688?logo=fastapi" alt="FastAPI" />
    <img src="https://img.shields.io/badge/Supabase-PostgreSQL-3ECF8E?logo=supabase" alt="Supabase / PostgreSQL" />
    <img src="https://img.shields.io/badge/Python-3.x-3776AB?logo=python" alt="Python" />
    <img src="https://img.shields.io/badge/Status-In%20Development-yellow" alt="In development" />
  </p>
</div>

---

## Why Lemmas?

What could a learning platform discover if it treated a student's learning process as structured data instead of recording only right and wrong answers?

Two students can make the same mistake for different reasons. One may misunderstand a concept; another may understand it but make an algebraic error. An adaptive system needs to preserve the work actually submitted, distinguish it from AI-generated interpretation, and allow feedback or human review to correct that interpretation.

The core principle is:

> **Observed data ≠ AI interpretation ≠ validated data.**

Lemmas is an evolving product and a hands-on engineering project. The codebase focuses on a modular web/API architecture and AI-assisted mathematics workflows. Reliable persistence, curated analytical datasets, and evaluated predictive models are engineering goals—not accomplishments claimed as complete.

## Engineering focus

- **Data Engineering:** structured API inputs, data-integrity hashes, explicit schemas, and separation of raw student work from derived assessments.
- **Data Science:** a domain for investigating recurring errors, learning progress, retention, and exercise recommendation once suitable, consented, validated data is available.
- **AI Engineering:** modular MathAI services for tutoring, cognitive evaluation, recommendation, and image/transcription workflows, with configurable model providers.
- **Software Engineering:** Next.js frontend, FastAPI backend, environment-based configuration, and pytest-based architecture tests.

## System architecture

Student interactions flow through the Next.js frontend to a modular FastAPI backend. The backend exposes workflows for authentication, exercises, attempts, feedback, tutoring, and flashcards. MathAI services call configurable model providers, while student feedback and human validation can add context to generated assessments.

Supabase/PostgreSQL integration exists in the codebase, but not every route persists to the database yet. Some route handlers still use in-memory stores. This distinction matters for reliability and is documented below.

## What is implemented?

### API and data contracts

The FastAPI application includes modular routes for authentication, exercises, attempts, feedback, tutoring, and flashcards. Pydantic schemas define request and response contracts. The repository also includes automated tests for parts of the backend architecture.

### Data integrity and provenance

Attempt capture computes a deterministic SHA-256 hash of the submitted raw input. Domain models and architecture tests express a separation between:

| Layer | Meaning |
|---|---|
| **Observed data** | The student's submitted work and interaction metadata |
| **AI interpretation** | A model-generated assessment, such as an error classification or suggested next step |
| **Validated data** | Feedback or a human-reviewed correction associated with an assessment |

The goal is to preserve evidence and support future re-evaluation without automatically treating model inference as ground truth.

### MathAI services

The backend has separate services for Socratic hints, cognitive evaluation, recommendation, and vision/transcription workflows. The code is configured to work with direct providers such as Google Gemini, NVIDIA, and DeepSeek; 9Router is an optional routing path.

These integrations put model output inside application workflows. They do **not** mean Lemmas has trained its own foundation model or demonstrated the predictive performance of a custom ML model.

### Learning and review

The codebase includes student-feedback and human-validation endpoints, flashcard workflows, and Anki export. The current spaced-repetition scheduler is a **simplified FSRS-inspired prototype**; its parameters and behavior need validation before supporting production-level claims about retention prediction.

## Data Engineering roadmap

The intended data flow prioritizes traceability:

1. **Capture:** preserve the original student submission and relevant interaction metadata.
2. **Validate:** check schemas and data quality before downstream use.
3. **Interpret:** store AI-generated assessments separately from the original submission.
4. **Review:** collect student feedback and, where available, expert validation.
5. **Prepare datasets:** define consent, provenance, deduplication, and quality rules before analytics or training.

Key engineering priorities include durable persistence for relevant event types, explicit database migrations, repeatable validation, and reproducible tests. These are substantive data-platform problems, not merely API integration.

## Data Science opportunities

Lemmas creates a practical domain for future, testable questions:

- Can recurring error patterns be classified more reliably than a simple rules-based baseline?
- Which exercise-recommendation strategies improve engagement or learning outcomes?
- How well can a model estimate when a concept should be reviewed?
- How do model providers compare on mathematical correctness, latency, and cost across task types?

The planned process is to define measurable targets, establish baselines, build a clean dataset, prevent leakage between training and evaluation, and report task-appropriate metrics. Classification may use precision, recall, and F1; ranking-based recommendations may use Recall@K or NDCG@K.

**No custom-trained ML model or validated predictive result is being claimed at this stage.** The focus is building a trustworthy product and data foundation from which responsible experiments can follow.

## Technology stack

| Area | Technologies |
|---|---|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS 4 |
| Backend | Python, FastAPI, Pydantic |
| Data integration | Supabase client / PostgreSQL |
| AI integrations | Google Gemini, NVIDIA, DeepSeek; optional 9Router |
| Learning workflows | Socratic tutoring, evaluation, flashcards, simplified spaced-repetition scheduler |
| Quality | pytest-based architecture and API tests |

## Run locally

### 1. Clone the repository

    git clone https://github.com/StylishGH/LemmaS.git
    cd LemmaS

### 2. Set up the backend

    cd backend
    python -m venv .venv

Activate the virtual environment:

    # Linux / macOS
    source .venv/bin/activate

    # Windows PowerShell
    .venv\Scripts\Activate.ps1

Install dependencies:

    pip install -r requirements.txt

Use the repository's root-level .env.example as a reference to create a local .env file. Configure only the credentials needed for the integrations you plan to use. Never commit secrets.

Start the API from the backend directory:

    uvicorn app.main:app --reload

The API should be available at http://localhost:8000. Interactive API documentation is enabled when the backend's DEBUG setting is on.

### 3. Run the frontend

In another terminal:

    cd frontend
    npm install
    npm run dev

The frontend development server normally runs at http://localhost:3000. Configure the frontend's required environment variables locally before using features that depend on external services.

## Current status and limitations

**Project status: in development.** The repository contains implemented API and MathAI workflows, but important data-platform capabilities still need further engineering.

- **Persistence:** attempt, feedback, and flashcard routes still use in-memory stores in parts of the backend. Those records are not durable across process restarts. Supabase integration exists, but it has not replaced every in-memory store.
- **Machine Learning:** model training, systematic offline evaluation, and production monitoring are future work. The project does not claim a custom predictive model is deployed.
- **Spaced repetition:** the current scheduler uses simplified, illustrative logic and needs validation before supporting scientific conclusions about retention.
- **Data governance:** any future use of student records for analysis or model development must respect consent, privacy, data minimization, and applicable data-protection requirements.

These limitations are part of the engineering roadmap: establish reliable data contracts and persistence first, then build curated datasets and evaluate analytical approaches.

## Roadmap

- [ ] Replace prototype in-memory stores with durable persistence where required.
- [ ] Strengthen automated tests and reproducible development workflows.
- [ ] Define versioned schemas and data-quality checks for learning events.
- [ ] Build exploratory analyses from consented, validated data.
- [ ] Establish baselines and evaluate recommendation or retention models.
- [ ] Track model quality, latency, and cost by task type.

## About

Lemmas is being developed by **Guilherme Henrique Mendes**, a Mathematics undergraduate interested in Data Engineering, Data Science, and Applied AI.

- [GitHub](https://github.com/StylishGH)
- [LinkedIn](https://linkedin.com/in/ghmendes02)
- [Contact](mailto:ghmendes@id.uff.br)

---

*Lemmas is the learning platform. MathAI is the specialized intelligence layer being developed to support it.*
