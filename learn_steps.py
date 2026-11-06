"""Step-by-step teaching versions of each algorithm, for the Learn page.

OTTools 0.1.3 returns only final answers, so these small implementations record
every intermediate tableau / allocation for display. They follow the package's
own rules (tie-breaking, Vogel penalties, depth-first branch and bound), and
every lesson checks its final answer against the real package.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction as F
from itertools import combinations
from typing import Callable

import numpy as np
import plotly.graph_objects as go
from scipy.optimize import linprog

import solvers
from examples import LP_EXAMPLES, TP_EXAMPLES
from ui import table

SUB = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")


def sub(k: int) -> str:
    return str(k).translate(SUB)


def fx(x) -> str:
    """Format a Fraction / number for display: 3/5, −2, 12."""
    if isinstance(x, F):
        s = str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"
    else:
        x = float(x)
        s = str(int(round(x))) if abs(x - round(x)) < 1e-9 else f"{x:.4f}".rstrip("0").rstrip(".")
    return s.replace("-", "−")


@dataclass
class Step:
    title: str
    why: str
    html: str = ""
    fig: go.Figure | None = None
    dot: str = ""


@dataclass
class Lesson:
    key: str
    group: str
    summary: str
    use_when: str
    avoid_when: str
    idea: str
    mistakes: list[str]
    example: str                       # name in LP_EXAMPLES / TP_EXAMPLES
    solver_method: str                 # method label on the solver page
    build: Callable[[dict], tuple[list[Step], dict]]
    latex: list[str] = field(default_factory=list)

    @property
    def kind(self) -> str:
        return "lp" if self.group == "Linear programming" else "tp"


# ===========================================================================
# Simplex / Big M tableau engine (exact fractions, M kept symbolic)
# ===========================================================================

@dataclass(frozen=True)
class MV:
    """a + b·M with M a 'very large' number."""
    a: F = F(0)
    b: F = F(0)

    def __add__(self, o: "MV") -> "MV":
        return MV(self.a + o.a, self.b + o.b)

    def __sub__(self, o: "MV") -> "MV":
        return MV(self.a - o.a, self.b - o.b)

    def scale(self, k: F) -> "MV":
        return MV(self.a * k, self.b * k)

    def key(self):
        return (self.b, self.a)

    def negative(self) -> bool:
        return self.key() < (0, 0)

    def __str__(self) -> str:
        if self.b == 0:
            return fx(self.a)
        mag = abs(self.b)
        m_term = ("" if mag == 1 else fx(mag) if mag.denominator == 1 else f"({fx(mag)})") + "M"
        if self.a == 0:
            return ("−" if self.b < 0 else "") + m_term
        return f"{fx(self.a)} {'+' if self.b > 0 else '−'} {m_term}"


def _tableau_html(names, T, rhs, basis, z, zr, enter=None, leave=None, ratios=None, art=()):
    header = ["Basis"] + names + ["RHS"] + (["Ratio"] if ratios is not None else [])
    hcls = ["rowh"] + ["enter" if j == enter else ("dim" if j in art else "") for j in range(len(names))] + ["", ""]
    rows = []
    for i in range(len(T)):
        row = [(names[basis[i]], "leave" if i == leave else "")]
        for j, v in enumerate(T[i]):
            cls = "pivot" if (i == leave and j == enter) else "enter" if j == enter else "leave" if i == leave else ""
            row.append((fx(v), cls))
        row.append((fx(rhs[i]), "leave" if i == leave else ""))
        if ratios is not None:
            r = ratios[i]
            row.append((fx(r) if r is not None else "–", "leave" if i == leave else "dim" if r is None else ""))
        rows.append(row)
    zrow = [("Z", "")]
    for j, v in enumerate(z):
        cls = []
        if j == enter:
            cls.append("enter")
        if v.negative() and j not in basis:
            cls.append("neg")
        zrow.append((str(v), " ".join(cls)))
    zrow.append((str(zr), ""))
    if ratios is not None:
        zrow.append(("", ""))
    rows.append(zrow)
    return table(header, rows, hcls)


def run_tableau(c, rows, minimize=False):
    """rows: [(coeffs, op, rhs)] with op in ≤ ≥ =. Returns (steps, final)."""
    m, n = len(rows), len(c)
    cmax = [F(-v) if minimize else F(v) for v in c]
    names = [f"x{sub(j + 1)}" for j in range(n)]
    T = [[F(a) for a in r[0]] for r in rows]
    rhs = [F(r[2]) for r in rows]
    z = [MV(-cj) for cj in cmax]
    basis = [0] * m
    art: set[int] = set()
    added = []
    s_i = a_i = 0

    def add(row_i, name, coef, zval):
        names.append(name)
        for k in range(m):
            T[k].append(F(coef) if k == row_i else F(0))
        z.append(zval)
        return len(names) - 1

    for i, (_, op, _) in enumerate(rows):
        if op == "≤":
            s_i += 1
            basis[i] = add(i, f"s{sub(s_i)}", 1, MV())
            added.append(f"row {i + 1} (≤): slack **s{sub(s_i)}**")
        elif op == "≥":
            s_i += 1
            add(i, f"s{sub(s_i)}", -1, MV())
            a_i += 1
            basis[i] = add(i, f"A{sub(a_i)}", 1, MV(F(0), F(1)))
            art.add(basis[i])
            added.append(f"row {i + 1} (≥): surplus **s{sub(s_i)}** (−1) and artificial **A{sub(a_i)}**")
        else:
            a_i += 1
            basis[i] = add(i, f"A{sub(a_i)}", 1, MV(F(0), F(1)))
            art.add(basis[i])
            added.append(f"row {i + 1} (=): artificial **A{sub(a_i)}**")
    zr = MV()
    steps: list[Step] = []

    intro = ""
    if minimize:
        intro = "We minimise Z by **maximising −Z**, so every objective coefficient changes sign. "
    intro += "Add one extra variable per constraint: " + "; ".join(added) + ". "
    if art:
        intro += ("Artificial variables give an easy starting basis but must end at 0, so the objective "
                  "charges a huge penalty **M** for each one: the Z row gets **+M** under every artificial column.")
    else:
        intro += "The slacks form the starting basis (all decision variables = 0), and the Z row holds −c."
    steps.append(Step("Set up the tableau", intro, _tableau_html(names, T, rhs, basis, z, zr, art=art)))

    if art:
        for i in range(m):
            if basis[i] in art:
                z = [z[j] - MV(F(0), T[i][j]) for j in range(len(z))]
                zr = zr - MV(F(0), rhs[i])
        steps.append(Step(
            "Clear M from the basic columns",
            "A basic variable must have 0 in the Z row. Subtract **M × (each artificial's row)** from the Z row. "
            "Now the Z row mixes numbers and M; compare the M parts first, since M dominates.",
            _tableau_html(names, T, rhs, basis, z, zr, art=art)))

    for it in range(1, 30):
        cand = [j for j in range(len(z)) if j not in basis and z[j].negative()]
        if not cand:
            infeasible = any(basis[i] in art and rhs[i] > 0 for i in range(m))
            x = [F(0)] * n
            for i in range(m):
                if basis[i] < n:
                    x[basis[i]] = rhs[i]
            zmax = zr.a
            value = -zmax if minimize else zmax
            if infeasible:
                steps.append(Step("Infeasible", "No negative entries remain, yet an artificial variable is still "
                                  "positive. The constraints cannot all hold at once.",
                                  _tableau_html(names, T, rhs, basis, z, zr, art=art)))
                return steps, {"status": "infeasible"}
            sol = ", ".join(f"x{sub(j + 1)} = {fx(v)}" for j, v in enumerate(x))
            text = (f"No negative entries are left in the Z row, so this tableau is **optimal**. Read the answer "
                    f"off the RHS column: {sol} (variables not in the basis are 0). ")
            text += (f"Max(−Z) = {fx(zmax)}, so **min Z = {fx(value)}**." if minimize else f"**Z = {fx(value)}**.")
            steps.append(Step("Optimal", text, _tableau_html(names, T, rhs, basis, z, zr, art=art)))
            return steps, {"status": "optimal", "value": value, "x": x}

        e = min(cand, key=lambda j: (z[j].key(), j))
        ratios = [rhs[i] / T[i][e] if T[i][e] > 0 else None for i in range(m)]
        if all(r is None for r in ratios):
            steps.append(Step(f"Iteration {it}: unbounded",
                              f"**{names[e]}** would improve Z, but no entry in its column is positive, so it can "
                              "grow forever. The problem is **unbounded**.",
                              _tableau_html(names, T, rhs, basis, z, zr, enter=e, ratios=ratios, art=art)))
            return steps, {"status": "unbounded"}
        l = min((i for i in range(m) if ratios[i] is not None), key=lambda i: (ratios[i], i))
        reason = "has the most negative M part" if z[e].b != 0 else "is the most negative"
        tests = ", ".join(f"{names[basis[i]]}: {fx(rhs[i])} ÷ {fx(T[i][e])} = {fx(ratios[i])}"
                          for i in range(m) if ratios[i] is not None)
        text = (f"**{names[e]} enters**: its Z-row entry {z[e]} {reason}, so increasing it raises the objective fastest. "
                f"Ratio test (RHS ÷ positive entries of the {names[e]} column): {tests}. The smallest ratio is in row "
                f"{names[basis[l]]}, so **{names[basis[l]]} leaves**. The pivot is **{fx(T[l][e])}**.")
        if it > 1:
            text = "This is the tableau after the previous pivot. " + text
        steps.append(Step(f"Iteration {it}: choose the pivot", text,
                          _tableau_html(names, T, rhs, basis, z, zr, enter=e, leave=l, ratios=ratios, art=art)))
        # pivot
        p = T[l][e]
        T[l] = [v / p for v in T[l]]
        rhs[l] /= p
        for i in range(m):
            if i != l and T[i][e] != 0:
                f_ = T[i][e]
                T[i] = [T[i][j] - f_ * T[l][j] for j in range(len(T[i]))]
                rhs[i] -= f_ * rhs[l]
        zf = z[e]
        z = [z[j] - zf.scale(T[l][j]) for j in range(len(z))]
        zr = zr - zf.scale(rhs[l])
        basis[l] = e
    raise RuntimeError("too many iterations")


def _lp_rows(example):
    ex = LP_EXAMPLES[example]
    return ex["c"], [(r[:-2], r[-2], r[-1]) for r in ex["rows"]], ex["sense"] == "Minimize"


def build_simplex(t):
    c, rows, minimize = _lp_rows("Glass factory · max, 2 variables")
    return run_tableau(c, rows, minimize)


def build_bigm(t):
    c, rows, minimize = _lp_rows("Mixed constraints · min, ≥ and =")
    return run_tableau(c, rows, minimize)


# ===========================================================================
# Graphical method
# ===========================================================================

def _vertices(A, b):
    A = np.asarray(A, float)
    b = np.asarray(b, float)
    pts = []
    for i, j in combinations(range(len(A)), 2):
        M = A[[i, j]]
        if abs(np.linalg.det(M)) < 1e-12:
            continue
        p = np.linalg.solve(M, b[[i, j]])
        if np.all(A @ p <= b + 1e-9) and not any(np.allclose(p, q) for q in pts):
            pts.append(p)
    if not pts:
        return np.zeros((0, 2))
    P = np.array(pts)
    ctr = P.mean(axis=0)
    return P[np.argsort(np.arctan2(P[:, 1] - ctr[1], P[:, 0] - ctr[0]))]


def build_graphical(t):
    ex = LP_EXAMPLES["Glass factory · max, 2 variables"]
    c = np.array(ex["c"], float)
    A = np.array([r[:2] for r in ex["rows"]], float)
    b = np.array([r[3] for r in ex["rows"]], float)
    xs = [bi / a[0] for a, bi in zip(A, b) if a[0] > 0]
    ys = [bi / a[1] for a, bi in zip(A, b) if a[1] > 0]
    X, Y = max(xs) * 1.3, max(ys) * 1.25
    base_A = [[-1, 0], [0, -1], [1, 0], [0, 1]]
    base_b = [0, 0, X, Y]
    xx = np.linspace(0, X, 200)

    def line_trace(a, bi, color, width, name, dash=None):
        if abs(a[1]) > 1e-12:
            return go.Scatter(x=xx, y=(bi - a[0] * xx) / a[1], mode="lines", name=name,
                              line=dict(color=color, width=width, dash=dash))
        return go.Scatter(x=[bi / a[0]] * 2, y=[0, Y], mode="lines", name=name,
                          line=dict(color=color, width=width, dash=dash))

    def frame(k, extra=()):
        fig = go.Figure()
        poly = _vertices(np.vstack([A[:k], base_A]) if k else np.array(base_A), np.concatenate([b[:k], base_b]))
        if len(poly):
            closed = np.vstack([poly, poly[:1]])
            fig.add_trace(go.Scatter(x=closed[:, 0], y=closed[:, 1], fill="toself", fillcolor=t["fill"],
                                     line=dict(width=0), name="Feasible so far" if k < len(A) else "Feasible region",
                                     hoverinfo="skip"))
        for i in range(k):
            label = f"{solvers.expression(A[i])} ≤ {fx(b[i])}"
            new = i == k - 1 and not extra
            fig.add_trace(line_trace(A[i], b[i], t["teal"] if new else t["muted"], 3 if new else 1.5, label))
        for tr in extra:
            fig.add_trace(tr)
        fig.update_xaxes(range=[0, X], title="x₁")
        fig.update_yaxes(range=[0, Y], title="x₂")
        return fig

    steps = [Step("Start with x₁ ≥ 0, x₂ ≥ 0",
                  f"Every point in the first quadrant is allowed so far. Goal: **maximise Z = {solvers.expression(c)}**.",
                  fig=frame(0))]
    for i in range(len(A)):
        a, bi = A[i], b[i]
        pts = []
        if a[0] > 0:
            pts.append(f"({fx(bi / a[0])}, 0)")
        if a[1] > 0:
            pts.append(f"(0, {fx(bi / a[1])})")
        shape = "a vertical line" if a[1] == 0 else "a horizontal line" if a[0] == 0 else "the line through " + " and ".join(pts)
        steps.append(Step(
            f"Add constraint {i + 1}: {solvers.expression(a)} ≤ {fx(bi)}",
            f"Treat it as an equation and draw {shape}. Test the origin: 0 ≤ {fx(bi)} is true, so keep the side "
            "that contains (0, 0). The shaded area is what still satisfies every constraint so far.",
            fig=frame(i + 1)))

    corners = _vertices(np.vstack([A, base_A[:2]]), np.concatenate([b, [0, 0]]))
    zs = corners @ c
    best = int(np.argmax(zs))
    rows = [[f"({fx(p[0])}, {fx(p[1])})", (fx(z_), "hit" if k == best else "")] for k, (p, z_) in enumerate(zip(corners, zs))]
    corner_tr = go.Scatter(x=corners[:, 0], y=corners[:, 1], mode="markers+text", name="Corner points",
                           text=[f"({fx(p[0])}, {fx(p[1])})" for p in corners], textposition="top right",
                           marker=dict(size=9, color=t["text"]))
    steps.append(Step(
        "List the corner points",
        "If an LP has an optimum, one is at a corner of the feasible region. So evaluate Z at every corner.",
        html=table(["Corner (x₁, x₂)", f"Z = {solvers.expression(c)}"], rows), fig=frame(len(A), [corner_tr])))

    p = corners[best]
    zline = line_trace(c, zs[best], t["amber"], 2.5, f"Z = {fx(zs[best])}", dash="dash")
    star = go.Scatter(x=[p[0]], y=[p[1]], mode="markers", name="Optimum",
                      marker=dict(size=20, symbol="star", color=t["mint"], line=dict(width=1, color=t["bg"])))
    steps.append(Step(
        "Pick the best corner",
        f"Z is largest at **({fx(p[0])}, {fx(p[1])})** with **Z = {fx(zs[best])}**. Picture sliding the objective line "
        f"{solvers.expression(c)} = Z away from the origin: this corner is the last feasible point it touches.",
        fig=frame(len(A), [corner_tr, zline, star])))
    return steps, {"status": "optimal", "value": float(zs[best]), "x": [float(v) for v in p]}


# ===========================================================================
# Branch and bound
# ===========================================================================

def build_bnb(t):
    ex = LP_EXAMPLES["Whole units only · max, integer"]
    c = np.array(ex["c"], float)
    A = np.array([r[:2] for r in ex["rows"]], float)
    b = np.array([r[3] for r in ex["rows"]], float)
    n = len(c)

    stack = [("N0", [], None, None)]          # (id, extra bounds [(j, '<=|>=', v)], parent, edge label)
    nodes, edges, steps = [], [], []
    best_val, best_x = -np.inf, None
    counter = 1
    while stack:
        nid, extra, parent, elabel = stack.pop()
        A_ub, b_ub = [list(r) for r in A], list(b)
        for j, op, v in extra:
            row = [0.0] * n
            row[j] = 1.0 if op == "<=" else -1.0
            A_ub.append(row)
            b_ub.append(v if op == "<=" else -v)
        res = linprog(-c, A_ub=A_ub, b_ub=b_ub, bounds=[(0, None)] * n, method="highs")
        added = " and ".join(f"x{sub(j + 1)} {'≤' if op == '<=' else '≥'} {fx(v)}" for j, op, v in extra) or "no extra bounds"
        if parent:
            edges.append((parent, nid, elabel))
        if res.status != 0:
            nodes.append((nid, "infeasible", "infeasible"))
            text = f"Node {nid} ({added}): the LP has **no feasible point**, so this branch is dropped."
        else:
            x = res.x
            val = -res.fun
            desc = ", ".join(f"x{sub(j + 1)}={fx(v)}" for j, v in enumerate(x)) + f"\\nZ={fx(val)}"
            frac = [j for j, v in enumerate(x) if abs(v - round(v)) > 1e-7]
            if val <= best_val + 1e-9:
                nodes.append((nid, desc, "pruned"))
                text = (f"Node {nid} ({added}): LP optimum Z = {fx(val)}. That is no better than the best whole-number "
                        f"answer so far ({fx(best_val)}), so **prune**: nothing below this node can win.")
            elif not frac:
                best_val, best_x = val, x
                nodes.append((nid, desc, "integer"))
                text = (f"Node {nid} ({added}): LP optimum is already whole numbers, Z = {fx(val)}. "
                        f"This is the **new best integer solution** (the incumbent).")
            else:
                j = frac[0]
                fl = float(np.floor(x[j]))
                nodes.append((nid, desc, "branch"))
                left, right = f"N{counter}", f"N{counter + 1}"
                counter += 2
                stack.append((right, extra + [(j, ">=", fl + 1)], nid, f"x{sub(j + 1)} ≥ {fx(fl + 1)}"))
                stack.append((left, extra + [(j, "<=", fl)], nid, f"x{sub(j + 1)} ≤ {fx(fl)}"))
                text = (f"Node {nid} ({added}): LP optimum Z = {fx(val)} with x{sub(j + 1)} = {fx(x[j])}, not a whole number. "
                        f"**Branch**: no integer solution has {fx(fl)} < x{sub(j + 1)} < {fx(fl + 1)}, so split into "
                        f"x{sub(j + 1)} ≤ {fx(fl)} (explored first) and x{sub(j + 1)} ≥ {fx(fl + 1)}.")
        steps.append(Step(f"Node {nid}", text, dot=_bnb_dot(nodes, edges, nid, t)))
    sol = ", ".join(f"x{sub(j + 1)} = {fx(v)}" for j, v in enumerate(best_x))
    steps.append(Step("Done", f"Every branch is explored or pruned. The best integer solution is **{sol}, Z = {fx(best_val)}**. "
                      "The very first LP promised more, but no whole-number point reaches it.",
                      dot=_bnb_dot(nodes, edges, None, t)))
    return steps, {"status": "optimal", "value": float(best_val), "x": [float(v) for v in best_x]}


def _bnb_dot(nodes, edges, current, t):
    style = {
        "branch": f'fillcolor="{t["panel"]}"',
        "integer": f'fillcolor="{t["mint"]}33" color="{t["mint"]}"',
        "pruned": f'fillcolor="{t["panel"]}" fontcolor="{t["muted"]}" style="rounded,filled,dashed"',
        "infeasible": f'fillcolor="{t["panel"]}" fontcolor="{t["error"]}" style="rounded,filled,dashed"',
    }
    out = [
        "digraph G {", 'bgcolor="transparent"; rankdir=TB;',
        f'node [shape=box style="rounded,filled" fontname="IBM Plex Mono" fontsize=11 color="{t["border"]}" '
        f'fontcolor="{t["text"]}" fillcolor="{t["panel"]}"];',
        f'edge [color="{t["muted"]}" fontcolor="{t["muted"]}" fontname="IBM Plex Mono" fontsize=10];',
    ]
    for nid, desc, kind in nodes:
        extra = f' penwidth=2.5 color="{t["amber"]}"' if nid == current else ""
        out.append(f'{nid} [label="{nid}\\n{desc}" {style[kind]}{extra}];')
    for a, b_, lab in edges:
        out.append(f'{a} -> {b_} [label=" {lab}"];')
    out.append("}")
    return "\n".join(out)


# ===========================================================================
# Transportation: shared grid
# ===========================================================================

def _tp_example():
    ex = TP_EXAMPLES["Classic 3×4 · balanced"]
    return np.array(ex["cost"], float), np.array(ex["supply"], float), np.array(ex["demand"], float)


def _grid(cost, alloc, supply, demand, cls=None, row_extra=None, col_extra=None,
          row_extra_label="", col_extra_label="", cell_text=None, basis=None,
          supply_label="Supply", demand_label="Demand"):
    """Allocation grid. cls: {(i, j): css}. cell_text overrides a cell's content."""
    m, n = cost.shape
    cls = cls or {}
    header = [""] + [f"D{j + 1}" for j in range(n)] + [supply_label] + ([row_extra_label] if row_extra is not None else [])
    rows = []
    for i in range(m):
        r = [f"S{i + 1}"]
        for j in range(n):
            if cell_text and (i, j) in cell_text:
                content = cell_text[(i, j)]
            elif alloc[i, j] > 0 or (basis and (i, j) in basis):
                content = f'<span class="alloc">{fx(alloc[i, j])}</span><span class="cost">@{fx(cost[i, j])}</span>'
            else:
                content = f'<span class="dim">{fx(cost[i, j])}</span>'
            r.append((content, cls.get((i, j), "")))
        r.append((fx(supply[i]), "dim" if supply[i] == 0 else ""))
        if row_extra is not None:
            r.append((row_extra[i], cls.get(("row", i), "")))
        rows.append(r)
    d = [demand_label] + [(fx(demand[j]), "dim" if demand[j] == 0 else "") for j in range(n)] + [""]
    if row_extra is not None:
        d.append("")
    rows.append(d)
    if col_extra is not None:
        e = [col_extra_label] + [(col_extra[j], cls.get(("col", j), "")) for j in range(n)] + [""]
        if row_extra is not None:
            e.append("")
        rows.append(e)
    return table(header, rows)


def _total(cost, alloc):
    return float((cost * alloc).sum())


def build_nwcr(t):
    cost, supply, demand = _tp_example()
    alloc = np.zeros_like(cost)
    s, d = supply.copy(), demand.copy()
    steps = [Step("Start in the north-west corner",
                  "Ignore costs completely. Start at the top-left cell (S1, D1) and fill the grid like reading a page: "
                  "give each cell as much as the row's supply and the column's demand allow.",
                  _grid(cost, alloc, s, d, {(0, 0): "hit"}, supply_label="Supply left", demand_label="Demand left"))]
    i = j = 0
    m, n = cost.shape
    while i < m and j < n:
        if s[i] == 0:
            i += 1
            continue
        if d[j] == 0:
            j += 1
            continue
        q = min(s[i], d[j])
        sb, db = s[i], d[j]
        alloc[i, j] = q
        s[i] -= q
        d[j] -= q
        if s[i] == 0 and d[j] == 0:
            move = f"S{i + 1} and D{j + 1} are both used up"
        elif s[i] == 0:
            move = f"S{i + 1} is used up, so move **down**"
        else:
            move = f"D{j + 1} is satisfied, so move **right**"
        steps.append(Step(f"Allocate at (S{i + 1}, D{j + 1})",
                          f"Supply left {fx(sb)}, demand left {fx(db)}. Allocate the smaller: **{fx(q)}**. {move}.",
                          _grid(cost, alloc, s, d, {(i, j): "hit"}, supply_label="Supply left", demand_label="Demand left")))
    total = _total(cost, alloc)
    terms = " + ".join(f"{fx(alloc[a, b_])}×{fx(cost[a, b_])}" for a in range(m) for b_ in range(n) if alloc[a, b_] > 0)
    steps.append(Step("Total cost", f"{terms} = **{fx(total)}**. A valid starting solution, but usually far from the cheapest.",
                      _grid(cost, alloc, s, d, supply_label="Supply left", demand_label="Demand left")))
    return steps, {"status": "optimal", "value": total, "alloc": alloc}


def build_lcm(t):
    cost, supply, demand = _tp_example()
    alloc = np.zeros_like(cost)
    s, d = supply.copy(), demand.copy()
    m, n = cost.shape
    steps = [Step("Look for the cheapest route",
                  "Repeatedly pick the cheapest cell whose row still has supply and whose column still has demand, "
                  "and give it as much as possible. Ties go to the first such cell, reading row by row (as OTTools does).",
                  _grid(cost, alloc, s, d, supply_label="Supply left", demand_label="Demand left"))]
    while True:
        best = None
        for i in range(m):
            for j in range(n):
                if s[i] > 0 and d[j] > 0 and (best is None or cost[i, j] < cost[best]):
                    best = (i, j)
        if best is None:
            break
        i, j = best
        q = min(s[i], d[j])
        sb, db = s[i], d[j]
        alloc[i, j] = q
        s[i] -= q
        d[j] -= q
        crossed = []
        if s[i] == 0:
            crossed.append(f"row S{i + 1}")
        if d[j] == 0:
            crossed.append(f"column D{j + 1}")
        css = {(a, b_): "dim" for a in range(m) for b_ in range(n) if (s[a] == 0 or d[b_] == 0) and alloc[a, b_] == 0}
        css[(i, j)] = "hit"
        steps.append(Step(f"Cheapest open cell: (S{i + 1}, D{j + 1}) at {fx(cost[i, j])}",
                          f"Allocate min({fx(sb)}, {fx(db)}) = **{fx(q)}**. Cross out {' and '.join(crossed)}.",
                          _grid(cost, alloc, s, d, css, supply_label="Supply left", demand_label="Demand left")))
    total = _total(cost, alloc)
    steps.append(Step("Total cost", f"Total = **{fx(total)}**. Cheaper than North-West Corner, but greedy choices can "
                      "force expensive leftovers at the end.", _grid(cost, alloc, s, d, supply_label="Supply left",
                                                                     demand_label="Demand left")))
    return steps, {"status": "optimal", "value": total, "alloc": alloc}


def _penalty(vals):
    v = sorted(vals)
    return v[0] if len(v) == 1 else v[1] - v[0]


def vam(cost, supply, demand, record=True):
    alloc = np.zeros_like(cost)
    s, d = supply.copy(), demand.copy()
    m, n = cost.shape
    steps = []
    while (s > 0).any() and (d > 0).any():
        rows = [i for i in range(m) if s[i] > 0]
        cols = [j for j in range(n) if d[j] > 0]
        rp = {i: _penalty([cost[i, j] for j in cols]) for i in rows}
        cp = {j: _penalty([cost[i, j] for i in rows]) for j in cols}
        rmax, cmax = max(rp.values()), max(cp.values())
        if rmax >= cmax:
            i = next(i for i in rows if rp[i] == rmax)
            j = min(cols, key=lambda j: (cost[i, j], j))
            line = f"row S{i + 1} (penalty {fx(rmax)})"
            css = {(i, jj): "enter" for jj in cols}
            css[("row", i)] = "enter"
        else:
            j = next(j for j in cols if cp[j] == cmax)
            i = min(rows, key=lambda i: (cost[i, j], i))
            line = f"column D{j + 1} (penalty {fx(cmax)})"
            css = {(ii, j): "enter" for ii in rows}
            css[("col", j)] = "enter"
        css[(i, j)] = "pivot"
        q = min(s[i], d[j])
        sb, db = s[i], d[j]
        if record:
            rpen = [fx(rp[k]) if k in rp else "–" for k in range(m)]
            cpen = [fx(cp[k]) if k in cp else "–" for k in range(n)]
            before = alloc.copy()
            before[i, j] = q
            s2, d2 = s.copy(), d.copy()
            s2[i] -= q
            d2[j] -= q
            single = " (only one cell is left in it, so its penalty is that cell's cost)" if (
                (rmax >= cmax and len(cols) == 1) or (rmax < cmax and len(rows) == 1)) else ""
            steps.append(Step(
                f"Largest penalty: {line.split(' (')[0]}",
                f"Penalty = gap between the two cheapest open cells in a line: what you lose by not using the cheapest. "
                f"The largest is {line}{single}; rows win ties. Its cheapest cell is (S{i + 1}, D{j + 1}) at "
                f"{fx(cost[i, j])}. Allocate min({fx(sb)}, {fx(db)}) = **{fx(q)}**.",
                _grid(cost, before, s2, d2, css, row_extra=rpen, col_extra=cpen, row_extra_label="Row penalty",
                      col_extra_label="Col penalty", supply_label="Supply left", demand_label="Demand left")))
        alloc[i, j] = q
        s[i] -= q
        d[j] -= q
    return alloc, steps, s, d


def build_vam(t):
    cost, supply, demand = _tp_example()
    alloc, steps, s, d = vam(cost, supply, demand)
    total = _total(cost, alloc)
    steps.insert(0, Step("Compute penalties",
                         "For every row and column, find the two cheapest cells and take the difference. A big penalty "
                         "means 'if you don't use the cheapest cell here, it will hurt'. Vogel serves the most painful "
                         "line first.", _grid(cost, np.zeros_like(cost), supply, demand)))
    steps.append(Step("Total cost", f"Total = **{fx(total)}**. Vogel usually lands at or near the optimum, which makes it "
                      "the standard starting point for MODI.", _grid(cost, alloc, s, d, supply_label="Supply left",
                                                                      demand_label="Demand left")))
    return steps, {"status": "optimal", "value": total, "alloc": alloc}


def _complete_basis(alloc, cost):
    m, n = alloc.shape
    parent = list(range(m + n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    basis = []
    for i in range(m):
        for j in range(n):
            if alloc[i, j] > 0:
                basis.append((i, j))
                parent[find(i)] = find(m + j)
    for i, j in sorted(((i, j) for i in range(m) for j in range(n) if alloc[i, j] == 0), key=lambda c: cost[c]):
        if len(basis) >= m + n - 1:
            break
        if find(i) != find(m + j):
            basis.append((i, j))
            parent[find(i)] = find(m + j)
    return basis


def _loop(basis, start):
    cells = set(basis) | {start}

    def search(path, row_move):
        last = path[-1]
        for cell in cells:
            if cell == last:
                continue
            if row_move and cell[0] != last[0]:
                continue
            if not row_move and cell[1] != last[1]:
                continue
            if cell == start and len(path) >= 4:
                return path
            if cell in path:
                continue
            found = search(path + [cell], not row_move)
            if found:
                return found
        return None

    return search([start], True) or search([start], False)


def build_modi(t):
    cost, supply, demand = _tp_example()
    alloc, _, _, _ = vam(cost, supply, demand, record=False)
    m, n = cost.shape
    basis = _complete_basis(alloc, cost)
    total = _total(cost, alloc)
    steps = [Step("Start from Vogel's solution",
                  f"MODI does not build a solution; it improves one. OTTools starts from Vogel's answer (cost "
                  f"**{fx(total)}**). A usable basis needs m + n − 1 = {m + n - 1} cells; this one has {len(basis)}.",
                  _grid(cost, alloc, supply, demand, basis=basis))]
    for it in range(1, 20):
        u, v = [None] * m, [None] * n
        u[0] = 0.0
        changed = True
        while changed:
            changed = False
            for i, j in basis:
                if u[i] is not None and v[j] is None:
                    v[j] = cost[i, j] - u[i]; changed = True
                elif v[j] is not None and u[i] is None:
                    u[i] = cost[i, j] - v[j]; changed = True
        delta = {(i, j): cost[i, j] - u[i] - v[j] for i in range(m) for j in range(n) if (i, j) not in basis}
        texts = {}
        css = {}
        for (i, j), dv in delta.items():
            texts[(i, j)] = f'<span class="{"neg" if dv < -1e-9 else "dim"}">Δ {fx(dv)}</span><span class="cost">@{fx(cost[i, j])}</span>'
        ucol = [fx(x) for x in u]
        vrow = [fx(x) for x in v]
        neg = {k: dv for k, dv in delta.items() if dv < -1e-9}
        grid_kw = dict(row_extra=ucol, col_extra=vrow, row_extra_label="uᵢ", col_extra_label="vⱼ", cell_text=texts, basis=basis)
        if not neg:
            steps.append(Step(f"Iteration {it}: optimal",
                              "Set u₁ = 0 and solve uᵢ + vⱼ = cᵢⱼ for every allocated cell. For each empty cell, "
                              "Δᵢⱼ = cᵢⱼ − uᵢ − vⱼ is how much the total changes per unit sent along that route. "
                              f"**No Δ is negative**, so no route can lower the cost: total **{fx(_total(cost, alloc))}** is optimal.",
                              _grid(cost, alloc, supply, demand, css, **grid_kw)))
            return steps, {"status": "optimal", "value": _total(cost, alloc), "alloc": alloc}
        e = min(neg, key=lambda k: (neg[k], k))
        path = _loop(basis, e)
        minus = path[1::2]
        theta = min(alloc[c] for c in minus)
        for k, cell in enumerate(path):
            css[cell] = "plus" if k % 2 == 0 else "minus"
        css[e] = "plus hit"
        route = " → ".join(f"(S{i + 1},D{j + 1}){'+' if k % 2 == 0 else '−'}" for k, (i, j) in enumerate(path))
        old = _total(cost, alloc)
        steps.append(Step(
            f"Iteration {it}: find an improving route",
            "Set u₁ = 0 and solve uᵢ + vⱼ = cᵢⱼ on the allocated cells, then Δᵢⱼ = cᵢⱼ − uᵢ − vⱼ for the empty ones. "
            f"The most negative is **Δ at (S{e[0] + 1}, D{e[1] + 1}) = {fx(neg[e])}**: each unit sent there saves "
            f"{fx(-neg[e])}. To keep rows and columns balanced, shift units around a closed loop: {route}. "
            f"θ = smallest amount on a − cell = **{fx(theta)}**. New cost = {fx(old)} − {fx(-neg[e])} × {fx(theta)} = "
            f"**{fx(old + neg[e] * theta)}**.",
            _grid(cost, alloc, supply, demand, css, **grid_kw)))
        for k, cell in enumerate(path):
            alloc[cell] += theta if k % 2 == 0 else -theta
        leaving = next(c for c in minus if abs(alloc[c]) < 1e-9)
        alloc[leaving] = 0.0
        basis = [c for c in basis if c != leaving] + [e]
    raise RuntimeError("MODI did not converge")


# ===========================================================================
# Lesson catalogue
# ===========================================================================

LESSONS: dict[str, Lesson] = {
    "Graphical method": Lesson(
        "Graphical method", "Linear programming",
        "Solve a 2-variable LP by drawing it: shade the region every constraint allows, then pick its best corner.",
        "There are exactly two decision variables (OTTools also handles three, in 3D). Great for building intuition.",
        "There are more than three variables. Use Simplex or Big M.",
        "Each constraint is a straight line that cuts the plane in half. Keep the half that satisfies it; what survives "
        "every cut is the **feasible region**, a convex polygon. The objective Z = c₁x₁ + c₂x₂ draws parallel lines "
        "(one for each value of Z). Push that line in the improving direction and the last feasible point it touches "
        "is a **corner**. So you only need to check the corners.",
        ["Shading the wrong side: always test a point such as the origin.",
         "Forgetting x₁ ≥ 0 and x₂ ≥ 0: they are corners too, e.g. (0, 6).",
         "Assuming there is always an answer: an open region can make Z unbounded."],
        "Glass factory · max, 2 variables", "Graphical", build_graphical,
        [r"\max\ Z = 3x_1 + 5x_2", r"x_1 \le 4,\quad 2x_2 \le 12,\quad 3x_1 + 2x_2 \le 18,\quad x_1, x_2 \ge 0"]),
    "Simplex": Lesson(
        "Simplex", "Linear programming",
        "Walk from corner to neighbouring corner of the feasible region, improving Z each time, using a table of numbers.",
        "Any number of variables, with all constraints of the form ≤ and non-negative right-hand sides.",
        "There are ≥ or = constraints (no obvious starting corner). Use Big M.",
        "Add a **slack** variable to each ≤ row to turn it into an equation. Setting the decision variables to 0 gives a "
        "starting corner where the slacks are the **basic** variables. Each iteration: the most negative Z-row entry "
        "picks the variable that improves Z fastest (**entering**); the **ratio test** finds how far it can grow before a "
        "basic variable hits 0 (**leaving**). A **pivot** swaps them. When the Z row has no negatives, no neighbouring "
        "corner is better, so you're optimal.",
        ["Using the largest ratio, or a negative or zero entry, in the ratio test. Only positive entries count; take the smallest.",
         "Forgetting to update the Z row during the pivot.",
         "Reading the answer from the wrong column: values are in RHS, next to their basic variable."],
        "Glass factory · max, 2 variables", "Simplex", build_simplex,
        [r"\max\ Z = 3x_1 + 5x_2", r"x_1 + s_1 = 4,\quad 2x_2 + s_2 = 12,\quad 3x_1 + 2x_2 + s_3 = 18"]),
    "Big M": Lesson(
        "Big M", "Linear programming",
        "Simplex for problems with ≥ and = constraints, using temporary artificial variables with a huge penalty M.",
        "Some constraints are ≥ or =, so the origin is not a valid starting corner.",
        "All constraints are ≤ (plain Simplex is simpler).",
        "A ≥ row gets a **surplus** variable (subtracted) and an **artificial** variable; an = row gets an artificial only. "
        "Artificials make a starting basis possible but have no real meaning, so the objective charges a penalty **M** "
        "(think: a number bigger than anything else) for each. Simplex then drives them out. If one is still positive "
        "at the end, the original problem was **infeasible**.",
        ["Forgetting to clear M from the Z row before the first iteration.",
         "Comparing a + bM entries by a instead of by b: M dominates.",
         "Minimisation: either maximise −Z (as here) or flip the entering rule. Don't mix the two."],
        "Mixed constraints · min, ≥ and =", "Big M", build_bigm,
        [r"\min\ Z = 4x_1 + x_2", r"3x_1 + x_2 = 3,\quad 4x_1 + 3x_2 \ge 6,\quad x_1 + 2x_2 \le 4"]),
    "Branch & Bound": Lesson(
        "Branch & Bound", "Linear programming",
        "Find the best whole-number solution by solving LPs and splitting on fractional variables.",
        "Variables must be integers: units, people, trucks.",
        "Fractions are fine: plain LP is much faster.",
        "Solve the LP ignoring integrality (the **relaxation**). Its Z is an upper bound on any integer answer. If some "
        "xⱼ is fractional, say 1.5, no integer solution lies strictly between 1 and 2, so **branch** into xⱼ ≤ 1 and "
        "xⱼ ≥ 2. Keep the best integer answer found (the **incumbent**) and **prune** any branch whose LP bound can't "
        "beat it. OTTools explores depth-first, ≤ branch first.",
        ["Rounding the LP answer: (3, 1.5) rounded is not optimal here, and rounding can even be infeasible.",
         "Pruning on a bound that is merely equal or worse: that is correct, since it cannot improve the incumbent.",
         "Forgetting that each child keeps all of its parent's extra bounds."],
        "Whole units only · max, integer", "Integer", build_bnb,
        [r"\max\ Z = 5x_1 + 4x_2", r"6x_1 + 4x_2 \le 24,\quad x_1 + 2x_2 \le 6,\quad x_1, x_2 \in \mathbb{Z}_{\ge 0}"]),
    "North-West Corner": Lesson(
        "North-West Corner", "Transportation",
        "The simplest starting solution: fill the grid from the top-left corner, ignoring costs.",
        "You need any valid starting allocation quickly, or as a baseline to compare against.",
        "You want a good answer. It ignores costs entirely.",
        "Start at (S1, D1). Allocate as much as possible: the smaller of the remaining supply and demand. If the row's "
        "supply is used up, move down; if the column's demand is met, move right. Repeat until you reach the bottom-right.",
        ["Allocating more than the remaining supply or demand.",
         "Moving both down and right when only one is exhausted.",
         "Forgetting to balance first: OTTools adds a dummy row or column automatically."],
        "Classic 3×4 · balanced", "North-West Corner", build_nwcr),
    "Least Cost": Lesson(
        "Least Cost", "Transportation",
        "Greedy start: always fill the cheapest route still available.",
        "You want a quick starting solution that pays attention to costs.",
        "You need the optimum: follow up with MODI.",
        "Find the cheapest cell whose row still has supply and whose column still has demand. Allocate as much as "
        "possible, cross out whichever line is exhausted, and repeat.",
        ["Choosing a cell in a crossed-out row or column.",
         "Breaking ties inconsistently. OTTools takes the first cheapest cell reading row by row.",
         "Assuming greedy means optimal: the last allocations are often forced onto expensive routes."],
        "Classic 3×4 · balanced", "Least Cost", build_lcm),
    "Vogel's Approximation": Lesson(
        "Vogel's Approximation", "Transportation",
        "Smarter start: serve first the row or column that would lose the most by missing its cheapest route.",
        "You want the best starting solution, often already optimal. The usual input to MODI.",
        "Speed matters more than quality on very large problems (penalties are recomputed every step).",
        "For each open row and column, the **penalty** is the difference between its two cheapest open cells. Pick the "
        "line with the largest penalty, allocate as much as possible to its cheapest cell, cross out the exhausted line "
        "and recompute penalties.",
        ["Computing penalties over crossed-out cells. Only open cells count.",
         "Choosing the largest cost instead of the largest penalty.",
         "Single-cell lines: OTTools uses that cell's cost as the penalty so it gets served."],
        "Classic 3×4 · balanced", "Vogel's Approximation", build_vam),
    "MODI": Lesson(
        "MODI", "Transportation",
        "Test a starting solution for optimality and improve it until no route can lower the cost.",
        "You have a starting allocation (OTTools uses Vogel's) and want the true optimum.",
        "The basis has fewer than m + n − 1 cells and you haven't fixed the degeneracy (OTTools does this for you).",
        "Give every source a number uᵢ and every destination a number vⱼ so that uᵢ + vⱼ = cᵢⱼ on each allocated cell "
        "(start with u₁ = 0). For each empty cell, **Δᵢⱼ = cᵢⱼ − uᵢ − vⱼ** is the change in total cost per unit sent along "
        "that route. If every Δ ≥ 0 you're optimal. Otherwise bring in the most negative cell, move θ units around a "
        "closed **loop** of alternating +/− cells, and repeat.",
        ["Computing Δ for allocated cells: they are always 0.",
         "Loops that turn on an empty cell: every corner except the start must be allocated.",
         "θ is the smallest allocation on a − corner, not a + corner."],
        "Classic 3×4 · balanced", "MODI (optimal)", build_modi),
}


def check(lesson: Lesson, final: dict) -> tuple[str, bool]:
    """Run the real OTTools function on the lesson's example and compare."""
    if lesson.kind == "lp":
        ex = LP_EXAMPLES[lesson.example]
        A = [r[:-2] for r in ex["rows"]]
        ops = [r[-2] for r in ex["rows"]]
        b = [r[-1] for r in ex["rows"]]
        res = solvers.solve_lp(lesson.solver_method, ex["c"], A, b, ops, ex["sense"] == "Minimize")
        ok = res.status == "optimal" and abs(res.value - float(final["value"])) < 1e-6
        return res.code, ok
    ex = TP_EXAMPLES[lesson.example]
    res = solvers.solve_tp(ex["cost"], ex["supply"], ex["demand"], lesson.solver_method)
    ok = res.status == "optimal" and abs(res.total - float(final["value"])) < 1e-6
    return res.code, ok
