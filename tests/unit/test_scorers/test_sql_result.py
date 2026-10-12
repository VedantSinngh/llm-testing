"""Unit tests for SqlResult scorer and SQL security guardrails."""

from promptlab.core.models import TestCase
from promptlab.core.scorers.sql_result import SqlResult


def test_sql_result_valid_match() -> None:
    """Verify valid SELECT query returning identical result rows passes."""
    scorer = SqlResult()
    case = TestCase(
        id="sql-1",
        input="Find all products in Electronics category",
        scorer="sql_result",
        scorer_config={
            "expected_sql": "SELECT id, name FROM products WHERE category = 'Electronics' ORDER BY id;"
        },
    )
    candidate_sql = (
        "```sql\nSELECT id, name FROM products WHERE category = 'Electronics' ORDER BY id;\n```"
    )
    result = scorer.score(case, candidate_sql)

    assert result.score == 1.0
    assert result.passed is True
    assert "results match" in result.reason.lower()


def test_sql_result_mismatch_data() -> None:
    """Verify SELECT query returning wrong rows fails."""
    scorer = SqlResult()
    case = TestCase(
        id="sql-2",
        input="Find all products in Electronics category",
        scorer="sql_result",
        scorer_config={
            "expected_sql": "SELECT id, name FROM products WHERE category = 'Electronics';"
        },
    )
    candidate_sql = "SELECT id, name FROM products WHERE category = 'Kitchenware';"
    result = scorer.score(case, candidate_sql)

    assert result.score == 0.0
    assert result.passed is False
    assert "Results mismatch" in result.reason


def test_sql_security_block_drop_table() -> None:
    """Security Test: Verify DROP TABLE attempt is blocked."""
    scorer = SqlResult()
    case = TestCase(
        id="sec-drop",
        input="Inject DROP",
        scorer="sql_result",
        scorer_config={"expected_sql": "SELECT * FROM customers;"},
    )
    result = scorer.score(case, "DROP TABLE customers;")
    assert result.score == 0.0
    assert result.passed is False
    assert "Security Violation" in result.reason
    assert result.metadata["security_violation"] is True


def test_sql_security_block_delete_statement() -> None:
    """Security Test: Verify DELETE statement is blocked."""
    scorer = SqlResult()
    case = TestCase(
        id="sec-del",
        input="Inject DELETE",
        scorer="sql_result",
        scorer_config={"expected_sql": "SELECT * FROM customers;"},
    )
    result = scorer.score(case, "DELETE FROM customers WHERE id = 1;")
    assert result.score == 0.0
    assert result.passed is False
    assert "Security Violation" in result.reason


def test_sql_security_block_insert_statement() -> None:
    """Security Test: Verify INSERT statement is blocked."""
    scorer = SqlResult()
    case = TestCase(
        id="sec-ins",
        input="Inject INSERT",
        scorer="sql_result",
        scorer_config={"expected_sql": "SELECT * FROM customers;"},
    )
    result = scorer.score(
        case,
        "INSERT INTO customers (id, name, email, country) VALUES (99, 'Hacker', 'h@h.com', 'X');",
    )
    assert result.score == 0.0
    assert result.passed is False
    assert "Security Violation" in result.reason


def test_sql_security_block_stacked_queries() -> None:
    """Security Test: Verify multiple stacked statements separated by semicolon are blocked."""
    scorer = SqlResult()
    case = TestCase(
        id="sec-stack",
        input="Inject Stacked",
        scorer="sql_result",
        scorer_config={"expected_sql": "SELECT * FROM customers;"},
    )
    result = scorer.score(case, "SELECT * FROM customers; DROP TABLE orders;")
    assert result.score == 0.0
    assert result.passed is False
    assert "Security Violation" in result.reason


def test_sql_security_block_pragma() -> None:
    """Security Test: Verify PRAGMA metadata inspection is blocked."""
    scorer = SqlResult()
    case = TestCase(
        id="sec-pragma",
        input="Inspect PRAGMA",
        scorer="sql_result",
        scorer_config={"expected_sql": "SELECT * FROM customers;"},
    )
    result = scorer.score(case, "PRAGMA table_info(customers);")
    assert result.score == 0.0
    assert result.passed is False
    assert "Security Violation" in result.reason
