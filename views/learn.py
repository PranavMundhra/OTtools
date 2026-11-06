import streamlit as st

import learn_steps as L
import ui
from examples import TP_EXAMPLES

ss = st.session_state
LP = [k for k, v in L.LESSONS.items() if v.group == "Linear programming"]
TP = [k for k, v in L.LESSONS.items() if v.group == "Transportation"]

if "learn_goto" in ss:
    ss.learn_algo = ss.pop("learn_goto")
ss.setdefault("learn_algo", LP[0])


@st.cache_data(show_spinner=False)
def lesson_steps(key: str, theme: str):
    lesson = L.LESSONS[key]
    steps, final = lesson.build(ui.TOKENS[theme])
    code, ok = L.check(lesson, final)
    return steps, final, code, ok


def pick(group_key: str, other_key: str):
    if ss.get(group_key):
        ss.learn_algo = ss[group_key]
        ss[other_key] = None
    else:                                  # clicking the selected pill again: keep it selected
        ss[group_key] = ss.learn_algo


ss.learn_pick_lp = ss.learn_algo if ss.learn_algo in LP else None
ss.learn_pick_tp = ss.learn_algo if ss.learn_algo in TP else None

ui.eyebrow("Learn")
st.title("How the algorithms work")
ui.lede("Pick an algorithm and step through a worked example: every tableau, pivot, penalty and loop, "
        "with the reason for each move. At the end, the real package solves the same problem as a check.")

st.pills("Linear programming", LP, key="learn_pick_lp", on_change=pick, args=("learn_pick_lp", "learn_pick_tp"))
st.pills("Transportation", TP, key="learn_pick_tp", on_change=pick, args=("learn_pick_tp", "learn_pick_lp"))

lesson = L.LESSONS[ss.learn_algo]
steps, final, code, ok = lesson_steps(lesson.key, ui.mode())

st.divider()
st.header(lesson.key)
ui.lede(lesson.summary)
a, b = st.columns(2, gap="medium")
with a, st.container(border=True, height="stretch"):
    st.markdown(f"**Use it when** {lesson.use_when[0].lower() + lesson.use_when[1:]}")
with b, st.container(border=True, height="stretch"):
    st.markdown(f"**Not suitable when** {lesson.avoid_when[0].lower() + lesson.avoid_when[1:]}")

st.subheader("The idea")
st.markdown(lesson.idea)

st.subheader("Worked example")
if lesson.kind == "lp":
    st.latex(r"\begin{aligned}" + r"\\".join(lesson.latex) + r"\end{aligned}")
else:
    ex = TP_EXAMPLES[lesson.example]
    rows = [[f"S{i + 1}"] + [ui.num(c) for c in ex["cost"][i]] + [ui.num(ex["supply"][i])] for i in range(len(ex["supply"]))]
    rows.append(["Demand"] + [ui.num(d) for d in ex["demand"]] + [""])
    ui.show_html(ui.table([""] + [f"D{j + 1}" for j in range(len(ex["demand"]))] + ["Supply"], rows))
    st.caption("Each cell is the cost of shipping one unit along that route.")

# ---------------------------------------------------------------- step player
st.subheader("Step through it")
N = len(steps)
key = f"learn_step_{lesson.key}"
ss.setdefault(key, 1)
ss[key] = min(max(ss[key], 1), N)


def move(delta):
    ss[key] = min(max(ss[key] + delta, 1), N)


with st.container(horizontal=True, vertical_alignment="center"):
    st.button("Previous", icon=":material/chevron_left:", on_click=move, args=(-1,), disabled=ss[key] == 1)
    st.button("Next", icon=":material/chevron_right:", icon_position="right", on_click=move, args=(1,),
              disabled=ss[key] == N, type="primary")
    st.slider("Step", 1, N, key=key, label_visibility="collapsed", width=260)

step = steps[ss[key] - 1]
st.markdown(f"##### Step {ss[key]} of {N} · {step.title}")
ui.why(step.why)
if step.html:
    ui.show_html(step.html)
if step.fig is not None:
    ui.plot(step.fig, height=440, key=f"learn_fig_{lesson.key}")
if step.dot:
    st.graphviz_chart(step.dot)

if lesson.key in ("Simplex", "Big M"):
    ui.show_html('<p class="ot-legend"><span style="background:var(--ot-amber-soft)"></span>entering column / '
                 'leaving row<span style="background:var(--ot-mint)"></span>pivot'
                 '<span style="background:var(--ot-error)"></span>negative Z-row entry (can still improve)</p>')
elif lesson.key == "MODI":
    ui.show_html('<p class="ot-legend"><span style="box-shadow:inset 0 0 0 2px var(--ot-mint)"></span>loop cell +θ'
                 '<span style="box-shadow:inset 0 0 0 2px var(--ot-amber)"></span>loop cell −θ'
                 '<span style="background:var(--ot-error)"></span>negative Δ</p>')
elif lesson.key == "Vogel's Approximation":
    ui.show_html('<p class="ot-legend"><span style="background:var(--ot-amber-soft)"></span>line with the largest '
                 'penalty<span style="background:var(--ot-mint)"></span>cell allocated this step</p>')
elif lesson.kind == "tp":
    ui.show_html('<p class="ot-legend"><span style="background:var(--ot-mint-soft)"></span>cell allocated this step</p>')
elif lesson.key == "Branch & Bound":
    ui.show_html('<p class="ot-legend"><span style="box-shadow:inset 0 0 0 2px var(--ot-amber)"></span>current node'
                 '<span style="background:var(--ot-mint)"></span>integer solution'
                 '<span style="box-shadow:inset 0 0 0 2px var(--ot-muted)"></span>pruned (dashed)</p>')

# ---------------------------------------------------------------- check + mistakes
st.subheader("Check against OTTools")
if ok:
    st.success(f"OTTools {ui.PACKAGE_VERSION} gets the same answer as this walkthrough.", icon=":material/check_circle:")
else:
    st.error("The package's answer differs from this walkthrough. Please report this.", icon=":material/error:")
st.code(code, language="python")

st.subheader("Common mistakes")
st.markdown("\n".join(f"- {m}" for m in lesson.mistakes))

if st.button("Try this problem in the solver", type="primary", icon=":material/arrow_forward:"):
    if lesson.kind == "lp":
        ss.lp_goto = (lesson.example, lesson.solver_method)
        st.switch_page("views/lp.py")
    else:
        ss.tp_goto = (lesson.example, lesson.solver_method)
        st.switch_page("views/transport.py")
