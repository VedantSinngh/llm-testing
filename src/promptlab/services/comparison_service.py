"""Comparison Service for multi-model and multi-run evaluation analysis.

This module provides side-by-side comparative analytics across multiple evaluation runs:
- Metric summaries (pass rate, latency, token consumption).
- Per-case output and score alignment matrix.
- Comparative rankings for model selection.
"""

from typing import Any

from promptlab.core.models import RunResult
from promptlab.db.repositories import RunRepository
from promptlab.exceptions import ResourceNotFoundError, ValidationError


class ComparisonService:
    """Produces comparative matrices and metric deltas across evaluation runs."""

    def __init__(self, run_repo: RunRepository) -> None:
        """Initialize ComparisonService with run repository."""
        self._run_repo = run_repo

    async def compare_runs_by_ids(self, run_ids: list[str]) -> dict[str, Any]:
        """Fetch runs by IDs and generate a comprehensive comparison matrix."""
        if len(run_ids) < 2:
            raise ValidationError(
                "At least 2 run IDs are required for side-by-side comparison.",
                details={"provided_count": len(run_ids)},
            )

        runs: list[RunResult] = []
        for rid in run_ids:
            run = await self._run_repo.get_by_id(rid)
            if not run:
                raise ResourceNotFoundError("RunResult", rid)
            runs.append(run)

        return self.compare_runs(runs)

    def compare_runs(self, runs: list[RunResult]) -> dict[str, Any]:
        """Generate side-by-side comparison analytics for given RunResult instances."""
        summaries: list[dict[str, Any]] = [
            {
                "run_id": r.run_id,
                "suite_name": r.suite_name,
                "model": r.model,
                "technique": r.technique,
                "temperature": r.params.temperature,
                "pass_rate": r.pass_rate,
                "avg_latency_ms": r.avg_latency_ms,
                "total_tokens": r.total_tokens,
                "case_count": len(r.case_results),
            }
            for r in runs
        ]

        # Build case comparison matrix
        all_case_ids: list[str] = []
        for r in runs:
            for cr in r.case_results:
                if cr.case_id not in all_case_ids:
                    all_case_ids.append(cr.case_id)

        case_matrix: list[dict[str, Any]] = []
        for cid in all_case_ids:
            row: dict[str, Any] = {"case_id": cid, "runs": {}}
            for r in runs:
                cr = next((c for c in r.case_results if c.case_id == cid), None)
                if cr:
                    row["runs"][r.run_id] = {
                        "model": r.model,
                        "score": cr.score,
                        "passed": cr.passed,
                        "latency_ms": cr.response.latency_ms,
                        "output_preview": cr.response.text[:150],
                        "reason": cr.reason,
                    }
                else:
                    row["runs"][r.run_id] = None
            case_matrix.append(row)

        # Calculate leaderboards
        best_pass_rate = max(summaries, key=lambda s: float(s["pass_rate"]))
        fastest_latency = min(summaries, key=lambda s: float(s["avg_latency_ms"]))

        return {
            "run_count": len(runs),
            "summaries": summaries,
            "case_matrix": case_matrix,
            "best_performing_model": best_pass_rate["model"],
            "fastest_model": fastest_latency["model"],
        }
