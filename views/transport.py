import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import solvers
import ui
from examples import DEFAULT_TP, TP_EXAMPLES

ss = st.session_state
LESSON_FOR = {"North-West Corner": "North-West Corner", "Least Cost": "Least Cost",
              "Vogel's Approximation": "Vogel's Approximation", "MODI (optimal)": "MODI"}
LABEL_FOR_KEY = {v: k for k, v in solvers.TP_METHODS.items()}
WIDGETS = ["tp_m", "tp_n", "tp_method", "tp_example_pick"]


# ---------------------------------------------------------------- state helpers
def _grid_df(cost, supply, demand):
    m, n = len(supply), len(demand)
    data = [list(map(float, cost[i])) + [float(supply[i])] for i in range(m)]
    data.append(list(map(float, demand)) + [np.nan])
    return pd.DataFrame(data, index=[f"S{i + 1}" for i in range(m)] + ["Demand"],
                        columns=[f"D{j + 1}" for j in range(n)] + ["Supply"])


def _bump():
    ss.tp_ver = ss.get("tp_ver", 0) + 1
    ss.pop("tp_result", None)
    ss.pop("tp_grid_last", None)


def load_example(name, method_label=None):
    ex = TP_EXAMPLES[name]
    ss.tp_grid = _grid_df(ex["cost"], ex["supply"], ex["demand"])
    ss.tp_m, ss.tp_n = len(ex["supply"]), len(ex["demand"])
    ss.tp_method = method_label or LABEL_FOR_KEY[ex["method"]]
    ss.tp_example_pick = name
    _bump()


def on_example():
    if ss.tp_example_pick:
        load_example(ss.tp_example_pick)


def clear():
    ss.tp_grid = _grid_df(np.zeros((ss.tp_m, ss.tp_n)), [0] * ss.tp_m, [0] * ss.tp_n)
    ss.tp_example_pick = None
    _bump()


def on_resize():
    """Change the grid size, keeping every value already typed."""
    old = ss.get("tp_grid_last", ss.tp_grid)
    m, n = ss.tp_m, ss.tp_n
    om = len(old) - 1
    on = len(old.columns) - 1
    cost = np.zeros((m, n))
    supply, demand = np.zeros(m), np.zeros(n)
    for i in range(min(m, om)):
        for j in range(min(n, on)):
            cost[i, j] = old.iat[i, j]
        supply[i] = old.iat[i, on]
    for j in range(min(n, on)):
        demand[j] = old.iat[om, j]
    ss.tp_grid = _grid_df(np.nan_to_num(cost), np.nan_to_num(supply), np.nan_to_num(demand))
    _bump()


if "tp_goto" in ss:                       # arriving from a Learn lesson
    load_example(*ss.pop("tp_goto"))
elif "tp_grid" not in ss:
    load_example(DEFAULT_TP)
else:
    for k in WIDGETS:
        if k not in ss and f"_{k}" in ss:
            ss[k] = ss[f"_{k}"]
    if f"tp_grid_ed_{ss.tp_ver}" not in ss and "tp_grid_last" in ss:
        ss.tp_grid = ss.tp_grid_last

# ---------------------------------------------------------------- page
ui.eyebrow("Solver")
st.title("Transportation Problem")
ui.lede("Enter the cost of shipping one unit from each source to each destination, plus supply and demand. "
        "If totals differ, OTTools adds a dummy row or column automatically.")

with st.container(horizontal=True, vertical_alignment="bottom", gap="medium"):
    st.selectbox("Load an example", list(TP_EXAMPLES), key="tp_example_pick", on_change=on_example,
                 placeholder="Choose an example…", width=360)
    st.number_input("Sources", min_value=1, max_value=12, step=1, key="tp_m", on_change=on_resize, width=110)
    st.number_input("Destinations", min_value=1, max_value=12, step=1, key="tp_n", on_change=on_resize, width=130)
    st.button("Clear", on_click=clear, icon=":material/backspace:", type="tertiary")

m, n = ss.tp_m, ss.tp_n
cfg = {f"D{j + 1}": st.column_config.NumberColumn(f"D{j + 1}", min_value=0.0) for j in range(n)}
cfg["Supply"] = st.column_config.NumberColumn("Supply", min_value=0.0)
grid = st.data_editor(ss.tp_grid, key=f"tp_grid_ed_{ss.tp_ver}", column_config=cfg)
ss.tp_grid_last = grid
st.caption("Rows are sources, columns are destinations. The last row holds each destination's demand "
           "(its Supply cell is ignored). You can paste a block of cells from a spreadsheet.")

cost = grid.iloc[:m, :n].to_numpy(dtype=float)
supply = grid.iloc[:m]["Supply"].to_numpy(dtype=float)
demand = grid.iloc[m, :n].to_numpy(dtype=float)
errors = []
if np.isnan(cost).any() or np.isnan(supply).any() or np.isnan(demand).any():
    errors.append("Fill in every cost, supply and demand cell.")
elif (cost < 0).any() or (supply < 0).any() or (demand < 0).any():
    errors.append("Costs, supply and demand must be zero or more.")
elif supply.sum() == 0 or demand.sum() == 0:
    errors.append("Total supply and total demand must both be more than zero.")

if not errors:
    ts, td = supply.sum(), demand.sum()
    if abs(ts - td) < 1e-9:
        st.markdown(f"Supply **{ui.num(ts)}** · Demand **{ui.num(td)}** · ✓ Balanced")
    elif ts > td:
        st.markdown(f"Supply **{ui.num(ts)}** · Demand **{ui.num(td)}** · ⚠ Unbalanced: a dummy "
                    f"destination will absorb the extra **{ui.num(ts - td)}** units at cost 0.")
    else:
        st.markdown(f"Supply **{ui.num(ts)}** · Demand **{ui.num(td)}** · ⚠ Unbalanced: a dummy "
                    f"source will cover the missing **{ui.num(td - ts)}** units at cost 0 (that demand goes unmet).")

st.radio("Method", list(solvers.TP_METHODS), key="tp_method", horizontal=True)
st.caption("North-West Corner, Least Cost and Vogel build a starting solution. "
           "MODI starts from Vogel's and improves it to the cheapest possible.")
for k in WIDGETS:
    ss[f"_{k}"] = ss.get(k)

for e in errors:
    st.error(e, icon=":material/error:")

signature = repr((cost.tolist(), supply.tolist(), demand.tolist(), ss.tp_method))
if st.button("Solve", type="primary", icon=":material/play_arrow:", disabled=bool(errors)):
    with st.spinner("Solving with OTTools…"):
        ss.tp_result = (signature, solvers.solve_tp(cost.tolist(), supply.tolist(), demand.tolist(), ss.tp_method), m, n)


# ---------------------------------------------------------------- result
def _labels(res, m0, n0):
    rows = [f"S{i + 1}" for i in range(res.allocation.shape[0])]
    cols = [f"D{j + 1}" for j in range(res.allocation.shape[1])]
    if res.dummy == "row":
        rows[-1] = "Dummy"
    if res.dummy == "col":
        cols[-1] = "Dummy"
    return rows, cols


def allocation_table(res, m0, n0):
    rows_l, cols_l = _labels(res, m0, n0)
    mm, nn = res.allocation.shape
    hcls = [""] + ["dummy" if (res.dummy == "col" and j == nn - 1) else "" for j in range(nn)] + [""]
    body = []
    for i in range(mm):
        is_dummy_row = res.dummy == "row" and i == mm - 1
        r = [(rows_l[i], "dummy" if is_dummy_row else "")]
        for j in range(nn):
            a, c = res.allocation[i, j], res.cost[i, j]
            dummy = is_dummy_row or (res.dummy == "col" and j == nn - 1)
            if a > 0:
                r.append((f'<span class="alloc">{ui.num(a)}</span><span class="cost">@{ui.num(c)}</span>',
                          "dummy" if dummy else ""))
            else:
                r.append((f'<span class="dim">·</span><span class="cost">@{ui.num(c)}</span>', ""))
        r.append(ui.num(res.supply[i]))
        body.append(r)
    body.append(["Demand"] + [ui.num(d) for d in res.demand] + [""])
    return ui.table([""] + cols_l + ["Supply"], body, hcls)


def sankey(res, m0, n0, t):
    rows_l, cols_l = _labels(res, m0, n0)
    mm, nn = res.allocation.shape
    src, dst, val, colors, costs = [], [], [], [], []
    for i in range(mm):
        for j in range(nn):
            a = res.allocation[i, j]
            if a > 0:
                src.append(i)
                dst.append(mm + j)
                val.append(a)
                costs.append(res.cost[i, j])
                dummy = rows_l[i] == "Dummy" or cols_l[j] == "Dummy"
                colors.append("rgba(128,128,128,0.25)" if dummy else t["fill"])
    node_colors = [t["muted"] if l == "Dummy" else t["teal"] for l in rows_l] + \
                  [t["muted"] if l == "Dummy" else t["mint"] for l in cols_l]
    labels = [f"{l} ({ui.num(s)})" for l, s in zip(rows_l, res.supply)] + \
             [f"{l} ({ui.num(d)})" for l, d in zip(cols_l, res.demand)]
    fig = go.Figure(go.Sankey(
        arrangement="snap",
        node=dict(label=labels, color=node_colors, pad=22, thickness=14, line=dict(width=0)),
        link=dict(source=src, target=dst, value=val, color=colors, customdata=costs,
                  hovertemplate="%{source.label} → %{target.label}<br>%{value} units @ %{customdata}<extra></extra>"),
    ))
    return fig


if "tp_result" in ss:
    sig0, res, m0, n0 = ss.tp_result
    st.divider()
    if sig0 != signature:
        st.info("You've changed the problem since this result. Click **Solve** to update it.", icon=":material/info:")
    if res.status != "optimal":
        st.error(res.message or "The solver could not handle this input.", icon=":material/block:")
        st.code(res.code, language="python")
    else:
        tabs = st.tabs(["Result", "Flow", "Code"])
        with tabs[0]:
            badge = "optimal" if res.method.startswith("MODI") else "starting solution"
            cls = "ok" if badge == "optimal" else "warn"
            ui.show_html(f'<span class="ot-status {cls}">{badge.upper()}</span> '
                         f'<span class="ot-muted">&nbsp;{res.method}</span>')
            ui.show_html(ui.big_number("total cost =", ui.num(res.total)))
            ui.show_html(allocation_table(res, m0, n0))
            if res.dummy == "col":
                st.caption(f"ⓘ The dummy destination receives the {ui.num(res.demand[-1])} units of supply nobody needs. "
                           "In practice those units stay where they are.")
            elif res.dummy == "row":
                st.caption(f"ⓘ The dummy source 'ships' {ui.num(res.supply[-1])} units that don't exist: "
                           "that is the demand left unmet.")
            if badge != "optimal":
                st.caption("ⓘ This is a starting solution. Run **MODI (optimal)** to see whether it can be improved.")
            if st.button(f"How does {res.method.replace(' (optimal)', '')} work?", type="tertiary", icon=":material/school:"):
                ss.learn_goto = LESSON_FOR[res.method]
                st.switch_page("views/learn.py")
        with tabs[1]:
            ui.plot(sankey(res, m0, n0, ui.tokens()), height=420, key="tp_flow")
            st.caption("Band width = units shipped. Hover a band for its cost per unit.")
        with tabs[2]:
            st.markdown("The exact call this page just made:")
            st.code(res.code, language="python")
