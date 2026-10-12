# PromptLab: File-by-File Technical Deep Dive

This document provides a comprehensive, line-level analysis of **every single source file** in PromptLab. Files are arranged in strict **dependency order (bottom layer first)**: from cross-cutting utilities and domain models, up through core strategies, repositories, services, API controllers, and the frontend dashboard.

---

## Table of Contents

- [Layer 1: Core Foundation & Cross-Cutting](#layer-1-core-foundation--cross-cutting)
  - [1.1 `src/promptlab/__init__.py`](#11-srcpromptlab__init__py)
  - [1.2 `src/promptlab/config.py`](#12-srcpromptlabconfigpy)
  - [1.3 `src/promptlab/exceptions.py`](#13-srcpromptlabexceptionspy)
  - [1.4 `src/promptlab/logging_config.py`](#14-srcpromptlablogging_configpy)
- [Layer 2: Domain Entities](#layer-2-domain-entities)
  - [2.1 `src/promptlab/core/models.py`](#21-srcpromptlabcoremodelspy)
- [Layer 3: Providers (LLM Inference Adapters)](#layer-3-providers-llm-inference-adapters)
  - [3.1 `src/promptlab/core/providers/base.py`](#31-srcpromptlabcoreprovidersbasepy)
  - [3.2 `src/promptlab/core/providers/mock_provider.py`](#32-srcpromptlabcoreprovidersmock_providerpy)
  - [3.3 `src/promptlab/core/providers/groq_provider.py`](#33-srcpromptlabcoreprovidersgroq_providerpy)
  - [3.4 `src/promptlab/core/providers/factory.py`](#34-srcpromptlabcoreprovidersfactorypy)
  - [3.5 `src/promptlab/core/providers/__init__.py`](#35-srcpromptlabcoreproviders__init__py)
- [Layer 4: Prompt Engineering Techniques (Strategies)](#layer-4-prompt-engineering-techniques-strategies)
  - [4.1 `src/promptlab/core/techniques/base.py`](#41-srcpromptlabcoretechniquesbasepy)
  - [4.2 `src/promptlab/core/techniques/zero_shot.py`](#42-srcpromptlabcoretechniqueszero_shotpy)
  - [4.3 `src/promptlab/core/techniques/few_shot.py`](#43-srcpromptlabcoretechniquesfew_shotpy)
  - [4.4 `src/promptlab/core/techniques/chain_of_thought.py`](#44-srcpromptlabcoretechniqueschain_of_thoughtpy)
  - [4.5 `src/promptlab/core/techniques/structured_output.py`](#45-srcpromptlabcoretechniquesstructured_outputpy)
  - [4.6 `src/promptlab/core/techniques/registry.py`](#46-srcpromptlabcoretechniquesregistrypy)
  - [4.7 `src/promptlab/core/techniques/__init__.py`](#47-srcpromptlabcoretechniques__init__py)
- [Layer 5: Evaluation Scorers (Template Method Hierarchy)](#layer-5-evaluation-scorers-template-method-hierarchy)
  - [5.1 `src/promptlab/core/scorers/base.py`](#51-srcpromptlabcorescorersbasepy)
  - [5.2 `src/promptlab/core/scorers/exact_match.py`](#52-srcpromptlabcorescorersexact_matchpy)
  - [5.3 `src/promptlab/core/scorers/contains.py`](#53-srcpromptlabcorescorerscontainspy)
  - [5.4 `src/promptlab/core/scorers/regex_match.py`](#54-srcpromptlabcorescorersregex_matchpy)
  - [5.5 `src/promptlab/core/scorers/json_valid.py`](#55-srcpromptlabcorescorersjson_validpy)
  - [5.6 `src/promptlab/core/scorers/json_schema.py`](#56-srcpromptlabcorescorersjson_schemapy)
  - [5.7 `src/promptlab/core/scorers/sql_result.py`](#57-srcpromptlabcorescorerssql_resultpy)
  - [5.8 `src/promptlab/core/scorers/llm_judge.py`](#58-srcpromptlabcorescorersllm_judgepy)
  - [5.9 `src/promptlab/core/scorers/registry.py`](#59-srcpromptlabcorescorersregistrypy)
  - [5.10 `src/promptlab/core/scorers/__init__.py`](#510-srcpromptlabcorescorers__init__py)
- [Layer 6: Safety, Guardrails & Adversarial Audits](#layer-6-safety-guardrails--adversarial-audits)
  - [6.1 `src/promptlab/core/safety/pii_detector.py`](#61-srcpromptlabcoresafetypii_detectorpy)
  - [6.2 `src/promptlab/core/safety/guardrail.py`](#62-srcpromptlabcoresafetyguardrailpy)
  - [6.3 `src/promptlab/core/safety/injection_suite.py`](#63-srcpromptlabcoresafetyinjection_suitepy)
  - [6.4 `src/promptlab/core/safety/__init__.py`](#64-srcpromptlabcoresafety__init__py)
- [Layer 7: Core Orchestration Runner & Package Root](#layer-7-core-orchestration-runner--package-root)
  - [7.1 `src/promptlab/core/runner.py`](#71-srcpromptlabcorerunnerpy)
  - [7.2 `src/promptlab/core/__init__.py`](#72-srcpromptlabcore__init__py)
- [Layer 8: Database & Persistence Layer](#layer-8-database--persistence-layer)
  - [8.1 `src/promptlab/db/base.py`](#81-srcpromptlabdbbasepy)
  - [8.2 `src/promptlab/db/orm_models.py`](#82-srcpromptlabdborm_modelspy)
  - [8.3 `src/promptlab/db/repositories.py`](#83-srcpromptlabdbrepositoriespy)
  - [8.4 `src/promptlab/db/__init__.py`](#84-srcpromptlabdb__init__py)
- [Layer 9: Service Facades & Business Logic](#layer-9-service-facades--business-logic)
  - [9.1 `src/promptlab/services/comparison_service.py`](#91-srcpromptlabservicescomparison_servicepy)
  - [9.2 `src/promptlab/services/evaluation_service.py`](#92-srcpromptlabservicesevaluation_servicepy)
  - [9.3 `src/promptlab/services/safety_service.py`](#93-srcpromptlabservicessafety_servicepy)
  - [9.4 `src/promptlab/services/__init__.py`](#94-srcpromptlabservices__init__py)
- [Layer 10: API Layer (FastAPI)](#layer-10-api-layer-fastapi)
  - [10.1 `src/promptlab/api/schemas.py`](#101-srcpromptlabapischemaspy)
  - [10.2 `src/promptlab/api/dependencies.py`](#102-srcpromptlabapidependenciespy)
  - [10.3 `src/promptlab/api/routes/health.py`](#103-srcpromptlabapirouteshealthpy)
  - [10.4 `src/promptlab/api/routes/models.py`](#104-srcpromptlabapiroutesmodelspy)
  - [10.5 `src/promptlab/api/routes/suites.py`](#105-srcpromptlabapiroutessuitespy)
  - [10.6 `src/promptlab/api/routes/runs.py`](#106-srcpromptlabapiroutesrunspy)
  - [10.7 `src/promptlab/api/routes/safety.py`](#107-srcpromptlabapiroutessafetypy)
  - [10.8 `src/promptlab/api/routes/__init__.py`](#108-srcpromptlabapiroutes__init__py)
  - [10.9 `src/promptlab/api/main.py`](#109-srcpromptlabapimainpy)
  - [10.10 `src/promptlab/api/__init__.py`](#1010-srcpromptlabapi__init__py)
- [Layer 11: Presentation Layer (Streamlit Dashboard)](#layer-11-presentation-layer-streamlit-dashboard)
  - [11.1 `src/promptlab/dashboard/api_client.py`](#111-srcpromptlabdashboardapi_clientpy)
  - [11.2 `src/promptlab/dashboard/app.py`](#112-srcpromptlabdashboardapppy)
  - [11.3 `src/promptlab/dashboard/pages/1_Playground.py`](#113-srcpromptlabdashboardpages1_playgroundpy)
  - [11.4 `src/promptlab/dashboard/pages/2_Test_Suites.py`](#114-srcpromptlabdashboardpages2_test_suitespy)
  - [11.5 `src/promptlab/dashboard/pages/3_Safety_&_Guardrails.py`](#115-srcpromptlabdashboardpages3_safety__guardrailspy)
  - [11.6 `src/promptlab/dashboard/pages/4_History_&_Comparison.py`](#116-srcpromptlabdashboardpages4_history__comparisonpy)
  - [11.7 `src/promptlab/dashboard/__init__.py`](#117-srcpromptlabdashboard__init__py)
- [Gaps, Code Smells & Missing Elements](#gaps-code-smells--missing-elements)

---

## Layer 1: Core Foundation & Cross-Cutting

### 1.1 `src/promptlab/__init__.py`
[src/promptlab/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/__init__.py)

- **Purpose in one sentence:** Defines the top-level package metadata and exports the PromptLab semantic release version.
- **Public Classes and Functions:**
  - `__version__: str = "0.1.0"` (Module constant)
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* None.
  - *Outputs:* Exposes package version string.
  - *Side effects:* None.
- **Imports:**
  - *Imports from:* Nothing.
  - *Imported by:* Package consumers and packaging tooling.
- **Design Pattern:** None (standard Python package initialization).
- **Trickiest Line or Block:**
  ```python
  7: __version__ = "0.1.0"
  ```
  *Explanation:* Kept static to match the version in [pyproject.toml:7](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/pyproject.toml#L7) rather than dynamically loaded via `importlib.metadata`, avoiding startup filesystem lookups.

---

### 1.2 `src/promptlab/config.py`
[src/promptlab/config.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/config.py)

- **Purpose in one sentence:** Declares and validates strongly-typed runtime settings from `.env` files and environment variables, caching a global configuration singleton.
- **Public Classes and Functions:**
  - `class Settings(BaseSettings)`: Typed Pydantic configuration container.
  - `Settings.normalize_log_level(cls, value: str) -> str`: Field validator ensuring log levels are uppercase strings.
  - `def get_settings() -> Settings`: LRU-cached factory function returning the application settings singleton.
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* OS environment variables and optional `.env` file on disk.
  - *Outputs:* Validated `Settings` instance containing fields like `groq_api_key`, `default_model`, `max_concurrency`, `database_url`, `demo_mode`.
  - *Side effects:* Reads filesystem (`.env`) upon first execution.
- **Imports:**
  - *Imports from:* `pydantic`, `pydantic_settings`, `functools.lru_cache`, `typing`.
  - *Imported by:* `api.dependencies`, `api.routes.health`, `api.routes.models`, `core.runner`, `core.providers.groq_provider`, `core.scorers.llm_judge`, `db.base`, `services.*`, `scripts/seed_db.py`.
- **Design Pattern:** **Singleton Pattern** implemented via `@lru_cache(maxsize=1)` on [src/promptlab/config.py:99-106](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/config.py#L99-L106).
- **Trickiest Line or Block:**
  ```python
  99: @lru_cache(maxsize=1)
  100: def get_settings() -> Settings:
  101:     return Settings()
  ```
  *Explanation:* Using `@lru_cache(maxsize=1)` guarantees that `Settings()` is instantiated and validated exactly once across the lifetime of the process. Without this cache, every dependency injection call (`Depends(get_settings)`) in FastAPI would re-read the `.env` file and re-run all Pydantic validators, introducing disk I/O latency to every HTTP request.

---

### 1.3 `src/promptlab/exceptions.py`
[src/promptlab/exceptions.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/exceptions.py)

- **Purpose in one sentence:** Establishes a unified domain exception hierarchy carrying machine-readable error codes and recommended HTTP status codes.
- **Public Classes and Functions:**
  - `class PromptLabError(Exception)`: Root exception. Method: `to_dict() -> dict[str, Any]`.
  - `class ConfigurationError(PromptLabError)`: Raised for invalid environment/config (status 500, code `CONFIGURATION_ERROR`).
  - `class ProviderError(PromptLabError)`: Raised on upstream LLM failures (status 502, code `PROVIDER_ERROR`).
  - `class RateLimitError(PromptLabError)`: Raised on 429 quota exhaustion (status 429, code `RATE_LIMIT_ERROR`).
  - `class ProviderNotFoundError(PromptLabError)`: Raised when an unregistered provider is requested (status 404).
  - `class ScorerNotFoundError(PromptLabError)`: Raised when an unregistered scorer is requested (status 404).
  - `class TechniqueNotFoundError(PromptLabError)`: Raised when an unregistered technique is requested (status 404).
  - `class ValidationError(PromptLabError)`: Raised when domain invariants fail (status 422).
  - `class ResourceNotFoundError(PromptLabError)`: Raised when DB entities do not exist (status 404).
  - `class SecurityError(PromptLabError)`: Raised on security violations like non-SELECT SQL (status 400).
  - `class AuthenticationError(PromptLabError)`: Raised on auth failure (status 401).
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* Human message string, error code, status code, and optional diagnostic context dictionary.
  - *Outputs:* Serializable exception payloads.
  - *Side effects:* None.
- **Imports:**
  - *Imports from:* `typing`.
  - *Imported by:* Almost every module in `core`, `db`, `services`, `api`, and `dashboard.api_client`.
- **Design Pattern:** **Exception Hierarchy / Taxonomical Hierarchy Pattern**, decoupling application domain errors from FastAPI web dependencies.
- **Trickiest Line or Block:**
  ```python
  35: def to_dict(self) -> dict[str, Any]:
  36:     payload: dict[str, Any] = {
  37:         "error_code": self.error_code,
  38:         "message": self.message,
  39:     }
  40:     if self.details:
  41:         payload["details"] = self.details
  42:     return payload
  ```
  *Explanation:* Enables zero-coupling JSON serialization. The FastAPI global exception handler in [src/promptlab/api/main.py:77-92](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/main.py#L77-L92) can return this exact dictionary without knowing the internal attributes of subclassed errors.

---

### 1.4 `src/promptlab/logging_config.py`
[src/promptlab/logging_config.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/logging_config.py)

- **Purpose in one sentence:** Configures structured JSON logging with asynchronous request correlation IDs and automated credential masking.
- **Public Classes and Functions:**
  - `request_id_ctx: ContextVar[str]`: Async context variable storing current request ID.
  - `def set_request_id(request_id: str) -> None`: Sets active trace ID in current async context.
  - `def get_request_id() -> str`: Reads active trace ID.
  - `def mask_sensitive_value(text: str) -> str`: Regular-expression search replacing API keys, tokens, and bearer credentials with `[REDACTED]`.
  - `class JSONLogFormatter(logging.Formatter)`: Formats `logging.LogRecord` as single-line JSON with ISO-8601 UTC timestamp and request ID.
  - `def configure_logging(level: str = "INFO") -> None`: Clears existing root logger handlers and installs `JSONLogFormatter` on a `StreamHandler`.
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* Log strings, log records.
  - *Outputs:* JSON strings on `sys.stderr`/`sys.stdout`.
  - *Side effects:* Mutates global `logging.getLogger()` root handlers.
- **Imports:**
  - *Imports from:* `contextvars`, `datetime`, `json`, `logging`, `re`, `typing`.
  - *Imported by:* [src/promptlab/api/main.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/main.py) and [tests/conftest.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/tests/conftest.py).
- **Design Pattern:** **Decorator / Interceptor Pattern** via custom `logging.Formatter` injecting thread-safe / coroutine-safe context.
- **Trickiest Line or Block:**
  ```python
  17: request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
  ```
  *Explanation:* In an asynchronous system (FastAPI with asyncio), standard thread-local storage (`threading.local()`) leaks across concurrent requests because multiple coroutines share the same OS thread. `ContextVar` ensures that when `asyncio.gather` or background tasks run, the trace ID remains bound strictly to the coroutine's async execution tree.

---

## Layer 2: Domain Entities

### 2.1 `src/promptlab/core/models.py`
[src/promptlab/core/models.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/models.py)

- **Purpose in one sentence:** Defines the core immutable domain models representing prompts, test cases, evaluation metrics, and safety findings.
- **Public Classes and Functions:**
  - `class GenerationParams(BaseModel)`: Immutable hyperparameters (`temperature`, `top_p`, `max_tokens`, `seed`).
  - `class LLMRequest(BaseModel)`: Prompt payload (`model`, `prompt`, `system_prompt`, `params`).
  - `class LLMResponse(BaseModel)`: Completion output (`text`, `model`, `latency_ms`, `prompt_tokens`, `completion_tokens`, `raw_finish_reason`).
  - `class ScoreResult(BaseModel)`: Scorer output (`score` [0.0–1.0], `passed`, `reason`, `metadata`).
  - `class TestCase(BaseModel)`: Single test item (`id`, `input`, `expected`, `scorer`, `scorer_config`, `tags`).
  - `class TestSuite(BaseModel)`: Collection of cases (`name`, `description`, `system_prompt`, `technique`, `technique_config`, `cases`).
  - `class CaseResult(BaseModel)`: Evaluated case (`case_id`, `response`, `score`, `passed`, `reason`, `error`).
  - `class RunResult(BaseModel)`: Aggregate run (`run_id`, `suite_name`, `model`, `params`, `technique`, `case_results`, `pass_rate`, `avg_latency_ms`, `total_tokens`, `created_at`).
  - `class SafetyReport(BaseModel)`: Safety audit (`injection_results`, `pii_findings`, `risk_level`, `passed`).
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* Typed dictionaries or keyword arguments.
  - *Outputs:* Validated Pydantic models.
  - *Side effects:* None (models have `frozen=True` where applicable).
- **Imports:**
  - *Imports from:* `pydantic`, `datetime`, `uuid`, `typing`.
  - *Imported by:* Every layer except `config`, `exceptions`, and `logging_config`.
- **Design Pattern:** **Value Object & Entity Pattern** (Domain-Driven Design).
- **Trickiest Line or Block:**
  ```python
  19: model_config = ConfigDict(frozen=True)
  ```
  *Explanation:* Applied to `GenerationParams`, `LLMRequest`, `LLMResponse`, and `ScoreResult`. Making them frozen renders them hashable, thread-safe, and prevents accidental mutation by scorers or runners downstream during concurrent execution.

---

## Layer 3: Providers (LLM Inference Adapters)

### 3.1 `src/promptlab/core/providers/base.py`
[src/promptlab/core/providers/base.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/providers/base.py)

- **Purpose in one sentence:** Declares the abstract base interface that all LLM inference adapters must satisfy.
- **Public Classes and Functions:**
  - `class LLMProvider(ABC)`: Abstract class.
    - `async def generate(self, request: LLMRequest) -> LLMResponse`: Abstract async completion method.
    - `async def list_models(self) -> list[str]`: Abstract async model catalog method.
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* `LLMRequest`.
  - *Outputs:* `LLMResponse`.
  - *Side effects:* Dictated by concrete subclasses.
- **Imports:**
  - *Imports from:* `abc`, `promptlab.core.models`.
  - *Imported by:* `factory.py`, `groq_provider.py`, `mock_provider.py`, `runner.py`, `services.*`.
- **Design Pattern:** **Interface Segregation / Abstract Adapter Contract** (GoF Adapter pattern target interface).
- **Trickiest Line or Block:**
  ```python
  21: @abstractmethod
  22: async def generate(self, request: LLMRequest) -> LLMResponse:
  ```
  *Explanation:* Mandates an asynchronous signature. Even synchronous or simulated providers must expose an `async` interface so callers (like `TestRunner`) can treat all providers uniformly via `await`.

---

### 3.2 `src/promptlab/core/providers/mock_provider.py`
[src/promptlab/core/providers/mock_provider.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/providers/mock_provider.py)

- **Purpose in one sentence:** Provides a deterministic, offline mock LLM implementation supporting simulated latencies, canned keyword responses, and controlled failure injection.
- **Public Classes and Functions:**
  - `class MockProvider(LLMProvider)`:
    - `def __init__(self, canned_responses: dict[str, str] | None = None, default_response: str | None = None, simulated_latency_ms: float = 5.0) -> None`
    - `def simulate_failure(self, count: int, error: Exception | None = None) -> None`: Queues simulated exceptions for the next `count` calls.
    - `def set_canned_response(self, keyword: str, response: str) -> None`: Maps prompt substring to deterministic output.
    - `async def generate(self, request: LLMRequest) -> LLMResponse`: Generates mock response with simulated sleep and token counts.
    - `async def list_models(self) -> list[str]`: Returns list of 4 mock model identifiers.
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* `LLMRequest`.
  - *Outputs:* `LLMResponse`.
  - *Side effects:* Calls `asyncio.sleep` to mimic network delay; decrements internal failure counters.
- **Imports:**
  - *Imports from:* `asyncio`, `time`, `typing`, `promptlab.core.models`, `promptlab.core.providers.base`, `promptlab.exceptions`.
  - *Imported by:* `factory.py`, unit and integration tests.
- **Design Pattern:** **Mock Object Pattern / Test Double**.
- **Trickiest Line or Block:**
  ```python
  68: if self._failure_count > 0:
  69:     self._failure_count -= 1
  70:     error = self._failure_error or ProviderError("Simulated mock failure")
  71:     raise error
  ```
  *Explanation:* Allows unit tests in [tests/unit/test_runner.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/tests/unit/test_runner.py) to simulate transient failures (e.g., fail 2 times then succeed) to verify that retry and error isolation logic in callers behaves correctly without mocking internal method calls.

---

### 3.3 `src/promptlab/core/providers/groq_provider.py`
[src/promptlab/core/providers/groq_provider.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/providers/groq_provider.py)

- **Purpose in one sentence:** Wraps the external Groq hosted inference SDK, implementing exponential backoff with full jitter to handle transient network errors and rate limits.
- **Public Classes and Functions:**
  - `class GroqProvider(LLMProvider)`:
    - `def __init__(self, api_key: str | None = None, max_retries: int = 3, base_backoff_seconds: float = 0.5, timeout_seconds: float = 60.0, client: Any = None) -> None`
    - `async def generate(self, request: LLMRequest) -> LLMResponse`: Executes chat completion with retries, measuring wall-clock latency.
    - `async def list_models(self) -> list[str]`: Calls Groq models API and returns model IDs.
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* `LLMRequest`.
  - *Outputs:* `LLMResponse`.
  - *Side effects:* Network HTTPS requests to `api.groq.com`; warning logs on retry attempts.
- **Imports:**
  - *Imports from:* `asyncio`, `logging`, `random`, `time`, `groq`, `promptlab.config`, `promptlab.core.models`, `promptlab.exceptions`.
  - *Imported by:* `factory.py`.
- **Design Pattern:** **Adapter Pattern** (adapting `groq.AsyncGroq` to `LLMProvider`) combined with **Retry with Exponential Backoff and Jitter**.
- **Trickiest Line or Block:**
  ```python
  70: exponential = self._base_backoff_seconds * (2**attempt)
  71: jitter = random.uniform(0.05, 0.25)
  72: return round(exponential + jitter, 3)
  ```
  *Explanation:* Pure exponential backoff (`0.5s, 1.0s, 2.0s`) causes concurrent test tasks to retry at the exact same millisecond, creating a "thundering herd" problem that exacerbates 429 rate limits. Adding randomized jitter spreads retries evenly across time windows.

---

### 3.4 `src/promptlab/core/providers/factory.py`
[src/promptlab/core/providers/factory.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/providers/factory.py)

- **Purpose in one sentence:** Provides a dynamic registry and factory for instantiating LLM providers by string identifier without hardcoding provider classes.
- **Public Classes and Functions:**
  - `class ProviderFactory`:
    - `register(cls, name: str) -> Callable`: Decorator for registering a provider class.
    - `register_provider(cls, name: str, provider_cls: type[LLMProvider]) -> None`: Direct registration method.
    - `create(cls, name: str, **kwargs: Any) -> LLMProvider`: Instantiates and returns provider by key.
    - `list_providers(cls) -> list[str]`: Returns sorted registered provider names.
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* Provider name (`"groq"`, `"mock"`).
  - *Outputs:* Concrete `LLMProvider` instance.
  - *Side effects:* None. Raises `ProviderNotFoundError` if unregistered.
- **Imports:**
  - *Imports from:* `collections.abc`, `typing`, `promptlab.core.providers.base`, `groq_provider`, `mock_provider`, `promptlab.exceptions`.
  - *Imported by:* `services.evaluation_service`, `services.safety_service`, `api.routes.models`, `core.scorers.llm_judge`.
- **Design Pattern:** **Factory Pattern & Registry Pattern**.
- **Trickiest Line or Block:**
  ```python
  54: lookup = name.lower()
  55: if lookup not in cls._registry:
  56:     raise ProviderNotFoundError(name)
  57: provider_cls = cls._registry[lookup]
  58: return provider_cls(**kwargs)
  ```
  *Explanation:* Forwards arbitrary `**kwargs` directly into the constructor of `provider_cls`. This enables unit tests to inject mock clients or custom API keys via `create("groq", client=mock_client)` without altering the factory signature.

---

### 3.5 `src/promptlab/core/providers/__init__.py`
[src/promptlab/core/providers/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/providers/__init__.py)

- **Purpose in one sentence:** Exposes public provider classes and factory from the providers sub-package.
- **Public Classes and Functions:**
  - Exports `LLMProvider`, `GroqProvider`, `MockProvider`, `ProviderFactory`.
- **Imports, Outputs, Side Effects:** Standard module re-exports.

---

## Layer 4: Prompt Engineering Techniques (Strategies)

### 4.1 `src/promptlab/core/techniques/base.py`
[src/promptlab/core/techniques/base.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/techniques/base.py)

- **Purpose in one sentence:** Defines the Strategy pattern interface for prompt techniques that format user queries and system prompts.
- **Public Classes and Functions:**
  - `class PromptTechnique(ABC)`:
    - `apply(self, case_input: str, config: dict[str, Any]) -> tuple[str | None, str]`: Abstract method returning `(system_prompt_addition, formatted_user_prompt)`.
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* Raw case prompt string and technique config dictionary.
  - *Outputs:* Tuple of optional system instruction and modified user prompt.
  - *Side effects:* None.
- **Imports:**
  - *Imports from:* `abc`, `typing`.
  - *Imported by:* Subclasses (`zero_shot.py`, etc.), `registry.py`, `runner.py`.
- **Design Pattern:** **Strategy Pattern** (base interface).
- **Trickiest Line or Block:**
  ```python
  22: ) -> tuple[str | None, str]:
  ```
  *Explanation:* Returning a 2-tuple separates instructions intended for the model's high-priority `system` channel from input data placed in the `user` channel.

---

### 4.2 `src/promptlab/core/techniques/zero_shot.py`
[src/promptlab/core/techniques/zero_shot.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/techniques/zero_shot.py)

- **Purpose in one sentence:** Baseline prompt technique passing the input directly without examples or reasoning guidance.
- **Public Classes and Functions:**
  - `class ZeroShot(PromptTechnique)`: Method `apply(case_input, config) -> (None, case_input)`.
- **Imports, Outputs, Side Effects:** Pure function, zero side effects.
- **Design Pattern:** Concrete **Strategy**.

---

### 4.3 `src/promptlab/core/techniques/few_shot.py`
[src/promptlab/core/techniques/few_shot.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/techniques/few_shot.py)

- **Purpose in one sentence:** Formats demonstration input/output pairs and prepends them to the user prompt for in-context learning.
- **Public Classes and Functions:**
  - `class FewShot(PromptTechnique)`: Method `apply(case_input, config) -> (system_addition, user_prompt_with_examples)`.
- **Inputs, Outputs, and Side Effects:**
  - *Inputs:* Raw prompt and config containing `"examples"` list of dicts.
  - *Outputs:* Formatted example prompt blocks.
  - *Side effects:* None.
- **Design Pattern:** Concrete **Strategy**.
- **Trickiest Line or Block:**
  ```python
  46: user_prompt = f"{examples_text}\n\nInput: {case_input}\nOutput:"
  ```
  *Explanation:* Concludes with an open `Output:` token prompt, priming autoregressive LLMs to complete the pattern naturally.

---

### 4.4 `src/promptlab/core/techniques/chain_of_thought.py`
[src/promptlab/core/techniques/chain_of_thought.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/techniques/chain_of_thought.py)

- **Purpose in one sentence:** Enforces step-by-step intermediate reasoning in prompts and isolates the final answer token using delimiter extraction.
- **Public Classes and Functions:**
  - `class ChainOfThought(PromptTechnique)`:
    - `apply(self, case_input: str, config: dict[str, Any]) -> tuple[str | None, str]`: Injects reasoning instructions and delimiter requirements.
    - `extract_answer(output: str) -> str`: Static regex parser extracting answer following the `'Answer:'` delimiter.
- **Inputs, Outputs, and Side Effects:** String transformations; pure functions.
- **Design Pattern:** Concrete **Strategy** with parsing utility.
- **Trickiest Line or Block:**
  ```python
  46: match = re.search(r"(?:Answer|ANSWER):\s*(.+)$", output.strip(), re.MULTILINE)
  51: lines = [line.strip() for line in output.strip().splitlines() if line.strip()]
  52: return lines[-1] if lines else output.strip()
  ```
  *Explanation:* Robust fallback parser. If the model disregards instructions and fails to write `Answer:`, line 51 extracts the final non-empty line of text, preventing false scoring rejections when reasoning concludes naturally on the last line.

---

### 4.5 `src/promptlab/core/techniques/structured_output.py`
[src/promptlab/core/techniques/structured_output.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/techniques/structured_output.py)

- **Purpose in one sentence:** Injects JSON schema constraints into system prompts and formats targeted repair prompts for malformed JSON outputs.
- **Public Classes and Functions:**
  - `class StructuredOutput(PromptTechnique)`:
    - `apply(self, case_input: str, config: dict[str, Any]) -> tuple[str | None, str]`: Serializes schema into system prompt.
    - `format_repair_prompt(malformed_output: str, error_msg: str) -> str`: Generates targeted JSON fix prompt.
- **Design Pattern:** Concrete **Strategy**.
- **Trickiest Line or Block:**
  ```python
  25: schema_repr = json.dumps(schema, indent=2) if isinstance(schema, dict) else str(schema or "{}")
  ```
  *Explanation:* Normalizes both parsed Python dictionaries and raw string schemas passed by users in the UI, ensuring formatting consistency.

---

### 4.6 `src/promptlab/core/techniques/registry.py`
[src/promptlab/core/techniques/registry.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/techniques/registry.py)

- **Purpose in one sentence:** Central factory and registry for dynamically looking up and registering prompt engineering strategies.
- **Public Classes and Functions:**
  - `class TechniqueRegistry`:
    - `register(cls, name: str) -> Callable`: Decorator.
    - `register_technique(cls, name: str, technique_cls: type[PromptTechnique]) -> None`: Direct registration.
    - `get(cls, name: str) -> PromptTechnique`: Returns strategy instance.
    - `list_techniques(cls) -> list[str]`: Returns list of registered keys.
- **Design Pattern:** **Registry Pattern**.
- **Trickiest Line or Block:**
  ```python
  60: return cls._registry[lookup]()
  ```
  *Explanation:* Instantiates a fresh instance of the technique upon every call to `get()`, ensuring no state is shared between test runs.

---

### 4.7 `src/promptlab/core/techniques/__init__.py`
[src/promptlab/core/techniques/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/techniques/__init__.py)

- **Purpose in one sentence:** Exposes all concrete prompt techniques and the `TechniqueRegistry`.
- Standard re-export module.

---

## Layer 5: Evaluation Scorers (Template Method Hierarchy)

### 5.1 `src/promptlab/core/scorers/base.py`
[src/promptlab/core/scorers/base.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/base.py)

- **Purpose in one sentence:** Implements the Template Method pattern defining an invariant 3-step evaluation lifecycle: preprocessing, evaluation, and post-finalization clamping.
- **Public Classes and Functions:**
  - `class BaseScorer(ABC)`:
    - `score(self, case: TestCase, output: str) -> ScoreResult`: Synchronous template method.
    - `async def score_async(self, case: TestCase, output: str) -> ScoreResult`: Asynchronous template method.
    - `_preprocess(self, output: str) -> str`: Trims whitespace.
    - `_finalize(self, result: ScoreResult) -> ScoreResult`: Clamps score to `[0.0, 1.0]`.
    - `_evaluate(self, case: TestCase, output: str) -> ScoreResult`: Abstract sync hook.
    - `_evaluate_async(self, case: TestCase, output: str) -> ScoreResult`: Async hook defaulting to `_evaluate`.
- **Design Pattern:** **Template Method Pattern**.
- **Trickiest Line or Block:**
  ```python
  26: clamped = max(0.0, min(1.0, float(result.score)))
  ```
  *Explanation:* Guarantees mathematical score bounds across all subclasses, preventing faulty third-party scorers from returning negative scores or scores exceeding 1.0.

---

### 5.2 `src/promptlab/core/scorers/exact_match.py`
[src/promptlab/core/scorers/exact_match.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/exact_match.py)

- **Purpose in one sentence:** Compares model completion against expected reference text with configurable casing and whitespace collapse options.
- **Public Classes and Functions:**
  - `class ExactMatch(BaseScorer)`: Overrides `_evaluate(case, output) -> ScoreResult`.
- **Trickiest Line or Block:**
  ```python
  35: actual_cmp = re.sub(r"\s+", " ", actual_cmp).strip()
  ```
  *Explanation:* Replaces multi-line tabs, spaces, and line breaks with single space tokens when `ignore_whitespace=True`, preventing indentation differences from failing exact match tests.

---

### 5.3 `src/promptlab/core/scorers/contains.py`
[src/promptlab/core/scorers/contains.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/contains.py)

- **Purpose in one sentence:** Checks for presence of target substrings supporting conjunctive (`all`) and disjunctive (`any`) match modes.
- **Public Classes and Functions:**
  - `class Contains(BaseScorer)`: Overrides `_evaluate(case, output) -> ScoreResult`.
- **Trickiest Line or Block:**
  ```python
  62: score = len(found) / len(targets)
  63: passed = len(missing) == 0
  ```
  *Explanation:* Implements partial scoring. In `all` mode, finding 2 out of 4 targets yields a score of `0.5`, but `passed` is strictly `False` because not all required tokens appeared.

---

### 5.4 `src/promptlab/core/scorers/regex_match.py`
[src/promptlab/core/scorers/regex_match.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/regex_match.py)

- **Purpose in one sentence:** Verifies whether completion text matches a configured regular expression pattern with flag support.
- **Public Classes and Functions:**
  - `class RegexMatch(BaseScorer)`: Overrides `_evaluate(case, output) -> ScoreResult`.
- **Trickiest Line or Block:**
  ```python
  37: except re.error as err:
  ```
  *Explanation:* Gracefully catches malformed regex patterns provided in user configs, returning a `score=0.0` with diagnostic metadata rather than crashing the evaluation runner.

---

### 5.5 `src/promptlab/core/scorers/json_valid.py`
[src/promptlab/core/scorers/json_valid.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/json_valid.py)

- **Purpose in one sentence:** Verifies that model completion is syntactically valid JSON, automatically stripping markdown code fences (` ```json `).
- **Public Classes and Functions:**
  - `class JsonValid(BaseScorer)`: Overrides `_evaluate(case, output) -> ScoreResult`.
- **Trickiest Line or Block:**
  ```python
  22: fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
  ```
  *Explanation:* Extracts payload from markdown fences using non-greedy dotall `[\s\S]*?`, addressing the common LLM tendency to wrap JSON in markdown formatting despite explicit instructions not to.

---

### 5.6 `src/promptlab/core/scorers/json_schema.py`
[src/promptlab/core/scorers/json_schema.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/json_schema.py)

- **Purpose in one sentence:** Validates parsed JSON completions against a formal JSON Schema Draft specification.
- **Public Classes and Functions:**
  - `class JsonSchema(BaseScorer)`: Overrides `_evaluate(case, output) -> ScoreResult`.
- **Trickiest Line or Block:**
  ```python
  59: except JsonSchemaValidationError as val_err:
  63:     reason=f"Schema validation error at '{val_err.json_path}': {val_err.message}"
  ```
  *Explanation:* Captures the exact JSONPath where validation broke (e.g., `$.sentiment`), providing actionable debugging context back to the user.

---

### 5.7 `src/promptlab/core/scorers/sql_result.py`
[src/promptlab/core/scorers/sql_result.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/sql_result.py)

- **Purpose in one sentence:** Executes model-generated SQL against a sandboxed in-memory SQLite database, enforcing strict zero-trust AST checks to block destructive or stacked queries.
- **Public Classes and Functions:**
  - `class SqlResult(BaseScorer)`:
    - `_extract_sql(self, text: str) -> str`
    - `_validate_sql_safety(self, sql: str) -> None`: Raises `SecurityError` on non-SELECT statements.
    - `_init_in_memory_db(self) -> sqlite3.Connection`: Creates `:memory:` SQLite seeded from sample schema.
    - `_evaluate(self, case: TestCase, output: str) -> ScoreResult`: Executes and compares result sets.
- **Design Pattern:** Concrete **Template Method** with security sandbox filter.
- **Trickiest Line or Block:**
  ```python
  64: statements = [s.strip() for s in sql.split(";") if s.strip()]
  65: if len(statements) > 1:
  66:     raise SecurityError("Stacked SQL queries are prohibited.")
  77: if first_token not in {"SELECT", "WITH"}:
  78:     raise SecurityError(f"Unauthorized SQL command '{first_token}'.")
  ```
  *Explanation:* Defense-in-depth SQL sanitization. Semicolon splitting prevents stacked injection (`SELECT 1; DROP TABLE users;`), and first-token whitelisting ensures only query operations (`SELECT`, `WITH`) can execute against the SQLite sandbox.

---

### 5.8 `src/promptlab/core/scorers/llm_judge.py`
[src/promptlab/core/scorers/llm_judge.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/llm_judge.py)

- **Purpose in one sentence:** Employs an independent evaluator LLM to assess candidate completions against qualitative rubrics with zero temperature sampling.
- **Public Classes and Functions:**
  - `class LLMJudge(BaseScorer)`:
    - `__init__(judge_provider: LLMProvider | None = None, judge_model: str | None = None)`
    - `async _evaluate_async(case: TestCase, output: str) -> ScoreResult`: Asynchronous judge execution.
    - `_evaluate(case: TestCase, output: str) -> ScoreResult`: Synchronous placeholder forcing async usage.
- **Design Pattern:** Concrete **Template Method** with asynchronous remote I/O delegation.
- **Trickiest Line or Block:**
  ```python
  81: passed = clamped_score >= 0.7
  105: params=GenerationParams(temperature=0.0, max_tokens=500),
  ```
  *Explanation:* Enforces `temperature=0.0` for deterministic grading to mitigate stochastic drift. Sets a passing threshold of `0.7` to account for LLM central-tendency compression.

---

### 5.9 `src/promptlab/core/scorers/registry.py`
[src/promptlab/core/scorers/registry.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/registry.py)

- **Purpose in one sentence:** Central registry and factory for all evaluation scorers.
- **Public Classes and Functions:**
  - `class ScorerRegistry`:
    - `register(cls, name: str) -> Callable`
    - `register_scorer(cls, name: str, scorer_cls: type[BaseScorer]) -> None`
    - `get(cls, name: str, **kwargs: Any) -> BaseScorer`
    - `list_scorers(cls) -> list[str]`
- **Design Pattern:** **Registry Pattern & Factory Pattern**.

---

### 5.10 `src/promptlab/core/scorers/__init__.py`
[src/promptlab/core/scorers/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/__init__.py)

- **Purpose in one sentence:** Exports all concrete scorers and the `ScorerRegistry`.
- Standard re-export module.

---

## Layer 6: Safety, Guardrails & Adversarial Audits

### 6.1 `src/promptlab/core/safety/pii_detector.py`
[src/promptlab/core/safety/pii_detector.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/safety/pii_detector.py)

- **Purpose in one sentence:** Detects, classifies, and redacts sensitive entities (PII, Indian & international phone numbers, credit cards verified via Luhn algorithm, API keys, and IPv4 addresses).
- **Public Classes and Functions:**
  - `def validate_luhn(card_number_str: str) -> bool`: Validates payment cards using the Mod 10 checksum.
  - `class PIIDetector`:
    - `scan(self, text: str) -> list[dict[str, Any]]`: Returns list of findings with category, detector, and offset spans.
    - `redact(self, text: str) -> str`: Replaces detected items with masked snippets from back to front.
    - `has_pii(self, text: str) -> bool`: Convenience boolean check.
- **Inputs, Outputs, and Side Effects:** Pure string analysis and regex execution; zero side effects.
- **Trickiest Line or Block:**
  ```python
  173: sorted_findings = sorted(findings, key=lambda f: int(f["start"]), reverse=True)
  174: result = text
  175: for finding in sorted_findings:
  176:     start = int(finding["start"])
  177:     end = int(finding["end"])
  178:     snippet = str(finding["snippet"])
  179:     result = result[:start] + snippet + result[end:]
  ```
  *Explanation:* Reverse-index string replacement. Replacing substrings from the beginning changes character indices for all subsequent matches, corrupting their `start`/`end` positions. Sorting matches in reverse order (`reverse=True`) guarantees that earlier slice indices remain unaffected by downstream insertions.

---

### 6.2 `src/promptlab/core/safety/guardrail.py`
[src/promptlab/core/safety/guardrail.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/safety/guardrail.py)

- **Purpose in one sentence:** Combines PII detection with multi-factor risk categorization (`low`, `medium`, `high`) to filter and sanitize payloads.
- **Public Classes and Functions:**
  - `class Guardrail`:
    - `check_text(self, text: str) -> SafetyReport`: Assesses risk and returns report.
    - `filter_text(self, text: str, redact: bool = True) -> tuple[bool, str, SafetyReport]`: Returns `(is_safe, sanitized_text, report)`.
- **Trickiest Line or Block:**
  ```python
  29: has_critical = any(f.get("type") in {"api_key", "credit_card"} for f in pii_findings)
  32: if has_critical or len(pii_findings) >= 3:
  33:     return "high"
  ```
  *Explanation:* Differential severity weighting. Finding an email or phone number is categorized as `medium` risk, but any exposed API key or valid credit card instantly triggers `high` risk, causing `filter_text` to flag `is_safe=False`.

---

### 6.3 `src/promptlab/core/safety/injection_suite.py`
[src/promptlab/core/safety/injection_suite.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/safety/injection_suite.py)

- **Purpose in one sentence:** Evaluates model resistance against 16 prompt-injection attacks across 5 categories by planting and detecting canary secret leakage.
- **Public Classes and Functions:**
  - `class InjectionSuite`:
    - `load_attacks(self) -> list[dict[str, Any]]`: Reads `injection_prompts.json`.
    - `async run_suite(self, provider: LLMProvider, model: str, canary: str | None = None, max_concurrency: int = 5) -> dict[str, Any]`: Concurrently executes attacks under semaphore control and aggregates breach metrics.
- **Trickiest Line or Block:**
  ```python
  52: if canary.lower() in lower_output:
  53:     return (True, f"Canary token '{canary}' was successfully leaked in output.")
  55: for indicator in attack.get("success_indicators", []):
  56:     if str(indicator).lower() in lower_output:
  57:         return (True, f"Attack succeeded via indicator trigger: '{indicator}'.")
  ```
  *Explanation:* Dual breach verification. Even if the victim model does not leak the exact canary string, matching attack-specific success indicators (e.g., `root_admin mode enabled` or `system reset complete`) flags the model as compromised.

---

### 6.4 `src/promptlab/core/safety/__init__.py`
[src/promptlab/core/safety/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/safety/__init__.py)

- **Purpose in one sentence:** Re-exports `PIIDetector`, `validate_luhn`, `InjectionSuite`, and `Guardrail`.
- Standard re-export module.

---

## Layer 7: Core Orchestration Runner & Package Root

### 7.1 `src/promptlab/core/runner.py`
[src/promptlab/core/runner.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/runner.py)

- **Purpose in one sentence:** Concurrently executes evaluation test cases bounded by an `asyncio.Semaphore`, combining system prompts with techniques and isolating individual case failures.
- **Public Classes and Functions:**
  - `class TestRunner`:
    - `__init__(provider: LLMProvider, technique: PromptTechnique | str = "zero_shot", scorer_registry: ScorerRegistry | None = None, settings: Settings | None = None)`
    - `async run_suite(self, suite: TestSuite, model: str, params: GenerationParams | None = None) -> RunResult`: Concurrently runs suite cases and computes pass rate, latency, and tokens.
    - `async run_matrix(self, suite: TestSuite, models: list[str], param_sets: list[GenerationParams] | None = None) -> list[RunResult]`: Parameter sweep over models and configurations.
- **Design Pattern:** **Orchestrator / Coordinator Pattern**.
- **Trickiest Line or Block:**
  ```python
  107: except Exception as exc:
  108:     logger.error("Error evaluating test case '%s': %s", case.id, exc)
  109:     fallback_response = LLMResponse(
  110:         text="", model=model, latency_ms=0.0, prompt_tokens=0, completion_tokens=0, raw_finish_reason="error"
  111:     )
  112:     return CaseResult(case_id=case.id, response=fallback_response, score=0.0, passed=False, reason=f"Evaluation failed due to exception: {exc}", error=str(exc))
  ```
  *Explanation:* Partial failure containment. By catching all exceptions inside `_evaluate_single_case` and returning a failed `CaseResult` with `score=0.0`, an unexpected network timeout on 1 case will never crash the remaining 49 cases in an evaluation suite.

---

### 7.2 `src/promptlab/core/__init__.py`
[src/promptlab/core/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/__init__.py)

- **Purpose in one sentence:** Decoupled entrypoint exposing all domain models, provider adapters, techniques, scorers, safety analyzers, and the runner.
- Public facade for the entire `promptlab.core` domain library.

---

## Layer 8: Database & Persistence Layer

### 8.1 `src/promptlab/db/base.py`
[src/promptlab/db/base.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/db/base.py)

- **Purpose in one sentence:** Manages SQLAlchemy 2.0 async engine creation, session factory configuration, table initialization, and context-managed sessions.
- **Public Classes and Functions:**
  - `class Base(DeclarativeBase)`: Declarative root for typed ORM models.
  - `def get_engine(database_url: str | None = None) -> AsyncEngine`: Engine singleton.
  - `def get_session_factory(...) -> async_sessionmaker[AsyncSession]`: Factory singleton.
  - `async def init_db(engine: AsyncEngine | None = None) -> None`: Runs `create_all`.
  - `async def get_session() -> AsyncGenerator[AsyncSession, None]`: Context manager with automated rollback on exception and commit on clean exit.
- **Design Pattern:** **Unit of Work Pattern** (via SQLAlchemy `AsyncSession`).
- **Trickiest Line or Block:**
  ```python
  69: async with factory() as session:
  70:     try:
  71:         yield session
  72:         await session.commit()
  73:     except Exception:
  74:         await session.rollback()
  75:         raise
  ```
  *Explanation:* Safe atomic transaction boundary. If an unhandled error occurs anywhere inside the `async with get_session()` block, `session.rollback()` is automatically invoked before re-raising the exception.

---

### 8.2 `src/promptlab/db/orm_models.py`
[src/promptlab/db/orm_models.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/db/orm_models.py)

- **Purpose in one sentence:** Defines relational database tables (`suites`, `runs`, `case_results`, `safety_reports`) using SQLAlchemy 2.0 typed mappings.
- **Public Classes and Functions:**
  - `class SuiteModel(Base)`: Table `suites`.
  - `class RunModel(Base)`: Table `runs`. Index on `("suite_name", "created_at")`.
  - `class CaseResultModel(Base)`: Table `case_results`. Foreign key to `runs.id` with `ondelete="CASCADE"`.
  - `class SafetyReportModel(Base)`: Table `safety_reports`.
- **Trickiest Line or Block:**
  ```python
  72: case_results: Mapped[list["CaseResultModel"]] = relationship(
  73:     "CaseResultModel", back_populates="run", cascade="all, delete-orphan"
  74: )
  ```
  *Explanation:* Enforces cascade delete-orphan semantics. Deleting a `RunModel` automatically deletes all associated granular `CaseResultModel` rows without leaving orphaned foreign key records.

---

### 8.3 `src/promptlab/db/repositories.py`
[src/promptlab/db/repositories.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/db/repositories.py)

- **Purpose in one sentence:** Encapsulates all persistence and query logic, translating between SQLAlchemy ORM models and pure Pydantic domain models.
- **Public Classes and Functions:**
  - `class SuiteRepository`: Methods: `save(suite, suite_id)`, `get_by_id(suite_id)`, `get_by_name(name)`, `list(offset, limit)`, `delete(suite_id)`.
  - `class RunRepository`: Methods: `save(run, suite_id)`, `get_by_id(run_id)`, `list(offset, limit, suite_name, model)`, `delete(run_id)`.
  - `class SafetyRepository`: Methods: `save(report, model)`, `get_by_id(report_id)`, `list(offset, limit)`.
- **Design Pattern:** **Repository Pattern**.
- **Trickiest Line or Block:**
  ```python
  177: .options(selectinload(RunModel.case_results))
  ```
  *Explanation:* Avoids the N+1 select problem. Using `selectinload` instructs SQLAlchemy to load all related `case_results` in a single secondary SQL query using an `IN (...)` clause rather than issuing individual select statements per row.

---

### 8.4 `src/promptlab/db/__init__.py`
[src/promptlab/db/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/db/__init__.py)

- **Purpose in one sentence:** Re-exports database base classes, ORM models, and repositories.
- Standard re-export module.

---

## Layer 9: Service Facades & Business Logic

### 9.1 `src/promptlab/services/comparison_service.py`
[src/promptlab/services/comparison_service.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/services/comparison_service.py)

- **Purpose in one sentence:** Aligns multi-run evaluation results into side-by-side matrices and calculates competitive leaderboards.
- **Public Classes and Functions:**
  - `class ComparisonService`:
    - `async def compare_runs_by_ids(self, run_ids: list[str]) -> dict[str, Any]`
    - `def compare_runs(self, runs: list[RunResult]) -> dict[str, Any]`
- **Trickiest Line or Block:**
  ```python
  65: for cid in all_case_ids:
  66:     row: dict[str, Any] = {"case_id": cid, "runs": {}}
  67:     for r in runs:
  68:         cr = next((c for c in r.case_results if c.case_id == cid), None)
  ```
  *Explanation:* Outer-join alignment. Even if run A evaluated 10 cases and run B evaluated 8 cases, all unique case IDs are extracted, and missing cases in run B are safely populated as `None` rather than misaligning the matrix table.

---

### 9.2 `src/promptlab/services/evaluation_service.py`
[src/promptlab/services/evaluation_service.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/services/evaluation_service.py)

- **Purpose in one sentence:** Acts as the primary application facade coordinating test runners, repositories, provider factories, and persistence.
- **Public Classes and Functions:**
  - `class EvaluationService`:
    - CRUD methods: `create_suite`, `get_suite`, `list_suites`, `delete_suite`.
    - Run execution: `execute_run(suite_id_or_object, model, params, provider_name)`, `execute_matrix(...)`, `get_run`, `list_runs`.
- **Design Pattern:** **Facade Pattern**.
- **Trickiest Line or Block:**
  ```python
  79: if isinstance(suite_id_or_object, str):
  80:     suite_id, suite = await self.get_suite(suite_id_or_object)
  81: else:
  82:     suite = suite_id_or_object
  83:     suite_id = None
  ```
  *Explanation:* Polymorphic suite input. Enables executing runs against pre-registered database suites (by passing a string UUID) or against ephemeral ad-hoc suites authored on the fly in the playground (by passing a `TestSuite` object).

---

### 9.3 `src/promptlab/services/safety_service.py`
[src/promptlab/services/safety_service.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/services/safety_service.py)

- **Purpose in one sentence:** Coordinates adversarial prompt injection testing, PII scanning, and safety report storage.
- **Public Classes and Functions:**
  - `class SafetyService`:
    - `async def run_injection_test(self, model: str, canary: str | None = None, provider_name: str | None = None) -> dict[str, Any]`
    - `def scan_text(self, text: str) -> SafetyReport`
    - `async def get_report(self, report_id: str) -> dict[str, Any]`
    - `async def list_reports(self, offset: int = 0, limit: int = 50) -> tuple[list[dict[str, Any]], int]`
- **Design Pattern:** **Facade Pattern**.
- **Trickiest Line or Block:**
  ```python
  62: risk_level = "high" if breached > 0 else "low"
  ```
  *Explanation:* Conservative zero-tolerance safety threshold. If even a single prompt-injection attack out of 16 succeeds in extracting the canary token, the overall audit risk level is immediately escalated to `"high"`.

---

### 9.4 `src/promptlab/services/__init__.py`
[src/promptlab/services/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/services/__init__.py)

- **Purpose in one sentence:** Exports `EvaluationService`, `ComparisonService`, and `SafetyService`.
- Standard re-export module.

---

## Layer 10: API Layer (FastAPI)

### 10.1 `src/promptlab/api/schemas.py`
[src/promptlab/api/schemas.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/schemas.py)

- **Purpose in one sentence:** Declares Pydantic Data Transfer Objects (DTOs) for incoming HTTP request payloads and outgoing responses.
- **Public Classes and Functions:**
  - `HealthResponse`, `ModelsResponse`, `SuiteCreateRequest`, `SuiteResponse`, `SuiteListResponse`, `RunExecuteRequest`, `RunListResponse`, `CompareRequest`, `CompareResponse`, `InjectionTestRequest`, `ScanTextRequest`, `ScanTextResponse`, `SafetyReportListResponse`, `ErrorResponse`.
- **Trickiest Line or Block:**
  ```python
  83: @model_validator(mode="after")
  84: def validate_suite_source(self) -> "RunExecuteRequest":
  85:     if not self.suite_id and not self.suite:
  86:         raise ValueError("Either suite_id or inline suite must be provided.")
  87:     return self
  ```
  *Explanation:* Cross-field validation enforcing mutual presence: guarantees that a client must supply either an existing suite ID or an inline suite payload, rejecting ambiguous empty payloads with an HTTP 422.

---

### 10.2 `src/promptlab/api/dependencies.py`
[src/promptlab/api/dependencies.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/dependencies.py)

- **Purpose in one sentence:** Provides FastAPI dependency injection providers for scoped database sessions, repositories, and services.
- **Public Classes and Functions:**
  - `async def get_db() -> AsyncGenerator[AsyncSession, None]`: Scoped session generator.
  - `def get_suite_repo(session: AsyncSession = Depends(get_db)) -> SuiteRepository`
  - `def get_run_repo(...) -> RunRepository`
  - `def get_safety_repo(...) -> SafetyRepository`
  - `def get_evaluation_service(...) -> EvaluationService`
  - `def get_comparison_service(...) -> ComparisonService`
  - `def get_safety_service(...) -> SafetyService`
- **Design Pattern:** **Dependency Injection (Inversion of Control)**.
- **Trickiest Line or Block:**
  ```python
  26: async def get_db() -> AsyncGenerator[AsyncSession, None]:
  27:     factory = get_session_factory()
  28:     async with factory() as session:
  29:         try:
  30:             yield session
  31:             await session.commit()
  32:         except Exception:
  33:             await session.rollback()
  34:             raise
  ```
  *Explanation:* Ties the transaction lifecycle to the HTTP request lifecycle. A database transaction begins when a route handler starts, commits when the handler returns cleanly, and rolls back if any exception is thrown.

---

### 10.3 `src/promptlab/api/routes/health.py`
[src/promptlab/api/routes/health.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/routes/health.py)

- **Purpose in one sentence:** Lightweight liveness and readiness probe endpoint verifying operational status, demo mode flag, and active provider.
- **Public Routes:** `GET /health -> HealthResponse`.
- **Side effects:** None (read-only).

---

### 10.4 `src/promptlab/api/routes/models.py`
[src/promptlab/api/routes/models.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/routes/models.py)

- **Purpose in one sentence:** Returns the list of supported LLM identifiers from the requested or active inference provider.
- **Public Routes:** `GET /models -> ModelsResponse`.
- **Side effects:** Network call to Groq API if not in demo mode.

---

### 10.5 `src/promptlab/api/routes/suites.py`
[src/promptlab/api/routes/suites.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/routes/suites.py)

- **Purpose in one sentence:** REST endpoints for creating, listing, retrieving, and deleting evaluation test suites.
- **Public Routes:** `POST /suites` (201 Created), `GET /suites`, `GET /suites/{suite_id}`, `DELETE /suites/{suite_id}`.
- **Side effects:** Database inserts, updates, and deletes on `suites` table.

---

### 10.6 `src/promptlab/api/routes/runs.py`
[src/promptlab/api/routes/runs.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/routes/runs.py)

- **Purpose in one sentence:** Endpoints for executing evaluation runs, listing historical runs, and generating comparative matrices.
- **Public Routes:** `POST /runs` (201 Created), `GET /runs`, `GET /runs/{run_id}`, `POST /runs/compare`.
- **Side effects:** Triggers LLM inference calls; writes `runs` and `case_results` records to DB.

---

### 10.7 `src/promptlab/api/routes/safety.py`
[src/promptlab/api/routes/safety.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/routes/safety.py)

- **Purpose in one sentence:** Endpoints for executing adversarial prompt injection audits, scanning text for PII/secrets, and inspecting safety reports.
- **Public Routes:** `POST /safety/injection-test`, `POST /safety/scan`, `GET /safety/reports`, `GET /safety/reports/{report_id}`.
- **Side effects:** Runs 16 adversarial LLM queries; writes `safety_reports` records to DB.

---

### 10.8 `src/promptlab/api/routes/__init__.py`
[src/promptlab/api/routes/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/routes/__init__.py)

- **Purpose in one sentence:** Aggregates health, models, suites, runs, and safety sub-routers into a master `api_router`.
- Standard route aggregation module.

---

### 10.9 `src/promptlab/api/main.py`
[src/promptlab/api/main.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/main.py)

- **Purpose in one sentence:** FastAPI application factory configuring CORS, request-ID tracking middleware, global exception handlers, lifespan database migration, and route mounting.
- **Public Classes and Functions:**
  - `def create_app() -> FastAPI`: Application factory.
  - `async def lifespan(app: FastAPI)`: Startup and shutdown lifecycle context manager.
  - `app = create_app()`: Module-level ASGI entrypoint.
- **Design Pattern:** **Application Factory Pattern**.
- **Trickiest Line or Block:**
  ```python
  64: header_req_id = request.headers.get("X-Request-ID")
  65: active_req_id = header_req_id if header_req_id else str(uuid.uuid4())
  66: set_request_id(active_req_id)
  ...
  73: response.headers["X-Request-ID"] = active_req_id
  ```
  *Explanation:* Distributed trace propagation. Reuses incoming client-supplied `X-Request-ID` or generates a UUID, binds it to the async context via `set_request_id()`, and writes it back into response headers so errors and logs can be correlated end-to-end.

---

### 10.10 `src/promptlab/api/__init__.py`
[src/promptlab/api/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/__init__.py)

- **Purpose in one sentence:** Exports the `create_app` factory function.
- Standard re-export module.

---

## Layer 11: Presentation Layer (Streamlit Dashboard)

### 11.1 `src/promptlab/dashboard/api_client.py`
[src/promptlab/dashboard/api_client.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/dashboard/api_client.py)

- **Purpose in one sentence:** Synchronous HTTP client encapsulating all REST API calls between Streamlit pages and the FastAPI backend.
- **Public Classes and Functions:**
  - `class APIClientError(PromptLabError)`: Raised when the backend is unreachable or returns an error.
  - `class PromptLabClient`:
    - `health()`, `list_models()`, `create_suite()`, `list_suites()`, `get_suite()`, `delete_suite()`, `execute_run()`, `list_runs()`, `get_run()`, `compare_runs()`, `run_injection_test()`, `scan_text()`, `list_safety_reports()`, `get_safety_report()`, `close()`.
- **Design Pattern:** **Client Facade / Remote Proxy Pattern**.
- **Trickiest Line or Block:**
  ```python
  46: if response.is_error:
  47:     msg = payload.get("message", f"HTTP {response.status_code} error from API server.")
  48:     raise APIClientError(message=str(msg), status_code=response.status_code, details=payload)
  ```
  *Explanation:* Translates remote HTTP error payloads directly into typed local `APIClientError` exceptions, ensuring that UI code catches domain errors cleanly instead of handling raw network status codes.

---

### 11.2 `src/promptlab/dashboard/app.py`
[src/promptlab/dashboard/app.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/dashboard/app.py)

- **Purpose in one sentence:** Main landing page for the Streamlit dashboard displaying backend connectivity status, inference provider KPIs, module navigation cards, and interview architecture highlights.
- **Key Widgets and State:**
  - Checks `client.health()`; displays status badges (`Online`/`Offline`), provider name (`GROQ`/`MOCK`), and demo mode status in responsive metric cards.

---

### 11.3 `src/promptlab/dashboard/pages/1_Playground.py`
[src/promptlab/dashboard/pages/1_Playground.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/dashboard/pages/1_Playground.py)

- **Purpose in one sentence:** Interactive prompt engineering lab for tweaking sampling hyperparameters, prompt techniques, and scorers on single-shot queries.
- **Key Widgets and State:**
  - Sidebar: model picker, sliders (`temperature`, `top_p`, `max_tokens`), technique selector (`zero_shot`, `few_shot`, `chain_of_thought`, `structured_output`).
  - Main area: system prompt, user prompt, scorer selector, expected output, run button.
- **Trickiest Line or Block:**
  ```python
  152: if "<thought>" in response_text and "</thought>" in response_text:
  153:     thought = response_text.split("<thought>")[1].split("</thought>")[0].strip()
  154:     final_ans = response_text.split("</thought>")[1].strip()
  ```
  *Explanation:* Dynamically renders Chain-of-Thought reasoning steps inside a collapsible Streamlit `expander` while displaying the final conclusion in a clean markdown codeblock.

---

### 11.4 `src/promptlab/dashboard/pages/2_Test_Suites.py`
[src/promptlab/dashboard/pages/2_Test_Suites.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/dashboard/pages/2_Test_Suites.py)

- **Purpose in one sentence:** Suite management and batch evaluation runner allowing users to author test suites in JSON, run evaluations, and inspect pass rates and case breakdowns.
- **Key Widgets and State:**
  - Three tabs: "Run Suite", "Create Suite", "Manage Existing Suites".
  - Displays summary metric bars (`Pass Rate`, `Avg Latency`, `Total Tokens`, `Cases Evaluated`) and collapsible per-case breakdown drawers.

---

### 11.5 `src/promptlab/dashboard/pages/3_Safety_&_Guardrails.py`
[src/promptlab/dashboard/pages/3_Safety_&_Guardrails.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/dashboard/pages/3_Safety_&_Guardrails.py)

- **Purpose in one sentence:** Visual dashboard for executing adversarial prompt injection audits, scanning text payloads for PII/credentials with live redaction, and reviewing historical audit reports.
- **Key Widgets and State:**
  - Three tabs: "Adversarial Injection Audit", "Real-time PII & Secrets Scanner", "Historical Safety Reports".
  - Quick-load sample buttons: "Load Leaky Sample" vs "Load Safe Sample" for live demonstrations.

---

### 11.6 `src/promptlab/dashboard/pages/4_History_&_Comparison.py`
[src/promptlab/dashboard/pages/4_History_&_Comparison.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/dashboard/pages/4_History_&_Comparison.py)

- **Purpose in one sentence:** Explorer for historical evaluation runs providing multi-run side-by-side matrices, leaderboards for top pass rates and latencies, and search filtering.
- **Key Widgets and State:**
  - Two tabs: "Side-by-Side Comparison", "Historical Run Explorer".
  - Multi-select picker allowing selection of 2 or more historical runs to render competitive comparison tables and aligned case matrices.

---

### 11.7 `src/promptlab/dashboard/__init__.py`
[src/promptlab/dashboard/__init__.py](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/dashboard/__init__.py)

- **Purpose in one sentence:** Re-exports `PromptLabClient` from the dashboard package.
- Standard re-export module.

---

## Gaps, Code Smells & Missing Elements

Based on the line-by-line inspection of all 58 source files, here is an objective catalog of weak spots, code smells, and potential technical interview discussion points:

1. **Private Attribute Access Across Layers:**
   In [src/promptlab/api/routes/safety.py:44](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/routes/safety.py#L44), the endpoint invokes `safety_service._guardrail.filter_text(payload.text)`. Reaching into a private member (`_guardrail`) breaks encapsulation; `SafetyService` should expose a public `filter_text()` facade method.
2. **Missing Service Wrapper in Models Route:**
   In [src/promptlab/api/routes/models.py:23](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/api/routes/models.py#L23), the endpoint calls `ProviderFactory.create(target_provider).list_models()` directly, bypassing the service layer entirely.
3. **Fragile Relative Path Traversal for Seed Data:**
   In [src/promptlab/core/scorers/sql_result.py:48](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/sql_result.py#L48) and [src/promptlab/core/safety/injection_suite.py:26](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/safety/injection_suite.py#L26), file paths are computed as `Path(__file__).resolve().parents[3] / "data"`. If PromptLab is installed as a wheel in `site-packages`, this relative traversal fails because `data/` is not inside `src/`.
4. **Synchronous Fallback Inconsistency in `LLMJudge`:**
   In [src/promptlab/core/scorers/llm_judge.py:111-117](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/core/scorers/llm_judge.py#L111-L117), `LLMJudge` implements the synchronous `_evaluate()` hook by simply returning `ScoreResult(score=0.0, passed=False, reason="LLMJudge requires asynchronous execution via score_async()")`. If an external caller calls `scorer.score()` synchronously instead of `score_async()`, it silently fails with a 0 score rather than raising an informative `NotImplementedError`.
5. **No Database Migration Tooling (Alembic):**
   The application initializes schemas via `conn.run_sync(Base.metadata.create_all)` in [src/promptlab/db/base.py:62](file:///c:/Users/vedaa/OneDrive/Desktop/Master%20Folder/promptLab/src/promptlab/db/base.py#L62). While suitable for SQLite prototypes and demo mode, production databases require Alembic for zero-downtime schema migrations.
