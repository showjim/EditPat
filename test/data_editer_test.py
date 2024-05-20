import streamlit as st
import pandas as pd


df = pd.DataFrame([
    {"name": "Alice", "edited": False},
    {"name": "Bob", "edited": False},
    {"name": "Cecil", "edited": False},
])


def df_on_change(df):
    state = st.session_state["df_editor"]
    for index, updates in state["edited_rows"].items():
        st.session_state["df"].loc[st.session_state["df"].index == index, "edited"] = True
        for key, value in updates.items():
            st.session_state["df"].loc[st.session_state["df"].index == index, key] = value


def editor():
    if "df" not in st.session_state:
        st.session_state["df"] = df
    st.data_editor(st.session_state["df"], key="df_editor", on_change=df_on_change, args=[df])


editor()