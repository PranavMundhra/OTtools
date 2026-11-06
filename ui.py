"""Shared look and chrome for the OTTools site.

One place for the colour tokens, the small CSS layer, the header (links + theme
toggle), the footer, number formatting, HTML tables and Plotly styling.
Streamlit's own widgets are themed by .streamlit/config.toml; this module only
adds what config.toml cannot express.
"""
from __future__ import annotations

import html
import json
import re

import streamlit as st

REPO = "https://github.com/Strangehumaan/OT"
PYPI = "https://pypi.org/project/OTTools/"
ISSUES = "https://github.com/Strangehumaan/OT/issues"
PACKAGE_VERSION = "0.1.3"

# url_path of every page registered in app.py ("" is the home page).
PAGE_SLUGS = ["", "linear-programming", "transportation", "learn"]

TOKENS = {
    "dark": {
        "bg": "#0E1417", "panel": "#152024", "grid": "#1F2E33", "text": "#E8EEEC",
        "muted": "#9DB0AC", "teal": "#4FB3A9", "mint": "#5FD3B4", "amber": "#F2B33D",
        "error": "#FF7B6B", "border": "#2A3B40", "on_mint": "#0E1417",
        "fill": "rgba(95,211,180,0.25)", "amber_soft": "rgba(242,179,61,0.18)",
        "mint_soft": "rgba(95,211,180,0.16)", "gridline": "rgba(31,46,51,0.55)",
        "lines": ["#4FB3A9", "#9DB0AC", "#7C9BD1", "#C79BD8", "#D9A07B"],
    },
    "light": {
        "bg": "#F7F9F8", "panel": "#FFFFFF", "grid": "#E3EBE9", "text": "#10201E",
        "muted": "#4E615D", "teal": "#2F5D5A", "mint": "#16795F", "amber": "#8F5A00",
        "error": "#B42318", "border": "#CBD8D5", "on_mint": "#FFFFFF",
        "fill": "rgba(22,121,95,0.20)", "amber_soft": "rgba(143,90,0,0.12)",
        "mint_soft": "rgba(22,121,95,0.10)", "gridline": "rgba(203,216,213,0.45)",
        "lines": ["#2F5D5A", "#4E615D", "#3E5F9E", "#7A4C8F", "#9A5B2E"],
    },
}

MONO = "'IBM Plex Mono', ui-monospace, monospace"

CSS = """
.stApp {
  background-image:
    linear-gradient(var(--ot-gridline) 1px, transparent 1px),
    linear-gradient(90deg, var(--ot-gridline) 1px, transparent 1px);
  background-size: 24px 24px;
}
.ot-eyebrow { font-family: var(--ot-mono); font-size: .78rem; letter-spacing: .08em;
  text-transform: uppercase; color: var(--ot-teal); margin: 0 0 .2rem; }
.ot-lede { font-size: 1.12rem; color: var(--ot-muted); max-width: 40rem; margin: 0 0 1rem; }
.ot-muted { color: var(--ot-muted); }
.ot-status { display: inline-block; font-family: var(--ot-mono); font-size: .74rem; font-weight: 600;
  letter-spacing: .06em; padding: .12rem .6rem; border-radius: 999px; border: 1px solid currentColor; }
.ot-status.ok { color: var(--ot-mint); }
.ot-status.warn { color: var(--ot-amber); }
.ot-status.bad { color: var(--ot-error); }
.ot-big { font-family: var(--ot-mono); font-size: 2.6rem; font-weight: 500; line-height: 1.15;
  color: var(--ot-text); margin: .35rem 0 .6rem; overflow-wrap: anywhere; }
.ot-big small { font-size: 1rem; color: var(--ot-muted); margin-right: .5rem; font-weight: 400; }
.ot-table-wrap { overflow-x: auto; margin: .4rem 0 1rem; }
.ot-table { border-collapse: collapse; font-family: var(--ot-mono); font-size: .88rem; }
.ot-table th, .ot-table td { border: 1px solid var(--ot-border); padding: .38rem .65rem;
  text-align: right; white-space: nowrap; background: var(--ot-panel); color: var(--ot-text); }
.ot-table th { color: var(--ot-muted); font-weight: 500; }
.ot-table th.rowh { text-align: left; }
.ot-table .enter { background: var(--ot-amber-soft); }
.ot-table .leave { background: var(--ot-amber-soft); }
.ot-table .pivot { background: var(--ot-mint); color: var(--ot-on-mint); font-weight: 600; }
.ot-table .hit { background: var(--ot-mint-soft); }
.ot-table .alloc { color: var(--ot-mint); font-weight: 600; }
.ot-table .cost { color: var(--ot-muted); font-size: .76rem; margin-left: .35rem; }
.ot-table .dim { color: var(--ot-muted); }
.ot-table .neg { color: var(--ot-error); font-weight: 600; }
.ot-table .plus { box-shadow: inset 0 0 0 2px var(--ot-mint); }
.ot-table .minus { box-shadow: inset 0 0 0 2px var(--ot-amber); }
.ot-table .dummy th, .ot-table td.dummy, .ot-table th.dummy { font-style: italic; color: var(--ot-muted); }
.ot-why { border-left: 3px solid var(--ot-amber); background: var(--ot-panel); padding: .6rem .95rem;
  border-radius: 0 6px 6px 0; margin: .4rem 0 1rem; }
.ot-legend { font-size: .82rem; color: var(--ot-muted); }
.ot-legend span { display: inline-block; width: .8rem; height: .8rem; border-radius: 2px;
  vertical-align: -1px; margin: 0 .3rem 0 .8rem; }
.ot-footer { border-top: 1px solid var(--ot-border); margin-top: 3rem; padding: 1.2rem 0 .5rem;
  font-size: .9rem; color: var(--ot-muted); }
.ot-footer a { color: var(--ot-text); }
"""


# ---------------------------------------------------------------------------
# Theme
# ---------------------------------------------------------------------------

def mode() -> str:
    """'light' or 'dark', as reported by the browser for the active Streamlit theme."""
    try:
        kind = st.context.theme.type
    except Exception:
        kind = None
    return "light" if kind == "light" else "dark"


def tokens() -> dict:
    return TOKENS[mode()]


def inject_css() -> None:
    t = tokens()
    variables = "".join(
        f"--ot-{k.replace('_', '-')}:{v};" for k, v in t.items() if isinstance(v, str)
    )
    st.markdown(
        f"<style>:root{{{variables}--ot-mono:{MONO};}}{CSS}</style>",
        unsafe_allow_html=True,
    )


_TOGGLE_HTML = """
<style>
  html, body { margin: 0; background: transparent; overflow: hidden; }
  button { display: inline-flex; align-items: center; gap: 6px; height: 34px; padding: 0 12px;
    border-radius: 999px; border: 1px solid var(--b); background: var(--p); color: var(--t);
    font: 500 13px 'IBM Plex Sans', system-ui, sans-serif; cursor: pointer; }
  button:hover { border-color: var(--a); }
  button:focus-visible { outline: 2px solid var(--a); outline-offset: 2px; }
</style>
<button id="ot-theme" type="button"></button>
<script>
(function () {
  const PAL = __PALETTES__;
  const SLUGS = __SLUGS__;
  const P = window.parent;
  const btn = document.getElementById("ot-theme");
  const path = P.location.pathname;
  let base = path;
  for (const s of SLUGS) {
    if (s && (path.endsWith("/" + s) || path.endsWith("/" + s + "/"))) {
      base = path.slice(0, path.lastIndexOf("/" + s));
      break;
    }
  }
  if (!base.endsWith("/")) base += "/";
  // Streamlit stores the visitor's theme choice per page path under this key.
  const key = (p) => "stActiveTheme-" + p + "-v2";
  let current = null;
  try { current = JSON.parse(P.localStorage.getItem(key(path))); } catch (e) {}
  if (current !== "Light" && current !== "Dark") {
    current = P.matchMedia("(prefers-color-scheme: dark)").matches ? "Dark" : "Light";
  }
  const next = current === "Dark" ? "Light" : "Dark";
  const pal = PAL[current.toLowerCase()];
  btn.style.setProperty("--b", pal.border);
  btn.style.setProperty("--p", pal.panel);
  btn.style.setProperty("--t", pal.text);
  btn.style.setProperty("--a", pal.teal);
  btn.textContent = current === "Dark" ? "\\u263E  Dark" : "\\u2600  Light";
  btn.title = "Switch to " + next.toLowerCase() + " mode";
  btn.setAttribute("aria-label", btn.title);
  btn.addEventListener("click", function () {
    const paths = new Set([path]);
    for (const s of SLUGS) {
      const p = base + s;
      paths.add(p);
      paths.add(p.length > 1 && p.endsWith("/") ? p.slice(0, -1) : p + "/");
    }
    try { paths.forEach((p) => P.localStorage.setItem(key(p), JSON.stringify(next))); } catch (e) {}
    P.location.reload();
  });
})();
</script>
"""


def theme_toggle() -> None:
    palettes = {
        name: {k: t[k] for k in ("border", "panel", "text", "teal")} for name, t in TOKENS.items()
    }
    markup = _TOGGLE_HTML.replace("__PALETTES__", json.dumps(palettes)).replace(
        "__SLUGS__", json.dumps(PAGE_SLUGS)
    )
    st.iframe(markup, height=38, width=104)  # same-origin, so the script can reach the page


# ---------------------------------------------------------------------------
# Page chrome
# ---------------------------------------------------------------------------

def header() -> None:
    with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center", gap="small"):
        st.link_button("GitHub", REPO, type="tertiary", icon=":material/code:")
        st.link_button("PyPI", PYPI, type="tertiary", icon=":material/package_2:")
        theme_toggle()


def footer() -> None:
    st.markdown(
        f"""<div class="ot-footer">
        <strong>OTTools</strong> · operations research in Python ·
        Built by <a href="https://github.com/PranavMundhra" target="_blank">Pranav Mundhra</a>
        &amp; <a href="https://github.com/Strangehumaan" target="_blank">Saad Nathani</a>
        <br><a href="{REPO}" target="_blank">GitHub</a> ·
        <a href="{PYPI}" target="_blank">PyPI</a> ·
        <a href="{ISSUES}" target="_blank">Report an issue</a> ·
        site runs OTTools {PACKAGE_VERSION}
        </div>""",
        unsafe_allow_html=True,
    )


def eyebrow(text: str) -> None:
    st.markdown(f'<p class="ot-eyebrow">{html.escape(text)}</p>', unsafe_allow_html=True)


def lede(text: str) -> None:
    st.markdown(f'<p class="ot-lede">{text}</p>', unsafe_allow_html=True)


def status_badge(status: str) -> str:
    cls = {"optimal": "ok", "unbounded": "warn"}.get(status, "bad")
    return f'<span class="ot-status {cls}">{html.escape(status.upper())}</span>'


def big_number(label: str, value: str) -> str:
    return f'<div class="ot-big"><small>{html.escape(label)}</small>{html.escape(value)}</div>'


def why(text: str) -> None:
    """An explanation callout. Supports **bold**, `code` and HTML."""
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
    st.markdown(f'<div class="ot-why">{text}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Numbers and tables
# ---------------------------------------------------------------------------

def num(x, digits: int = 4) -> str:
    """Compact number: 36 → '36', 12.66666 → '12.6667', -0.0 → '0'."""
    if x is None:
        return "–"
    x = float(x)
    if abs(x - round(x)) < 1e-7:
        return str(int(round(x)))
    return f"{x:.{digits}f}".rstrip("0").rstrip(".")


def table(header: list[str], rows: list[list], header_classes: list[str] | None = None) -> str:
    """Build an HTML table. Each body cell is a str, or a (html, css_class) tuple.

    The first cell of every row is rendered as a row header.
    """
    header_classes = header_classes or [""] * len(header)
    head = "".join(
        f'<th class="{c}">{h}</th>' for h, c in zip(header, header_classes)
    )
    body = []
    for row in rows:
        cells = []
        for k, cell in enumerate(row):
            content, cls = cell if isinstance(cell, tuple) else (cell, "")
            if k == 0:
                cells.append(f'<th class="rowh {cls}">{content}</th>')
            else:
                cells.append(f'<td class="{cls}">{content}</td>')
        body.append("<tr>" + "".join(cells) + "</tr>")
    return (
        '<div class="ot-table-wrap"><table class="ot-table"><thead><tr>'
        + head + "</tr></thead><tbody>" + "".join(body) + "</tbody></table></div>"
    )


def show_html(markup: str) -> None:
    st.markdown(markup, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Plotly
# ---------------------------------------------------------------------------

def style_fig(fig, height: int = 440):
    t = tokens()
    axis = dict(gridcolor=t["grid"], zerolinecolor=t["border"], linecolor=t["border"],
                tickfont=dict(family=MONO, size=12))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="'IBM Plex Sans', sans-serif", color=t["text"], size=13),
        colorway=t["lines"], height=height, title=None,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="top", y=-0.12, x=0),
        hoverlabel=dict(font=dict(family=MONO)),
    )
    fig.update_xaxes(**axis)
    fig.update_yaxes(**axis)
    scene_axis = dict(backgroundcolor="rgba(0,0,0,0)", gridcolor=t["grid"], color=t["text"])
    fig.update_scenes(xaxis=scene_axis, yaxis=scene_axis, zaxis=scene_axis)
    return fig


def plot(fig, height: int = 440, key: str | None = None) -> None:
    st.plotly_chart(style_fig(fig, height), theme=None, key=key,
                    config={"displaylogo": False, "responsive": True})
