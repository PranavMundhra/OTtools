import pandas as pd
import streamlit as st

import solvers
import ui
from examples import DEFAULT_LP, LP_EXAMPLES

ss = st.session_state
TYPES = ["≤", "≥", "="]
LESSON_FOR = {"Graphical": "Graphical method", "Simplex": "Simplex", "Big M": "Big M", "Integer": "Branch & Bound"}


# ---------------------------------------------------------------- state helpers
def _cols(n):
    return [f"x{j + 1}" for j in range(n)]


def _rows_df(rows, n):
    data = []
    for r in rows:
        coefs = [float(v) for v in r[:-2]][:n]
        data.append(coefs + [0.0] * (n - len(coefs)) + [r[-2], float(r[-1])])
    return pd.DataFrame(data, columns=_cols(n) + ["Type", "RHS"])


def _bump():
    ss.lp_ver = ss.get("lp_ver", 0) + 1
    ss.pop("lp_result", None)
    ss.pop("lp_c_last", None)
    ss.pop("lp_rows_last", None)


def load_example(name, method=None):
    ex = LP_EXAMPLES[name]
    ss.lp_n = len(ex["c"])
    ss.lp_sense = ex["sense"]
    ss.lp_c = [float(v) for v in ex["c"]]
    ss.lp_rows = _rows_df(ex["rows"], ss.lp_n)
    ss.lp_method = method or ex["method"]
    ss.lp_example_pick = name
    _bump()


def on_example():
    if ss.lp_example_pick:
        load_example(ss.lp_example_pick)


def clear():
    n = ss.lp_n
    ss.lp_c = [0.0] * n
    ss.lp_rows = pd.DataFrame([[0.0] * n + ["≤", 0.0] for _ in range(2)], columns=_cols(n) + ["Type", "RHS"])
    ss.lp_example_pick = None
    _bump()


def on_resize():
    """Change the number of variables, keeping every value already typed."""
    n = ss.lp_n
    c = list(ss.get("lp_c_last", ss.lp_c))
    rows = ss.get("lp_rows_last", ss.lp_rows)
    ss.lp_c = (c + [0.0] * n)[:n]
    new = pd.DataFrame({col: (rows[col].values if col in rows else [0.0] * len(rows)) for col in _cols(n)})
    new["Type"] = rows["Type"].values
    new["RHS"] = rows["RHS"].values
    ss.lp_rows = new
    _bump()


# Streamlit forgets widget values when you visit another page; these copies bring them back.
WIDGETS = ["lp_n", "lp_sense", "lp_method", "lp_example_pick"]

if "lp_goto" in ss:                       # arriving from a Learn lesson
    load_example(*ss.pop("lp_goto"))
elif "lp_c" not in ss:
    load_example(DEFAULT_LP)
else:
    for k in WIDGETS:
        if k not in ss and f"_{k}" in ss:
            ss[k] = ss[f"_{k}"]
    if f"lp_rows_ed_{ss.lp_ver}" not in ss and "lp_rows_last" in ss:
        ss.lp_rows = ss.lp_rows_last.reset_index(drop=True)   # keep edits made before leaving the page
        ss.lp_c = ss.lp_c_last

# ---------------------------------------------------------------- page
ui.eyebrow("Solver")
st.title("Linear Programming")
ui.lede("Type your problem into the tables, or load an example, then pick a method. "
        "Every variable is assumed to be ≥ 0.")

with st.container(horizontal=True, vertical_alignment="bottom", gap="medium"):
    st.selectbox("Load an example", list(LP_EXAMPLES), key="lp_example_pick", on_change=on_example,
                 placeholder="Choose an example…", width=330)
    st.segmented_control("Objective", ["Maximize", "Minimize"], key="lp_sense", required=True)
    st.number_input("Variables", min_value=1, max_value=10, step=1, key="lp_n", on_change=on_resize, width=120)
    st.button("Clear", on_click=clear, icon=":material/backspace:", type="tertiary")

n = ss.lp_n
cols = _cols(n)
num_cfg = {c: st.column_config.NumberColumn(c, default=0.0) for c in cols}

st.markdown("**Objective coefficients** · Z = " + " + ".join(f"c{solvers._sub(j + 1)}x{solvers._sub(j + 1)}" for j in range(n)))
c_edit = st.data_editor(pd.DataFrame([ss.lp_c], columns=cols), key=f"lp_c_ed_{ss.lp_ver}",
                        hide_index=True, column_config=num_cfg)
ss.lp_c_last = [0.0 if pd.isna(v) else float(v) for v in c_edit.iloc[0]]

st.markdown("**Constraints** · one row each")
row_cfg = dict(num_cfg)
row_cfg["Type"] = st.column_config.SelectboxColumn("Type", options=TYPES, required=True, default="≤", width="small")
row_cfg["RHS"] = st.column_config.NumberColumn("RHS", default=0.0)
rows_edit = st.data_editor(ss.lp_rows, key=f"lp_rows_ed_{ss.lp_ver}", hide_index=True,
                           num_rows="dynamic", column_config=row_cfg)
ss.lp_rows_last = rows_edit
st.caption("Add or delete rows from the table's toolbar, or paste cells straight from a spreadsheet.")

# ---------------------------------------------------------------- parse + preview
c_vals = ss.lp_c_last
df = rows_edit.dropna(how="all", subset=cols + ["RHS"])
errors = []
if df.empty:
    errors.append("Add at least one constraint.")
if df["RHS"].isna().any():
    errors.append("Every constraint needs a right-hand side (RHS).")
A = df[cols].fillna(0.0).astype(float).values.tolist()
ops = df["Type"].fillna("≤").tolist()
b = df["RHS"].fillna(0.0).astype(float).tolist()
minimize = ss.lp_sense == "Minimize"


def _latex_expr(coefs):
    out = ""
    for j, cval in enumerate(coefs):
        if cval == 0:
            continue
        mag = abs(cval)
        term = ("" if mag == 1 else ui.num(mag)) + f"x_{{{j + 1}}}"
        out += (" - " if cval < 0 else " + ") + term if out else ("-" if cval < 0 else "") + term
    return out or "0"


if not errors:
    tex_ops = {"≤": r"\le", "≥": r"\ge", "=": "="}
    lines = [rf"\{'min' if minimize else 'max'}\ \ Z &= {_latex_expr(c_vals)}"]
    for row, op, rhs in zip(A, ops, b):
        lines.append(rf"{_latex_expr(row)} &{tex_ops[op]} {ui.num(rhs)}")
    lines.append(r"x_j &\ge 0")
    with st.expander("Your problem, as the solver will read it", expanded=False):
        st.latex(r"\begin{aligned}" + r"\\".join(lines) + r"\end{aligned}")

# ---------------------------------------------------------------- method + solve
avail = solvers.lp_availability(n, ops)
st.radio("Method", solvers.LP_METHODS, key="lp_method", horizontal=True,
         format_func=lambda m: m if avail[m] is None else f"{m} (not available)")
st.caption(" · ".join(f"✓ {m}" if r is None else f"✕ {m}: {r}" for m, r in avail.items()))
for k in WIDGETS:
    ss[f"_{k}"] = ss.get(k)

for e in errors:
    st.error(e, icon=":material/error:")

signature = repr((c_vals, A, ops, b, minimize, ss.lp_method))
if st.button("Solve", type="primary", icon=":material/play_arrow:", disabled=bool(errors)):
    reason = avail[ss.lp_method]
    if reason:
        st.warning(f"{ss.lp_method} {reason}.", icon=":material/warning:")
    else:
        with st.spinner("Solving with OTTools…"):
            res = solvers.solve_lp(ss.lp_method, c_vals, A, b, ops, minimize, ui.tokens())
        ss.lp_result = (signature, res, minimize, ops)

# ---------------------------------------------------------------- result
if "lp_result" in ss:
    sig0, res, was_min, was_ops = ss.lp_result
    st.divider()
    if sig0 != signature:
        st.info("You've changed the problem since this result. Click **Solve** to update it.", icon=":material/info:")
    tab_names = ["Result", "Chart", "Code"] if res.fig is not None else ["Result", "Code"]
    tabs = st.tabs(tab_names)
    with tabs[0]:
        ui.show_html(f'{ui.status_badge(res.status)} <span class="ot-muted">&nbsp;{res.method}</span>')
        if res.status == "optimal":
            ui.show_html(ui.big_number(("min Z =" if was_min else "max Z ="), ui.num(res.value)))
            names = [f"x{solvers._sub(j + 1)}" for j in range(len(res.x))]
            ui.show_html(ui.table([""] + names, [["value"] + [ui.num(v) for v in res.x]]))
        elif res.status == "unbounded":
            st.warning(res.message or "Z can be improved without limit.", icon=":material/all_inclusive:")
        elif res.status == "unsupported":
            st.info(res.message, icon=":material/info:")
        else:
            st.error(res.message or "No feasible solution.", icon=":material/block:")
        for note in res.notes:
            st.caption(f"ⓘ {note}")
        lesson = LESSON_FOR[res.method]
        if st.button(f"How does {res.method} work?", type="tertiary", icon=":material/school:"):
            ss.learn_goto = lesson
            st.switch_page("views/learn.py")
    if res.fig is not None:
        with tabs[1]:
            ui.plot(res.fig, height=480, key="lp_fig")
            if any(o != "≤" for o in was_ops):
                st.caption("This is OTTools' own figure, recoloured. Constraints are shown as you typed them; "
                           "an open region is drawn only as far as its corner points.")
            else:
                st.caption("This is OTTools' own figure, recoloured for the site.")
    with tabs[-1]:
        st.markdown("The exact call this page just made:")
        st.code(res.code, language="python")
