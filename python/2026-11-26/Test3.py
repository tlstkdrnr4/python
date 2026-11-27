import pandas as pd
import streamlit as st

st.title("세 과목의 점수")
rows = [
    {"Subject" : "math" , "score" : 100},
    {"Subject" : "English" , "score" : 90},
    {"Subject" : "Korean Language" , "score" : 80}
] 

df = pd.DataFrame(rows)
st.dataframe(df , hide_index=True)
st.bar_chart(df.set_index("Subject")["score"])
st.metric("총평균" , f"{(df['score'].mean())}")