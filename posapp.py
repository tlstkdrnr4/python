import streamlit as st
import pandas as pd
from common import parse_sales , summarize
from pathlib import Path
import csv
import io

st.set_page_config(page_title = "미니 POS & 매출 대시보드" , layout="wide")
st.header("🏪올인원 미니 POS & 매출 분석기")
st.write("**학습 목표**: 입력(`form`), 상태 유지(`session_state`), 캐싱(`cache_data`), 데이터 시각화를 하나로 통합합니다.")

if "pos_orders" not in st.session_state : 
    st.session_state.pos_orders = []
if "messages:" not in st.session_state : 
    st.session_state.messages = [{"role": "assistant" , "content" : "안녕하세요! '총매출 , '인기상품' , '주문건수' 등을 물어보세요."}]
@st.cache_data(ttl= 60)
def get_cached_summary(rows):
    return summarize(rows)

st.sidebar.header("⚙️데이터 관리")
uploaded = st.sidebar.file_uploader("추가 매출 CSV 업로드 (UTF-8)" , type=['csv'])
if st.button("요약캐시 초기화") :
    get_cached_summary.clear()
    st.sidebar.success("캐시를 초기화했습니다")

if st.button("POS 입력 내역 초기화") :
    st.session_state.pos_orders = []
    st.sidebar.warning("현장 주문 내역이 초기화되었습니다")

if uploaded is not None :
    try :
        base_rows = parse_sales(uploaded.getvalue())
        st.sidebar.success(f"CSV 에서 {len(base_rows)}행을 불러왔습니다.")
    except Exception as e :
        st.sidebar.error(str(e))
else :
    sample = Path(__file__).resolve().parent / "data" / "sales.csv"
    base_rows = parse_sales(sample.read_bytes())
    temp = [{"product": "book", "quantity": 2, "price": 12000}, {"product": "pen", "quantity": 5, "price": 1500}]
    base_rows.extend(temp)

all_rows = base_rows + st.session_state.pos_orders
st.write(f"총 {len(all_rows)}건의 매출 데이터가 있습니다.")

tab1, tab2 , tab3 = st.tabs(["📊 매출 대시보드", "💳 POS 주문 입력", "💬 매출 도우미 챗봇"])

with tab1 :
    selected = st.selectbox("상품 선택" , ["전체"] + sorted({row["product"] for row in all_rows}))
    filetered = all_rows if selected == "전체" else [row for row in all_rows if row["product"] == selected]
    summary = get_cached_summary(filetered)  
    col1, col2, col3 = st.columns(3)
    col1.metric("총매출", f"{summary['revenue']:,}원")
    col2.metric("총 판매 수량", f"{summary['quantity']:,}개")
    col3.metric("거래 건수", f"{len(filetered)}건")
    left , right = st.columns([1.2, 1])
    with left :
        st.subheader("상세 거래내역")
        if filetered :
            df = pd.DataFrame(filetered)
            df["subtotal"] = df["quantity"] * df["price"]
            st.dataframe(df , use_container_width=True , hide_index=True)
        else :
            st.info("표시할 데이터가 없습니다")
    with right :
        st.subheader("상품별 매출 비중")
        if summary["by_product"] :
            st.bar_chart(summary["by_product"])

with tab2 :
    st.subheader("신규 현장 주문 등록")
    with st.form("pos_form" , clear_on_submit=True) : 
        p_name = st.text_input("상품명 (1~40자)")
        c1 , c2 = st.columns(2)
        p_qty = c1.number_input("수량" , min_value=1 , max_value=1000 , value=1) 
        p_price = c2.number_input("단가 (원)" , min_value=100 , max_value=1_000_000 , value=5000, step=5000)
        submitted = st.form_submit_button("주문 추가")
        clean_name = p_name.strip()
    if submitted:
        if not clean_name or len(clean_name) > 40 :
            st.error("상품명은 공백 제외 1~40글자로 입력하세요")
        else:
            st.session_state.pos_orders.append({"product" : clean_name, "quantity" : int(p_qty) , "price" : int(p_price)})
            st.success(f"{clean_name} {p_qty} 개 (총 {p_qty * p_price :,}원) 주문이 등록되었습니다")


with tab3:
    st.subheader("데이터 기반 간단 Q&A")
    if "messages" not in st.session_state:
        st.session_state.messages = [] 
    if st.button("대화 지우기"):
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    question = st.chat_input("매출에 대해 질문해보세요 (예: 총매출 알려줘, 가장 잘 팔린 상품은?)")

    if question and question.strip():
        answer = f"응답: {question.strip()}"

        for role, content in [("user" , question) , ("assistant" ,answer)]:
            st.session_state.messages.append({"role" : role , "content" : content})
        with st.chat_message(role):
            st.write(content)

    total_summary = get_cached_summary(all_rows)
    if question is not None and question.strip():
        if "총매출" in question or "매출" in question:
            reply = f"현재 누적 총매출은 {total_summary['revenue']:,}원 입니다."
            st.session_state.messages.append({"role" : "assistant" , "content" : reply})
            st.chat_message("assistant").write(reply) 
        elif "인기" in question or "가장" in question or "상품" in question :
            if total_summary["by_product"]:
                best = max(total_summary["by_product"].items(), key = lambda x : x[1])
                reply = f"매출 1위 상품은 **{best[0]}**이며, 총 **{best[1]:,}원**의 매출을 기록했습니다"
                st.session_state.messages.append({"role" : "assistant" , "content" : reply})
                st.chat_message("assistant").write(reply) 
            else:
                reply = "아직 등록된 상품 데이터가 없습니다"
                st.session_state.messages.append({"role" : "assistant" , "content" : reply})
                st.chat_message("assistant").write(reply) 
        elif "수량" in question or "건수" in question:
            reply = f"총 거래 건수는 **{len(all_rows)}건** , 총 판매 수량은 **{total_summary['quantity']:,}개**"
            st.session_state.messages.append({"role" : "assistant" , "content" : reply})
            st.chat_message("assistant").write(reply) 
        else:
            reply = "질문을 이해하지 못했습니다. **총 매출** , **인기 상품** , **판매 수량 ** 키워드를 포함해 질문해주세요"
            st.session_state.messages.append({"role" : "assistant" , "content" : reply})
            st.chat_message("assistant").write(reply) 
    

FIELDS = ['product' , 'quantity' , 'price']

def parse_sales(raw):
    if len(raw) > 100_100:
        raise ValueError("파일을 100KB 이하로 준비하세요") # raise 예외 발생
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text), strict=False)
        if reader.fieldnames != FIELDS:
            raise ValueError("필수 열 순서 : product, quantity, price")
        rows = []
        for number , source in enumerate(reader , 2):
            print(source)
            if len(rows) >= 1000:
                raise ValueError("데이터는 1000행 이하로 준비하세요")
            if set(source) != set(FIELDS) or None in source.values():
                raise ValueError(f"{number}번째 레코드의 열을 확인하세요")
            product = source["product"].strip()
            if not product or len(product) > 40:
                raise ValueError("상품명은 1 ~ 40 글자입니다.")
            numeric = []
            for name in ("quantity" , "price"):
                value = source[name].strip()
                if not value.isascii() or not value.isdecimal():
                    raise ValueError(f"{name}에는 양의 정수를 입력하세요.")
                value = int(value)
                if not 1 <= value <= 1_000_000:
                    raise ValueError(f"{name}은 1 ~ 100000 범위입니다.")
                numeric.append(value)
            rows.append(dict(product = product , quantity = numeric[0] , price = numeric[1]))
        return rows
    except UnicodeDecodeError as exc:
        raise ValueError("UTF-8 CSV를 사용하세요.") from exc
    except csv.Error as exc:
        raise ValueError("CSV 형식을 확인하세요") from exc

def summarize(rows):
    by_product = {}
    for row in rows:
        name = row["product"]
        by_product[name] = by_product.get(name , 0) + row["quantity"] * row["price"]
    return {"revenue" : sum(by_product.values()), "quantity" : sum(row["quantity"] for row in rows),
            "by_product" : by_product}