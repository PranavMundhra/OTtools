import streamlit as st

import solvers
import ui
from examples import LP_EXAMPLES, TP_EXAMPLES

t = ui.tokens()

# ---------------------------------------------------------------- hero
left, right = st.columns([5, 6], gap="large", vertical_alignment="center")
with left:
    ui.eyebrow(f"Python package · v{ui.PACKAGE_VERSION}")
    st.title("Operations research, in one pip install.")
    ui.lede("OTTools solves linear programming and transportation problems in a few lines of Python: "
            "Simplex, Big M, branch and bound, Vogel, MODI and more. Everything on this site is computed "
            "live by the package.")
    st.code("pip install OTTools", language="bash")
    with st.container(horizontal=True):
        if st.button("Solve an LP", type="primary", icon=":material/show_chart:"):
            st.switch_page("views/lp.py")
        if st.button("Transportation", icon=":material/local_shipping:"):
            st.switch_page("views/transport.py")
        if st.button("Learn the algorithms", type="tertiary", icon=":material/school:"):
            st.switch_page("views/learn.py")

with right:
    ex = LP_EXAMPLES["Glass factory · max, 2 variables"]
    A = [r[:-2] for r in ex["rows"]]
    ops = [r[-2] for r in ex["rows"]]
    b = [r[-1] for r in ex["rows"]]
    hero = solvers.solve_lp("Graphical", ex["c"], A, b, ops, False, t)
    if hero.fig is not None:
        ui.plot(hero.fig, height=380, key="hero_fig")
    if hero.status == "optimal":
        st.caption(f"`graphical_method` on a 2-variable LP, solved just now → **Z = {ui.num(hero.value)}** "
                   f"at x₁ = {ui.num(hero.x[0])}, x₂ = {ui.num(hero.x[1])}")

# ---------------------------------------------------------------- what's inside
st.header("What's in the package")
c1, c2, c3 = st.columns(3, gap="medium")
with c1, st.container(border=True, height="stretch"):
    st.subheader("Linear programming")
    st.markdown("- **Graphical**: 2 or 3 variables, with a plot\n"
                "- **Simplex**: ≤ constraints\n"
                "- **Big M**: ≥, ≤ and = constraints\n"
                "- **Integer**: branch and bound")
    if st.button("Open the LP solver", key="card_lp", width="stretch"):
        st.switch_page("views/lp.py")
with c2, st.container(border=True, height="stretch"):
    st.subheader("Transportation")
    st.markdown("- **North-West Corner**, **Least Cost**, **Vogel**: starting solutions\n"
                "- **MODI**: proves and reaches the optimum\n"
                "- **Auto-balancing**: adds a dummy row or column when supply ≠ demand")
    if st.button("Open the transportation solver", key="card_tp", width="stretch"):
        st.switch_page("views/transport.py")
with c3, st.container(border=True, height="stretch"):
    st.subheader("Learn")
    st.markdown("Step through each algorithm on a worked example: every tableau, pivot, penalty and loop, "
                "with a one-line reason for each move. Each lesson is checked against the package.")
    if st.button("Start learning", key="card_learn", width="stretch"):
        st.switch_page("views/learn.py")

# ---------------------------------------------------------------- quickstart
st.header("Quickstart")
q1, q2 = st.columns(2, gap="medium")
with q1:
    st.markdown("**Linear programming**: maximise 3x₁ + 5x₂")
    res = solvers.solve_lp("Simplex", ex["c"], A, b, ops, False)
    st.code(res.code, language="python")
with q2:
    tex = TP_EXAMPLES["Classic 3×4 · balanced"]
    st.markdown("**Transportation**: 3 sources, 4 destinations")
    tres = solvers.solve_tp(tex["cost"], tex["supply"], tex["demand"], "MODI (optimal)")
    st.code(tres.code, language="python")
st.caption("The `# →` lines are the package's real output for these inputs, computed when this page loaded.")
