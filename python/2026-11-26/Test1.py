import streamlit as st

st.set_page_config(page_title="상품설명" , layout="wide")
st.title("상품 소개 화면")
st.sidebar.header("상품설명")
st.sidebar.write("아이폰")
st.markdown("오늘만 특가")

left , right , left1 , right1= st.columns(4)

with left :
    st.header("아이폰 맥스")
    st.write("150만원")

with right :
    st.header("아이맥")
    st.write("350만원")

with left1 :
    st.header("아이폰 미니")
    st.write("70만원")

with right1 :
    st.header("아이폰 15")
    st.write("130만원")