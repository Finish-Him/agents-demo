"""Symbolic math tool powered by SymPy.

Exposes a single tool ``solve_symbolic(expression, operation, variable)``
that can differentiate, integrate, solve equations, take limits, or
simplify an expression and return both the LaTeX form and a plain-text
rendering. The math tutor calls this whenever a numeric/symbolic check is
safer than trusting the LLM's own arithmetic.
"""

from __future__ import annotations

from typing import Literal

import sympy as sp
from langchain_core.tools import tool
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


def _parse(expression: str) -> sp.Expr:
    return parse_expr(expression, transformations=_TRANSFORMATIONS, evaluate=True)


@tool
def solve_symbolic(
    expression: str,
    operation: Literal[
        "derivative", "integral", "limit", "solve", "simplify", "evaluate"
    ] = "simplify",
    variable: str = "x",
    point: str | None = None,
) -> str:
    """Perform a symbolic math operation with SymPy.

    Use this to double-check any algebraic manipulation — derivatives,
    integrals, limits, equation solving, simplification, or numerical
    evaluation. Returns both the LaTeX form (for rendering) and a
    plain-text form.

    Args:
        expression: Math expression, e.g. ``'3*x**2 + 5*x - 7'`` or
            ``'sin(x)**2 + cos(x)**2'``. Implicit multiplication is
            allowed (``'3x'`` == ``'3*x'``).
        operation: ``'derivative'`` | ``'integral'`` | ``'limit'`` |
            ``'solve'`` (solve expr=0 for ``variable``) | ``'simplify'`` |
            ``'evaluate'`` (numerical value, 12 sig figs).
        variable: Variable of integration / differentiation / limit /
            solving. Defaults to ``x``.
        point: For ``limit`` the point to approach (e.g. ``'0'``,
            ``'oo'``). For ``evaluate`` the value of ``variable``.
    """
    try:
        expr = _parse(expression)
        var = sp.Symbol(variable)

        if operation == "derivative":
            result = sp.diff(expr, var)
        elif operation == "integral":
            result = sp.integrate(expr, var)
        elif operation == "limit":
            if point is None:
                return "error: limit requires a 'point' (e.g. '0', 'oo')."
            pt = _parse(point)
            result = sp.limit(expr, var, pt)
        elif operation == "solve":
            solutions = sp.solve(expr, var)
            result = solutions if solutions else []
        elif operation == "simplify":
            result = sp.simplify(expr)
        elif operation == "evaluate":
            if point is None:
                # Evaluate as a number when no free symbols.
                result = sp.N(expr, 12)
            else:
                result = sp.N(expr.subs(var, _parse(point)), 12)
        else:
            return f"error: unknown operation '{operation}'"
    except Exception as e:  # pragma: no cover
        return f"error: {type(e).__name__}: {e}"

    latex = sp.latex(result)
    return (
        f"{operation.upper()} — with respect to {variable}\n"
        f"Input: {expression}\n"
        f"Result (LaTeX): $${latex}$$\n"
        f"Result (plain): {result}"
    )


symbolic_tools = [solve_symbolic]
