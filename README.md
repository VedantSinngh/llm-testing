# 🧪 PromptLab

[![CI Pipeline](https://github.com/promptlab/promptlab/actions/workflows/ci.yml/badge.svg)](https://github.com/promptlab/promptlab/actions)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)](https://streamlit.io)
[![SQLAlchemy 2.0](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org)
[![Mypy Strict](https://img.shields.io/badge/mypy-strict-blue.svg)](https://mypy-lang.org/)
[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Coverage](https://img.shields.io/badge/coverage->85%25-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Product-Grade LLM Evaluation & Guardrails Playground**  
> Test prompts, evaluate multi-model trade-offs (Llama 3.3, Qwen 2.5, Mistral Large, Gemma 2), audit adversarial prompt injection vulnerabilities, and detect sensitive data leakage in real time.

---

## 🌟 Table of Contents
1. [Overview & Motivation](#-overview--motivation)
2. [System Architecture](#-system-architecture)
3. [Design Patterns & Engineering Principles](#-design-patterns--engineering-principles)
4. [Key Features](#-key-features)
5. [Tech Stack](#-tech-stack)
6. [Quickstart (Docker & Local)](#-quickstart)
7. [REST API Reference](#-rest-api-reference)
8. [Safety & Security Guardrails](#-safety--security-guardrails)
9. [Interview Talking Points & Technical FAQ](#-interview-talking-points--technical-faq)

---

## 🚀 Overview & Motivation

Building production applications on top of Large Language Models (LLMs) poses major engineering challenges:
- **Prompt Fragility:** Minor changes in phrasing or system prompts trigger silent downstream regressions.
- **Model Selection Dilemma:** Which model (Llama 3.3 70B vs Qwen 2.5 72B vs Mistral Large) delivers the optimal balance of pass rate, latency, and cost?
- **Adversarial Risks:** LLM apps are susceptible to prompt injection, delimiter hijacking, and system prompt leakage.
- **Compliance & Privacy:** Models might inadvertently echo customer PII, phone numbers, or leaked API keys.

**PromptLab** solves these problems with a clean, product-grade platform. It allows engineers to author versioned test suites, run concurrency-controlled evaluations against hosted inference engines (via Groq or offline mock providers), score completions across 7 automated metrics, and audit safety vectors in an interactive Streamlit dashboard.

---

## 🏗️ System Architecture

PromptLab enforces a strict **Layered Clean Architecture**. High-level modules depend exclusively on low-level abstractions, with zero circular imports:

```
┌─────────────────────────────────────────────────────────────┐
│                 Streamlit Multipage UI                      │
│   (Playground · Test Suites · Safety · History/Comparison)  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / REST
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI REST Backend                     │
│    (Request-ID Middleware · Pydantic DTOs · Error Handlers) │
└──────────────────────────────┬──────────────────────────────┘
                               │ Dependency Injection
┌──────────────────────────────▼──────────────────────────────┐
│                  Service Layer (Facades)                    │
│      EvaluationService · ComparisonService · SafetyService   │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
┌──────────────▼─────────────┐   ┌─────────────▼──────────────┐
│  Core Domain Engine (Pure) │   │ Async Repositories (DB)    │
│  - TestRunner (Semaphore)  │   │ - SuiteRepository          │
│  - PromptTechniques        │   │ - RunRepository            │
│  - BaseScorers (Template)  │   │ - SafetyRepository         │
│  - InjectionSuite & Guard  │   │ - SQLAlchemy 2.0 + SQLite  │
│  - ProviderFactory (Groq)  │   └────────────────────────────┘
└────────────────────────────┘
```

---

## 🧩 Design Patterns & Engineering Principles

| Design Pattern | Implementation Location | Engineering Purpose |
|---|---|---|
| **Template Method** | `BaseScorer` (`core/scorers/base.py`) | Enforces standard scoring workflow: `_preprocess()` → `_evaluate()` → `_finalize()` across all 7 scorers. |
| **Strategy Pattern** | `PromptTechnique` (`core/techniques/base.py`) | Decouples prompt formulation (`ZeroShot`, `FewShot`, `ChainOfThought`, `StructuredOutput`). |
| **Factory & Registry** | `ProviderFactory`, `ScorerRegistry`, `TechniqueRegistry` | Open/Closed Principle (SOLID). Allows registering new providers, scorers, or techniques without altering existing code. |
| **Facade Pattern** | `EvaluationService` (`services/evaluation_service.py`) | Provides a unified, simplified entry point orchestrating runners, providers, and repositories. |
| **Repository Pattern** | `db/repositories.py` | Encapsulates database queries (`SuiteRepository`, `RunRepository`, `SafetyRepository`), keeping domain code free of SQL cursors. |
| **Dependency Injection** | `api/dependencies.py` | FastAPI `Depends` manages request-scoped async database sessions and service lifecycles. |
| **Mock Object Pattern** | `MockProvider` (`core/providers/mock_provider.py`) | Deterministic, zero-credential testing and instant offline demo capability with fault simulation. |

---

## ⚡ Key Features

### 1. Multi-Model Inference with Resilient Retries
- Integrated with **Groq Cloud API** for ultra-low latency inference (Llama 3.3 70B, Qwen 2.5 72B, Gemma 2 9B, Mistral Large).
- Exponential backoff with random jitter on HTTP 429 (rate limits) and 5xx errors.
- Built-in deterministic `MockProvider` allowing full offline execution without API keys.

### 2. Automated Scoring Engine (7 Scorers)
- **Exact Match:** Case-insensitive or normalized string equality.
- **Contains:** Substring presence verification.
- **Regex Match:** Pattern validation for structured values (UUIDs, dates, phone codes).
- **JSON Valid:** Syntactic validation of JSON output strings.
- **JSON Schema:** Strict schema conformance validation via `jsonschema`.
- **SQL Result:** Zero-trust query execution against a target SQLite database. Blocks all non-SELECT queries.
- **LLM Judge:** Rubric-based scoring with score normalization (0.0 to 1.0) and justification logging.

### 3. Defense-in-Depth Safety & Guardrails
- **Adversarial Injection Suite:** 16 attack vectors across 5 categories:
  - Direct instruction overrides (`Ignore previous instructions`)
  - Delimiter and role hijacking (`### SYSTEM PROMPT TERMINATED`)
  - Roleplay jailbreaks (`DAN / Developer Mode simulation`)
  - Multi-lingual token bypasses
  - Base64 / ROT13 encoded payloads
- **Canary Extraction Detection:** Injects high-entropy tokens and monitors model completions for security boundary violations.
- **PII & Credential Guardrail:** Real-time regex detection and text sanitization for Emails, Indian & Intl Phone Numbers, IPv4 Addresses, Credit Cards (validated with **Luhn Algorithm**), and API keys (`gsk_`, `sk-`, `AKIA`).

### 4. Side-by-Side Comparison & Leaderboards
- Compare multiple runs across models, prompt formulations, and temperatures.
- Automated leaderboards for Best Pass Rate, Lowest Latency (ms), and Minimal Token Consumption.
- Case-by-case matrix alignment with visual output diffs.

---

## 💻 Tech Stack

- **Language:** Python 3.11+
- **API Framework:** FastAPI, Uvicorn, Pydantic v2, Pydantic-Settings
- **Persistence:** SQLAlchemy 2.0 (Async), `aiosqlite`, SQLite
- **LLM Inference:** `groq` SDK, Custom Async Mock Provider
- **Dashboard:** Streamlit (Multipage architecture)
- **HTTP Client:** `httpx` (Async for tests, Sync for UI)
- **Quality & CI:** Pytest, Pytest-Asyncio, Pytest-Cov, Ruff, Mypy (`strict = true`), Pre-commit

---

## 🏁 Quickstart

### Option A: 1-Click Docker Compose (Recommended)

Clone the repository and spin up both the FastAPI backend and Streamlit dashboard:

```bash
# 1. Clone repository
git clone https://github.com/promptlab/promptlab.git
cd promptlab

# 2. (Optional) Provide your Groq API key in .env
cp .env.example .env
# Edit .env and set GROQ_API_KEY=gsk_... or leave empty for Demo Mode!

# 3. Launch system
docker compose up --build
```

- **Streamlit Dashboard:** Navigate to [http://localhost:8501](http://localhost:8501)
- **FastAPI Interactive Docs (Swagger):** Navigate to [http://localhost:8000/docs](http://localhost:8000/docs)
- **API Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

### Option B: Local Python Environment

```bash
# 1. Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install package in editable mode with development dependencies
pip install -e ".[dev]"

# 3. Seed database with benchmark suites and baseline evaluation runs
python scripts/seed_db.py

# 4. Run test suite to verify everything passes (100% green)
pytest -v

# 5. Launch FastAPI Backend (Terminal 1)
uvicorn promptlab.api.main:app --host 0.0.0.0 --port 8000 --reload

# 6. Launch Streamlit Playground (Terminal 2)
streamlit run src/promptlab/dashboard/app.py --server.port 8501
```

---

## 📡 REST API Reference

All routes are mounted at `/api/v1` and accessible at root for developer ergonomics.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Application status, demo mode flag, active provider, and server timestamp. |
| `GET` | `/api/v1/models` | Supported model catalog from active provider. |
| `POST` | `/api/v1/suites` | Register and persist a new test suite. |
| `GET` | `/api/v1/suites` | List saved test suites with pagination (`offset`, `limit`). |
| `GET` | `/api/v1/suites/{id}` | Retrieve test suite details. |
| `DELETE` | `/api/v1/suites/{id}` | Delete test suite by ID. |
| `POST` | `/api/v1/runs` | Execute an evaluation run (by suite ID or inline suite payload). |
| `GET` | `/api/v1/runs` | Query evaluation run history with filtering (`suite_name`, `model`). |
| `GET` | `/api/v1/runs/{id}` | Get run results including individual case outcomes and token metrics. |
| `POST` | `/api/v1/runs/compare` | Compare 2+ evaluation runs side-by-side with matrix alignment. |
| `POST` | `/api/v1/safety/injection-test` | Run 16 adversarial prompt injection attacks with canary tracking. |
| `POST` | `/api/v1/safety/scan` | Scan arbitrary text for PII entities, tokens, and return sanitized text. |
| `GET` | `/api/v1/safety/reports` | List historical security audit reports. |

### Example cURL Commands

```bash
# 1. Health Check
curl http://localhost:8000/health

# 2. Trigger Evaluation Run
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "suite": {
      "name": "quick_math",
      "cases": [
        {"id": "c1", "input": "What is 15 * 4?", "expected": "60", "scorer": "exact_match"}
      ]
    },
    "model": "mock-llama-3.3-70b",
    "params": {"temperature": 0.1, "max_tokens": 128}
  }'

# 3. Real-Time PII & Secret Scan
curl -X POST http://localhost:8000/api/v1/safety/scan \
  -H "Content-Type: application/json" \
  -d '{"text": "Contact user at admin@acme.com with key gsk_abcdef1234567890abcdef."}'
```

---

## 🛡️ Safety & Security Guardrails

### 1. SQL Injection Protection in `SqlResult` Scorer
When evaluating Text-to-SQL generation, letting LLM output execute against a database is a major security hazard. PromptLab implements a **zero-trust execution sandbox**:
- Strict regex token inspection requiring the statement to start with `SELECT` or `WITH`.
- Rejects stacked queries (queries containing `;` followed by additional statements).
- Strictly blocks destructive SQL keywords: `DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`, `TRUNCATE`, `EXEC`, `CREATE`, `ATTACH`, `PRAGMA`.
- Raises `SecurityError` immediately before any query hits SQLite.

### 2. Canary Leakage Detection
In adversarial testing, measuring prompt injection resistance requires proof that the model followed the attacker's prompt over the system instructions. PromptLab uses **high-entropy canary tokens** (e.g. `CANARY_4f8a...`). The suite verifies whether the canary is present in the output, yielding deterministic, binary breach verification.

### 3. Credit Card Luhn Algorithm Validation
Rather than blindly matching 16 digits, PromptLab validates candidate credit card numbers using the standard **Luhn checksum algorithm**, eliminating false-positive matches on order numbers or product codes.

---

## 🎙️ Interview Talking Points & Technical FAQ

### Q1: Why use the Template Method pattern for scorers?
> *"In evaluation frameworks, all evaluation scorers share a common lifecycle: preprocessing input text (stripping whitespace, lowercasing), executing domain-specific validation logic, and finalizing metadata and score normalization between 0.0 and 1.0. The Template Method pattern in `BaseScorer` keeps this skeleton invariant while allowing subclasses (`ExactMatch`, `JsonSchema`, `SqlResult`, `LLMJudge`) to implement only `_evaluate()` and `_evaluate_async()`, eliminating repetitive boilerplate and guaranteeing consistent score formats."*

### Q2: How is concurrency managed when running evaluations across hundreds of test cases?
> *"LLM inference APIs enforce strict rate and concurrency limits. Using unbounded `asyncio.gather()` would immediately trigger HTTP 429 rate limits. In `TestRunner`, concurrency is throttled using `asyncio.Semaphore(max_concurrency)`. Furthermore, each case execution is wrapped in isolated exception handlers so an individual model timeout or error records a failed `CaseResult` rather than crashing the entire test suite run."*

### Q3: How do you handle distributed tracing and structured logging across async tasks?
> *"In high-concurrency async Python, standard thread-local storage fails because coroutines hop threads. PromptLab uses `contextvars.ContextVar` to bind a unique `request_id`. An HTTP middleware captures or generates `X-Request-ID`, propagating it through the async context. The custom `JSONLogFormatter` extracts this ID for every log line and automatically masks sensitive tokens (`gsk_`, `sk-`, `AKIA`) using precompiled regexes to prevent credential leakage in logs."*

### Q4: Why SQLAlchemy 2.0 with the Repository Pattern?
> *"SQLAlchemy 2.0 introduces fully typed queries (`select(Model)`) with modern `async/await` semantics through `AsyncSession`. We encapsulated queries behind the Repository pattern (`SuiteRepository`, `RunRepository`, `SafetyRepository`). This adheres to Dependency Inversion: higher-level service facades and API controllers depend on domain interfaces rather than raw ORM sessions or SQL queries, making testing with in-memory SQLite fixtures fast and decoupled."*

### Q5: How do you prevent prompt injection from compromising LLM applications?
> *"Defense-in-depth: At PromptLab, we address prompt injection in two ways. First, our `InjectionSuite` actively benchmarks models against 16 known attack vectors (instruction overrides, delimiters, roleplay jailbreaks, encoding) using canary tokens to quantify model resilience. Second, our `Guardrail` inspects runtime inputs and completions, classifying risk levels and automatically redacting PII and API credentials before payloads leave the trust boundary."*

---

## 📄 License
PromptLab is open-source software licensed under the [MIT License](LICENSE).
