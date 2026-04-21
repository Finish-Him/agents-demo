"""Tests for arquimedes/tools/symbolic.py."""

from arquimedes.tools import solve_symbolic


class TestSymbolic:
    def test_derivative_polynomial(self):
        r = solve_symbolic.invoke(
            {"expression": "3*x**2 + 5*x - 7", "operation": "derivative", "variable": "x"}
        )
        assert "6 x + 5" in r.replace("*", " ") or "6*x + 5" in r

    def test_derivative_implicit_mul(self):
        r = solve_symbolic.invoke(
            {"expression": "3x**2 + 5x - 7", "operation": "derivative"}
        )
        assert "6 x + 5" in r.replace("*", " ") or "6*x + 5" in r

    def test_integral(self):
        r = solve_symbolic.invoke(
            {"expression": "x**2", "operation": "integral"}
        )
        assert "x**3/3" in r or "x^{3}}{3}" in r

    def test_solve_quadratic(self):
        r = solve_symbolic.invoke(
            {"expression": "x**2 - 4", "operation": "solve"}
        )
        assert "-2" in r and "2" in r

    def test_limit(self):
        r = solve_symbolic.invoke(
            {"expression": "sin(x)/x", "operation": "limit", "point": "0"}
        )
        assert "1" in r.splitlines()[-1]

    def test_simplify(self):
        r = solve_symbolic.invoke(
            {"expression": "sin(x)**2 + cos(x)**2", "operation": "simplify"}
        )
        assert "1" in r.splitlines()[-1]

    def test_evaluate(self):
        r = solve_symbolic.invoke(
            {"expression": "pi", "operation": "evaluate"}
        )
        assert "3.14159" in r


class TestSymbolicErrors:
    def test_unknown_operation_rejected_by_schema(self):
        """LangChain enforces the Literal schema, so invalid ops never reach the body."""
        import pytest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            solve_symbolic.invoke(
                {"expression": "x**2", "operation": "nope"}  # type: ignore[arg-type]
            )
