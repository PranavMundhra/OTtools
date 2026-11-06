"""OTTools showcase site: entry point.

Run with:  streamlit run app.py
"""
import streamlit as st

import ui

st.set_page_config(page_title="OTTools", page_icon="logo.png", layout="wide")
st.logo("logo.png", size="large")

pages = [
    st.Page("views/home.py", title="Home", icon=":material/home:", default=True),
    st.Page("views/lp.py", title="Linear Programming", icon=":material/show_chart:", url_path="linear-programming"),
    st.Page("views/transport.py", title="Transportation", icon=":material/local_shipping:", url_path="transportation"),
    st.Page("views/learn.py", title="Learn", icon=":material/school:", url_path="learn"),
]
page = st.navigation(pages, position="top")

ui.inject_css()
ui.header()
page.run()
ui.footer()
