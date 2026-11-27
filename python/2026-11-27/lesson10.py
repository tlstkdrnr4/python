from pathlib import Path
import streamlit as st
from common import parse_sales, summarize

st.set_page_config(page_title="매출 대시보드" , layout="wide")
st.title("업로드 매출 대시보드")
uploaded = st.file_uploader("UTF-8 CSV" , type=["csv"])
sample = Path(__file__).resolve().parent[1] / "data" / "sales.csv"
raw = uploaded.getvalue() if uploaded else sample.read_bytes()
try:
    rows = parse_sales(raw)
except ValueError as exc:
    st.error(str(exc))
    st.stop
choices = ["전체"] + sorted({row["product"] for row in rows})
selected = st.selectbox("상품" , choices)
filtered = rows if selected == "전체" else [row for row in rows if row["product"] == selected]

summary = summarize(filtered)
st.metric("총매출" , f"{summary['revenue']:,}원")
st.metric("수량" , summary["quantity"])
st.dataframe(filtered)
if filtered:
    st.bar_chart(summary["by_product"])
else : 
    st.info("표시할 데이터가 없습니다")

def summarize(rows):
    by_product = {}
    for row in rows:
        name = row['product']
        by_product[name] = by_product.get(name , 0) + row['quantity'] * row['price']
    return {'revenue' : sum(by_product.values()),
            'quantity' : sum(row['quantity'] for row in rows),
            'by_product' : by_product}