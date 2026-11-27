import streamlit as st
st.title("점수 계산기")
if "number" not in st.session_state:
    st.session_state.number = 0
if st.button("증가"):
    st.session_state.number += 10
if st.button("감소"):
    st.session_state.number -= 5
st.metric("현재값" , st.session_state.number)