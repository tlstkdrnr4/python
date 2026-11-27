import streamlit as st
st.title("단가 수량 계산기")
price = int(st.number_input("단가" , min_value= 0 , value = 0))
number = int(st.number_input("수량" , min_value = 0 , value = 0))
total = price * number
total1 = price + number
total2 = price - number
if st.button("계산"):
    st.metric("총액" ,  f"{total}원 입니다")
    st.metric("총액" ,  f"{total1}원 입니다")
    st.metric("총액" ,  f"{total2}원 입니다")
