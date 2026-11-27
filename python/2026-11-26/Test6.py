import streamlit as st
st.title("참가 인원 신청")
with st.form("email_form"):
    email = st.text_input("이메일")
    people = st.number_input("인원" , min_value = 1 , max_value=10)
    done = st.form_submit_button("미리보기")

if done :
    if "@" not in email:
        st.error("이메일을 확인하세요")
    else:
        st.write(email , int(people))

