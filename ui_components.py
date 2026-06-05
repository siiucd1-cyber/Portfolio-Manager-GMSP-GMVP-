"""Small Streamlit UI helpers."""

import streamlit as st


def render_dark_table(df):
    return st.markdown(
        df.to_html(
            index=False,
            escape=False,
            classes="dark-table",
        ),
        unsafe_allow_html=True,
    )
