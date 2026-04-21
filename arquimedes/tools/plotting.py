"""Plotting tool — renders a math function to a base64 PNG data URI.

The agent can call ``plot_function`` to produce an inline image. The React
frontend renders the returned Markdown image tag directly, so the student
sees the graph next to the derivation.
"""

from __future__ import annotations

import base64
import io

import matplotlib

matplotlib.use("Agg")  # headless backend — critical when running inside API
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import sympy as sp  # noqa: E402
from langchain_core.tools import tool  # noqa: E402
from sympy.parsing.sympy_parser import (  # noqa: E402
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application,)


@tool
def plot_function(
    expression: str,
    x_min: float = -10.0,
    x_max: float = 10.0,
    variable: str = "x",
    title: str | None = None,
    mark_zeros: bool = True,
) -> str:
    """Render a 1-D math function to a base64 PNG data URI.

    The returned string is a Markdown image tag — the frontend embeds it
    inline in the chat bubble.

    Args:
        expression: Expression in terms of ``variable`` (default ``x``),
            e.g. ``'x**3 - 3*x'`` or ``'sin(x)/x'``.
        x_min: Lower bound of the plotting range.
        x_max: Upper bound of the plotting range.
        variable: Independent variable. Defaults to ``x``.
        title: Optional plot title. Defaults to the expression.
        mark_zeros: If True, drops red dots at x where the function
            crosses zero (within the plotted range).
    """
    try:
        var = sp.Symbol(variable)
        expr = parse_expr(expression, transformations=_TRANSFORMATIONS, evaluate=True)
        f = sp.lambdify(var, expr, modules=["numpy"])
    except Exception as e:
        return f"error: failed to parse expression: {e}"

    xs = np.linspace(x_min, x_max, 500)
    with np.errstate(all="ignore"):
        ys = f(xs)
    ys = np.array(ys, dtype=float)

    fig, ax = plt.subplots(figsize=(6, 4), dpi=120)
    ax.plot(xs, ys, color="#6366f1", linewidth=2)
    ax.axhline(0, color="#94a3b8", linewidth=0.6)
    ax.axvline(0, color="#94a3b8", linewidth=0.6)
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.set_title(title or f"f({variable}) = {expression}")
    ax.set_xlabel(variable)
    ax.set_ylabel(f"f({variable})")

    if mark_zeros:
        try:
            roots = sp.solve(expr, var)
            numeric_roots = [float(sp.N(r)) for r in roots if r.is_real]
            in_range = [r for r in numeric_roots if x_min <= r <= x_max]
            for r in in_range:
                ax.plot(r, 0, "o", color="#ef4444", markersize=6)
        except Exception:
            pass

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    data = base64.b64encode(buf.getvalue()).decode("ascii")
    uri = f"data:image/png;base64,{data}"
    alt = f"Plot of {expression}"
    return f"![{alt}]({uri})"


plotting_tools = [plot_function]
