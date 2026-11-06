# OTTools website

A Streamlit site that shows the [OTTools](https://pypi.org/project/OTTools/) Python package at work. Visitors can solve linear programming and transportation problems in the browser, see the exact OTTools call behind each answer, and step through how each algorithm works.

Every result on the site is computed live by the package. Nothing is hard-coded.

## What's on the site

| Page | What it does |
|---|---|
| **Home** | What OTTools is, `pip install OTTools`, a live solved example, and a quickstart |
| **Linear Programming** | Graphical (2–3 variables, with a plot), Simplex, Big M, and Integer (branch and bound) |
| **Transportation** | North-West Corner, Least Cost, Vogel's Approximation and MODI, with automatic balancing |
| **Learn** | Step-by-step walkthroughs of all 8 algorithms on worked examples, each checked against the package |

On the solver pages you:
- enter the problem in an editable table, or load an example;
- pick a method (methods that don't fit the problem say why);
- see the answer in three tabs: **Result**, **Chart** (LP) or **Flow** (Transportation), and **Code**. The Code tab shows the exact Python call that produced the answer.

The site has light and dark themes, switched with the toggle in the header.

## Run it locally

Requires Python 3.10+.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501.

## Project layout

```
app.py              Entry point: page navigation, header, footer
views/
  home.py           Landing page
  lp.py             Linear programming solver
  transport.py      Transportation solver
  learn.py          Algorithm lessons with a step player
solvers.py          Thin wrappers around OTTools: normalise results, build code snippets
learn_steps.py      Step-by-step teaching versions of each algorithm, plus lesson text
examples.py         Preset problems shared by the solvers, home page and lessons
ui.py               Theme tokens, CSS layer, theme toggle, tables, Plotly styling
.streamlit/
  config.toml       Light and dark theme colours and fonts
```

## How it works

**Solvers.** `solvers.py` calls the real package functions (`graphical_method`, `simplex_method`, `big_m_method`, `integer_simplex`, `TransportationProblem.solve`). It also fills two gaps in OTTools 0.1.3:

- `graphical_method` only maximises with `≤` constraints, so Minimize problems and `≥` / `=` rows are converted before the call. The page says so, and the generated code shows the conversion.
- `graphical_method` opens its Plotly figure with `fig.show()`. The site captures that figure and draws it on the page instead.

It also double-checks each Graphical answer with `big_m_method`, so an unbounded problem isn't reported as optimal.

**Lessons.** OTTools returns only final answers, so `learn_steps.py` has small teaching versions of each algorithm that record every intermediate step.
- Simplex and Big M use exact fractions and keep M symbolic.
- The teaching versions follow the package's rules: tie-breaking, Vogel penalties, depth-first branch and bound, and MODI starting from Vogel's solution.
- Each lesson runs the real package on the same problem and shows whether the answers match.

**Theme toggle.** Both themes are defined in `config.toml`. The toggle (`ui.theme_toggle`) stores the choice where Streamlit itself keeps it in the browser, then reloads the page. That storage key is internal to Streamlit, so a future Streamlit release could break the toggle. Streamlit's own **Settings → Theme** menu always works as a fallback.

## Testing

There is no automated test suite yet. During development, every page, example and method was exercised with Streamlit's [`AppTest`](https://docs.streamlit.io/develop/api-reference/app-testing), and all 8 lessons were checked against OTTools 0.1.3. A minimal check that a page renders:

```python
from streamlit.testing.v1 import AppTest

at = AppTest.from_file("app.py").run()
at.switch_page("views/lp.py").run()
assert not at.exception
```

## Planned

- Step-by-step output from the package itself (tableaux, MODI u/v values), replacing the teaching versions
- Running several methods on one problem side by side
- Exporting results (CSV / LaTeX)
- Sensitivity analysis

## Links

- Package: [pypi.org/project/OTTools](https://pypi.org/project/OTTools/)
- Package source and issues: [github.com/Strangehumaan/OT](https://github.com/Strangehumaan/OT)

## Authors

Built by [Pranav Mundhra](https://github.com/PranavMundhra) and [Saad Nathani](https://github.com/Strangehumaan).
