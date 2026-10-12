"""Database seeding script for PromptLab benchmark suites and baseline evaluation runs.

This script initializes database schemas and populates:
- Pre-built benchmark test suites (Text-to-SQL, Sentiment Classification, Math CoT).
- Baseline evaluation runs across mock models to seed comparison leaderboards.
- Baseline adversarial prompt injection security audit.
"""

import asyncio
import json
import logging
from pathlib import Path
import sys

from promptlab.config import get_settings
from promptlab.core.models import GenerationParams, TestSuite
from promptlab.db.base import get_session, init_db
from promptlab.db.repositories import RunRepository, SafetyRepository, SuiteRepository
from promptlab.services.evaluation_service import EvaluationService
from promptlab.services.safety_service import SafetyService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_db")


async def seed() -> None:
    """Execute database table initialization and benchmark suite seeding."""
    logger.info("Initializing database schema...")
    await init_db()

    data_path = Path(__file__).resolve().parent.parent / "data" / "benchmark_suites.json"
    if not data_path.exists():
        logger.error("Benchmark suites file not found at: %s", data_path)
        sys.exit(1)

    with open(data_path, encoding="utf-8") as f:
        suites_raw = json.load(f)

    logger.info("Seeding %d benchmark test suites...", len(suites_raw))

    async with get_session() as session:
        suite_repo = SuiteRepository(session)
        run_repo = RunRepository(session)
        safety_repo = SafetyRepository(session)

        settings = get_settings()
        eval_service = EvaluationService(suite_repo=suite_repo, run_repo=run_repo, settings=settings)
        safety_service = SafetyService(safety_repo=safety_repo, settings=settings)

        seeded_suite_ids: list[str] = []
        for suite_dict in suites_raw:
            suite_obj = TestSuite(**suite_dict)
            existing = await suite_repo.get_by_name(suite_obj.name)
            if existing:
                logger.info("Suite '%s' already exists (ID: %s). Skipping.", suite_obj.name, existing[0])
                seeded_suite_ids.append(existing[0])
            else:
                suite_id = await suite_repo.save(suite_obj)
                logger.info("Saved suite '%s' (ID: %s)", suite_obj.name, suite_id)
                seeded_suite_ids.append(suite_id)

        # Execute baseline demo runs for side-by-side comparison showcase
        if seeded_suite_ids:
            target_suite_id = seeded_suite_ids[0]
            logger.info("Executing baseline comparison runs for suite ID: %s...", target_suite_id)

            # Model 1 Run: mock-llama-3.3-70b
            run1 = await eval_service.execute_run(
                suite_id_or_object=target_suite_id,
                model="mock-llama-3.3-70b",
                params=GenerationParams(temperature=0.2, max_tokens=256),
            )
            logger.info("Executed baseline run 1: %s (Pass rate: %.1f%%)", run1.model, run1.pass_rate * 100)

            # Model 2 Run: mock-qwen-2.5-72b
            run2 = await eval_service.execute_run(
                suite_id_or_object=target_suite_id,
                model="mock-qwen-2.5-72b",
                params=GenerationParams(temperature=0.7, max_tokens=256),
            )
            logger.info("Executed baseline run 2: %s (Pass rate: %.1f%%)", run2.model, run2.pass_rate * 100)

            # Seed baseline safety report
            logger.info("Executing baseline adversarial injection audit...")
            safety_res = await safety_service.run_injection_test(
                model="mock-llama-3.3-70b",
                canary="CANARY_BENCHMARK_SECRET",
            )
            logger.info(
                "Completed safety audit (Tested: %d, Breached: %d, Report ID: %s)",
                safety_res["tested_count"],
                safety_res["breached_count"],
                safety_res["report_id"],
            )

    logger.info("PromptLab database seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
