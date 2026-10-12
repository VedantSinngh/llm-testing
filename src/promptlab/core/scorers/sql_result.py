"""Text-to-SQL evaluation scorer with strict query safety enforcement.

This module evaluates model-generated SQL statements by executing them against a
sandboxed SQLite database and comparing the returned result set with ground truth.
Crucially, it enforces a strict zero-trust security policy: ANY query containing
non-SELECT statements or destructive keywords is blocked, raising SecurityError.
"""

from pathlib import Path
import re
import sqlite3

from promptlab.core.models import ScoreResult, TestCase
from promptlab.core.scorers.base import BaseScorer
from promptlab.exceptions import SecurityError

# Disallowed keywords that modify state, inspect metadata, or break sandbox boundaries
FORBIDDEN_SQL_KEYWORDS: set[str] = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "REPLACE",
    "TRUNCATE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
    "VACUUM",
    "REINDEX",
    "TRANSACTION",
    "COMMIT",
    "ROLLBACK",
}


# Design Pattern: Template Method concrete subclass with strict security validation.
class SqlResult(BaseScorer):
    """Scorer executing SQL against a sandboxed SQLite DB and comparing result sets."""

    name: str = "sql_result"

    def __init__(self, sample_db_sql_path: str | None = None) -> None:
        """Initialize SqlResult with schema path for seeding sandboxed databases."""
        self._sample_db_sql_path = sample_db_sql_path or str(
            Path(__file__).resolve().parents[3] / "data" / "sample.db.sql"
        )

    def _extract_sql(self, text: str) -> str:
        """Extract clean SQL query, stripping markdown code fences."""
        match = re.search(r"```(?:sql)?\s*([\s\S]*?)\s*```", text, re.IGNORECASE)
        sql = match.group(1).strip() if match else text.strip()
        return sql.rstrip(";")

    def _validate_sql_safety(self, sql: str) -> None:
        """Enforce strict read-only policy. Only SELECT or WITH queries are permitted.

        Raises:
            SecurityError: If query contains state-modifying or forbidden keywords.
        """
        # Block multi-statement execution attempts
        statements = [s.strip() for s in sql.split(";") if s.strip()]
        if len(statements) > 1:
            raise SecurityError(
                "Stacked SQL queries are prohibited.",
                details={"statements_count": len(statements)},
            )

        clean_sql = statements[0] if statements else sql
        tokens = re.findall(r"\b[A-Za-z_]+\b", clean_sql.upper())
        if not tokens:
            raise SecurityError("Empty or invalid SQL statement.")

        first_token = tokens[0]
        if first_token not in {"SELECT", "WITH"}:
            raise SecurityError(
                f"Unauthorized SQL command '{first_token}'. Only SELECT queries are permitted.",
                details={"command": first_token},
            )

        for token in tokens:
            if token in FORBIDDEN_SQL_KEYWORDS:
                raise SecurityError(
                    f"Forbidden SQL keyword '{token}' detected.",
                    details={"forbidden_token": token},
                )

    def _init_in_memory_db(self) -> sqlite3.Connection:
        """Initialize an in-memory SQLite database seeded from the sample schema."""
        conn = sqlite3.connect(":memory:")
        schema_path = Path(self._sample_db_sql_path)
        if schema_path.exists():
            schema_sql = schema_path.read_text(encoding="utf-8")
            conn.executescript(schema_sql)
        return conn

    def _evaluate(self, case: TestCase, output: str) -> ScoreResult:
        """Execute candidate SQL, compare result sets, and evaluate match."""
        try:
            candidate_sql = self._extract_sql(output)
            self._validate_sql_safety(candidate_sql)
        except SecurityError as sec_err:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason=f"Security Violation: {sec_err.message}",
                metadata={"security_violation": True, "error": sec_err.message},
            )

        expected_sql = self._extract_sql(
            case.scorer_config.get("expected_sql") or case.expected or ""
        )
        if not expected_sql:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason="Configuration error: 'expected_sql' or expected query must be provided.",
            )

        conn = self._init_in_memory_db()
        try:
            cursor = conn.cursor()
            candidate_rows = cursor.execute(candidate_sql).fetchall()
            expected_rows = cursor.execute(expected_sql).fetchall()

            matched = candidate_rows == expected_rows
            return ScoreResult(
                score=1.0 if matched else 0.0,
                passed=matched,
                reason=(
                    "Query results match expected rows."
                    if matched
                    else f"Results mismatch: got {len(candidate_rows)} rows, expected {len(expected_rows)}."
                ),
                metadata={
                    "candidate_rows_count": len(candidate_rows),
                    "expected_rows_count": len(expected_rows),
                },
            )
        except sqlite3.Error as sql_err:
            return ScoreResult(
                score=0.0,
                passed=False,
                reason=f"SQLite execution error: {sql_err}",
                metadata={"error": str(sql_err)},
            )
        finally:
            conn.close()
