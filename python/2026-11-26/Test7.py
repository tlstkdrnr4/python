import streamlit as st
st.title("1부터 n 까지 합계 구하기")
@st.cache_data(ttl=30)
def sum_num(limit):
    return sum(n +n for n in range(limit + 1))

limit = st.number_input("끝 숫자" , min_value= 1 , max_value= 10000 , value= 1)
with st.spinner("계산 중"):
    result = sum_num(int(limit))
st.metric("1 ~ n 까지의 합" , result)
if st.button("함수 캐시 지우기"):
    sum_num.clear()
    st.success("캐시를 지웠습니다.")