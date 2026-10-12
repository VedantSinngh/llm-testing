# PromptLab Master Architecture & Engineering Guide (00_INDEX)

Welcome to the definitive engineering documentation and interview preparation repository for **PromptLab** (`VedantSinngh/llm-testing`). This guide provides comprehensive, file-by-file, line-level architectural transparency into every subsystem, pattern, testing strategy, and production deployment pipeline across the codebase.

---

## Document Index & Reading Tracks

The documentation suite is split into 14 structured parts located under `docs/understanding/`.

| Part | Document | Primary Focus | Best For |
|---|---|---|---|
| **01** | [01_big_picture.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/01_big_picture.md) | High-level system architecture, problem domain, core workflows | Onboarding & Overview |
| **02** | [02_file_by_file.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/02_file_by_file.md) | Exhaustive file-by-file walkthrough of all 42 modules | Implementation Deep Dive |
| **03** | [03_domain_models.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/03_domain_models.md) | Pydantic v2 schemas, type safety, JSON serialization | Data Modeling & Schema |
| **04** | [04_data_flow_traces.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/04_data_flow_traces.md) | Step-by-step trace of 4 core system journeys | Execution Tracing |
| **05** | [05_design_patterns_and_oop.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/05_design_patterns_and_oop.md) | Strategy, Template Method, Registry, Adapter, Repository | Software Design & OOP |
| **06** | [06_database_and_persistence.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/06_database_and_persistence.md) | Async SQLAlchemy 2.0, dual SQLite/Postgres ORM | Database Engineering |
| **07** | [07_concurrency_and_reliability.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/07_concurrency_and_reliability.md) | `asyncio.Semaphore`, retry backoff, jitter, timeouts | Distributed Systems & SRE |
| **08** | [08_config_security_and_safety.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/08_config_security_and_safety.md) | Canary tokens, PII scrubbing, SQL injection fences | Security & Compliance |
| **09** | [09_testing_map.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/09_testing_map.md) | 136 tests, unit/integration mocks, coverage map | QA & Test Architecture |
| **10** | [10_dashboard_walkthrough.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/10_dashboard_walkthrough.md) | Streamlit dashboard UI, session state, charts | Frontend & UX |
| **11** | [11_build_run_deploy.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/11_build_run_deploy.md) | Docker, Render PaaS, GitHub Actions CI/CD matrix | DevOps & Infrastructure |
| **12** | [12_honest_review.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/12_honest_review.md) | Architecture review, technical debt, trade-offs | Tech Lead & Senior Review |
| **13** | [13_interview_pack.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/13_interview_pack.md) | 30 technical interview Q&As, STAR stories, system design | Interview Preparation |

---

## Role-Based Quick Tracks

### Track A: The Interview Candidate (Time: 45 mins)
1. Read [01_big_picture.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/01_big_picture.md) to explain what PromptLab is and why it exists.
2. Read [05_design_patterns_and_oop.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/05_design_patterns_and_oop.md) to master the design patterns (Strategy, Factory, Repository).
3. Read [13_interview_pack.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/13_interview_pack.md) to drill the top 30 questions and STAR scenario walkthroughs.

### Track B: The Core Backend & LLM Engineer (Time: 60 mins)
1. Read [03_domain_models.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/03_domain_models.md) to learn the data contracts.
2. Read [04_data_flow_traces.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/04_data_flow_traces.md) to trace the execution from API request to evaluation metrics.
3. Read [07_concurrency_and_reliability.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/07_concurrency_and_reliability.md) and [08_config_security_and_safety.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/08_config_security_and_safety.md) for resilience and safety mechanics.

### Track C: DevOps, SRE & Platform Engineer (Time: 30 mins)
1. Read [11_build_run_deploy.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/11_build_run_deploy.md) for Docker, Render, and GitHub Actions CI pipelines.
2. Read [06_database_and_persistence.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/06_database_and_persistence.md) for async pooling, connection lifecycle, and database URL dialect normalization (`asyncpg` / `psycopg`).
3. Read [09_testing_map.md](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/docs/understanding/09_testing_map.md) for test execution and coverage enforcement.

---

## Architectural Summary

PromptLab is designed around clean separation of concerns:
- **Presentation Layer:** FastAPI REST API (`src/promptlab/api`) and Streamlit Interactive Dashboard (`src/promptlab/dashboard`).
- **Domain & Application Services:** `EvaluationService`, `ComparisonService`, `SafetyService` orchestrating business operations.
- **Core Engine:** Pluggable `PromptTechnique`, `LLMProvider`, and `BaseScorer` implementations governed by strict registries.
- **Persistence Layer:** SQLAlchemy 2.0 Async ORM with the Repository Pattern supporting both zero-dependency SQLite and production PostgreSQL.
- **Safety & Guardrails:** Regex PII entity redaction with Luhn credit-card verification, AST SQL safety fences, and canary-token injection vulnerability testing.
