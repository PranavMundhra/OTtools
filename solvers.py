"""Thin, honest wrappers around the OTTools package.

Each wrapper calls the real package function, normalises what it returns,
and builds the exact Python snippet a visitor can copy to reproduce the result.
Nothing here re-implements a solver: if a number is shown on the site, OTTools
computed it.
"""
from __future__ import annotations

import contextlib
import io
import threading
from dataclasses import dataclass, field

import numpy as np
import plotly.graph_objects as go

import OTTools

OPS = {"≤": "<=", "≥": ">=", "=": "="}
LP_METHODS = ["Graphical", "Simplex", "Big M", "Integer"]
TP_METHODS = {
    "North-West Corner": "NWCR",
    "Least Cost": "LCM",
    "Vogel's Approximation": "VAM",
    "MODI (optimal)": "MODI",
}

_lock = threading.Lock()


def quiet_call(fn, *args, **kwargs):
    """Run an OTTools function, capturing any figure it tries to .show() and its prints.

    graphical_method opens its Plotly figure with fig.show() and prints its
    corner points. On a web server that would open a browser tab on the server,
    so the figure is captured and returned to the page instead.
    """
    figures: list[go.Figure] = []
    with _lock:
        original_show = go.Figure.show
        go.Figure.show = lambda self, *a, **k: figures.append(self)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as printed:
                result = fn(*args, **kwargs)
        finally:
            go.Figure.show = original_show
    return result, figures, printed.getvalue()


# ---------------------------------------------------------------------------
# Formatting helpers for code snippets
# ---------------------------------------------------------------------------

def _n(x) -> str:
    x = float(x)
    return str(int(x)) if x.is_integer() else repr(round(x, 10))


def _vec(v) -> str:
    return "[" + ", ".join(_n(x) for x in v) + "]"


def _mat(A, indent: int = 0) -> str:
    rows = [_vec(r) for r in A]
    if len(rows) <= 1 or sum(len(r) for r in rows) < 60:
        return "[" + ", ".join(rows) + "]"
    pad = " " * (indent + 4)
    return "[\n" + "".join(f"{pad}{r},\n" for r in rows) + " " * indent + "]"


def _term(coef: float, var: str, first: bool) -> str:
    sign = "-" if coef < 0 else "+"
    mag = abs(coef)
    body = var if mag == 1 else f"{_n(mag)}{var}"
    if first:
        return ("−" if coef < 0 else "") + body
    return f" {'−' if sign == '-' else '+'} {body}"


def expression(coefs, names=None) -> str:
    names = names or [f"x{_sub(j + 1)}" for j in range(len(coefs))]
    parts = [(c, v) for c, v in zip(coefs, names) if c != 0]
    if not parts:
        return "0"
    return "".join(_term(c, v, i == 0) for i, (c, v) in enumerate(parts))


def _sub(k: int) -> str:
    return str(k).translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))


# ---------------------------------------------------------------------------
# Linear programming
# ---------------------------------------------------------------------------

@dataclass
class LPResult:
    method: str
    status: str                      # optimal | unbounded | infeasible | unsupported | error
    value: float | None = None
    x: list[float] | None = None
    fig: go.Figure | None = None
    code: str = ""
    notes: list[str] = field(default_factory=list)
    message: str = ""


def lp_availability(n_vars: int, ops: list[str]) -> dict[str, str | None]:
    """None means the method can run; otherwise the reason it cannot."""
    return {
        "Graphical": None if n_vars in (2, 3) else f"needs 2 or 3 variables (this problem has {n_vars})",
        "Simplex": None if all(o == "≤" for o in ops) else "handles ≤ constraints only — use Big M for ≥ or =",
        "Big M": None,
        "Integer": None,
    }


def _normalise(value, solution):
    if isinstance(value, str):
        text = value.lower()
        status = "unbounded" if "unbound" in text else "infeasible" if "infeasible" in text else "error"
        return status, None, None, value
    if solution is None or value is None or not np.isfinite(float(value)):
        return "infeasible", None, None, "No feasible solution."
    x = [0.0 if abs(v) < 1e-9 else float(v) for v in np.asarray(solution, dtype=float)]
    return "optimal", float(value), x, ""


def _result_comment(status, value, x, value_name="value", x_name="x") -> str:
    if status != "optimal":
        return f"# → {status}"
    return f"# → {value_name} = {_n(round(value, 6))}, {x_name} = {_vec([round(v, 6) for v in x])}"


def solve_lp(method: str, c, A, b, ops_sym, minimize: bool, t: dict | None = None) -> LPResult:
    ops = [OPS[o] for o in ops_sym]
    try:
        if method == "Graphical":
            return _graphical(c, A, b, ops_sym, ops, minimize, t)
        if method == "Simplex":
            reason = lp_availability(len(c), ops_sym)["Simplex"]
            if reason:
                return LPResult(method, "unsupported", message=f"Simplex {reason}.")
            (value, sol), _, _ = quiet_call(OTTools.simplex_method, c, A, b, Min=minimize)
            call = (f"value, x = simplex_method(\n    c={_vec(c)},\n    A={_mat(A, 4)},\n"
                    f"    b={_vec(b)},\n    Min={minimize},\n)")
            fn = "simplex_method"
        elif method == "Big M":
            (value, sol), _, _ = quiet_call(OTTools.big_m_method, c, A, b, ops, Min=minimize)
            call = (f"value, x = big_m_method(\n    c={_vec(c)},\n    A={_mat(A, 4)},\n    b={_vec(b)},\n"
                    f"    constraint_types={ops!r},\n    Min={minimize},\n)")
            fn = "big_m_method"
        elif method == "Integer":
            (value, sol), _, _ = quiet_call(OTTools.integer_simplex, c, A, b, Min=minimize, constraint_types=ops)
            call = (f"value, x = integer_simplex(\n    c={_vec(c)},\n    A={_mat(A, 4)},\n    b={_vec(b)},\n"
                    f"    Min={minimize},\n    constraint_types={ops!r},\n)")
            fn = "integer_simplex"
        else:
            raise ValueError(f"Unknown method {method}")
    except Exception as exc:  # the package raises on malformed input
        return LPResult(method, "error", message=str(exc))

    status, value, x, message = _normalise(value, sol)
    code = f"from OTTools import {fn}\n\n{call}\n{_result_comment(status, value, x)}"
    notes = []
    if method == "Integer" and status == "optimal":
        notes.append("Branch and bound: every variable is forced to a whole number.")
    return LPResult(method, status, value, x, None, code, notes, message)


def _graphical(c, A, b, ops_sym, ops, minimize, t) -> LPResult:
    """graphical_method maximises c·x subject to A·x ≤ b, so convert first."""
    notes = []
    cg = [-v for v in c] if minimize else list(c)
    Ag, bg, labels = [], [], []
    for i, (row, op, rhs) in enumerate(zip(A, ops, b)):
        label = f"{expression(row)} {ops_sym[i]} {_n(rhs)}"
        if op == "<=":
            Ag.append(list(row)); bg.append(rhs); labels.append((label, True, i))
        elif op == ">=":
            Ag.append([-a for a in row]); bg.append(-rhs); labels.append((label, True, i))
        else:
            Ag += [list(row), [-a for a in row]]; bg += [rhs, -rhs]
            labels += [(label, True, i), (label, False, i)]
    if minimize:
        notes.append("Minimise Z is solved as maximise −Z (graphical_method only maximises).")
    if ">=" in ops:
        notes.append("Each ≥ row was multiplied by −1 to become a ≤ row.")
    if "=" in ops:
        notes.append("Each = row was split into a ≤ row and a ≥ row.")

    code = (
        "from OTTools import graphical_method\n\n"
        "# graphical_method maximises c·x subject to A·x ≤ b, x ≥ 0\n"
        + "".join(f"# {n_}\n" for n_ in notes)
        + f"point, value = graphical_method(\n    c={_vec(cg)},\n    A={_mat(Ag, 4)},\n    b={_vec(bg)},\n)\n"
    )
    try:
        (point, value), figures, _ = quiet_call(OTTools.graphical_method, cg, Ag, bg)
    except ValueError as exc:
        status = "infeasible" if "infeasible" in str(exc).lower() else "error"
        return LPResult("Graphical", status, code=code + f"# → {status}", notes=notes, message=str(exc))

    value = float(value)
    true_value = -value if minimize else value
    x = [0.0 if abs(v) < 1e-9 else float(v) for v in np.asarray(point, dtype=float)]
    code += f"# → point = {_vec([round(v, 6) for v in x])}, value = {_n(round(value, 6))}"
    if minimize:
        code += f"  (so min Z = {_n(round(true_value, 6))})"

    # The graphical method only looks at corner points, so it cannot see an
    # unbounded direction. Cross-check with Big M on the original problem.
    (chk_value, _), _, _ = quiet_call(OTTools.big_m_method, c, A, b, ops, Min=minimize)
    if isinstance(chk_value, str) and "unbound" in chk_value.lower():
        return LPResult("Graphical", "unbounded", code=code, notes=notes,
                        message="The feasible region is open in the direction of improvement, so Z "
                                "has no best value. (Checked with big_m_method; corner points alone "
                                "cannot show this.)",
                        fig=_restyle_graphical(figures[0], labels, None, t, Ag) if figures and t else None)

    fig = None
    if figures and t:
        fig = _restyle_graphical(figures[0], labels, true_value, t, Ag)
    return LPResult("Graphical", "optimal", true_value, x, fig, code, notes)


def _restyle_graphical(fig: go.Figure, labels, z_value, t: dict, rows=None) -> go.Figure:
    """Recolour the package's own figure in the site palette and restore readable labels.

    The package names its constraint lines from the converted (≤) rows, e.g.
    "−4x₁ + −3x₂ ≤ −6"; they are renamed back to what the visitor typed.
    """
    fig.update_layout(title=None)
    if any(tr.type != "scatter" for tr in fig.data):
        return fig  # 3-variable figure: keep the package's 3D styling, only the layout is themed
    traced = labels if rows is None else [lab for lab, r in zip(labels, rows) if r[0] or r[1]]
    k = 0
    for trace in fig.data:
        name = trace.name or ""
        if "≤" in name:
            if k < len(traced):
                text, show, row = traced[k]
                trace.name = text
                trace.showlegend = show
                trace.line = dict(color=t["lines"][row % len(t["lines"])], width=2)
            k += 1
        elif name == "Feasible Region":
            trace.fillcolor = t["fill"]
            trace.name = "Feasible region"
        elif name == "Corner Points":
            trace.marker = dict(size=8, color=t["text"])
            trace.name = "Corner points"
        elif name.startswith("Optimal"):
            trace.marker = dict(size=18, color=t["mint"], symbol="star", line=dict(width=1, color=t["bg"]))
        elif name.startswith("Z ="):
            trace.line = dict(color=t["amber"], dash="dash", width=2)
            if z_value is not None:
                trace.name = f"Z = {_n(round(z_value, 4))}"
    return fig


# ---------------------------------------------------------------------------
# Transportation
# ---------------------------------------------------------------------------

@dataclass
class TPResult:
    method: str
    status: str
    allocation: np.ndarray | None = None
    cost: np.ndarray | None = None
    supply: np.ndarray | None = None
    demand: np.ndarray | None = None
    total: float | None = None
    dummy: str | None = None          # "row" | "col" | None
    code: str = ""
    message: str = ""


def solve_tp(cost, supply, demand, method_label: str) -> TPResult:
    key = TP_METHODS[method_label]
    code = (
        "from OTTools import TransportationProblem\n\n"
        f"tp = TransportationProblem(\n    cost_matrix={_mat(cost, 4)},\n"
        f"    supply={_vec(supply)},\n    demand={_vec(demand)},\n)  # auto_balance=True adds a dummy row/column if needed\n"
        f'allocation = tp.solve("{key}")\n'
        "total = (allocation * tp.cost_matrix).sum()\n"
    )
    try:
        tp = OTTools.TransportationProblem(cost, supply, demand)
        allocation, _, _ = quiet_call(tp.solve, key)
    except Exception as exc:
        return TPResult(method_label, "error", code=code, message=str(exc))
    allocation = np.asarray(allocation, dtype=float)
    cost_b = np.asarray(tp.cost_matrix, dtype=float)
    total = float((allocation * cost_b).sum())
    m, n = len(supply), len(demand)
    dummy = "row" if cost_b.shape[0] > m else "col" if cost_b.shape[1] > n else None
    code += f"# → total = {_n(round(total, 6))}"
    return TPResult(method_label, "optimal", allocation, cost_b, np.asarray(tp.supply, float),
                    np.asarray(tp.demand, float), total, dummy, code)
