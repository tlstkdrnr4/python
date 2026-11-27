import streamlit as st
st.title("세션 카운터")
if "count" not in st.session_state:
    st.session_state.count = 0
if st.button("증가"):
    st.session_state.count += 10
if st.button("초기화"):
    st.session_state.count = 0
st.metric("현재값" , st.session_state.count)