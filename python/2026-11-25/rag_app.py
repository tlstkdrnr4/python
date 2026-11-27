
import streamlit as st
import chromadb
import requests
import hashlib
import io

from pypdf import PdfReader
from openai import OpenAI


# 1. 웹사이트 설정
st.set_page_config(
    page_title="나만의 RAG 챗봇",
    page_icon="📚",
    layout="wide"
)

st.title("📚 나만의 RAG 챗봇")
st.caption("Ollama + Qwen + ChromaDB")


# 2. Ollama 연결
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


# 3. 벡터 DB 영구 저장
@st.cache_resource
def get_db():
    return chromadb.PersistentClient(
        path="./chroma_db"
    )

db = get_db()


# 4. 임베딩 함수
def get_embedding(text):

    response = requests.post(
        "http://localhost:11434/api/embed",
        json={
            "model": "nomic-embed-text",
            "input": text
        },
        timeout=300
    )

    response.raise_for_status()

    return response.json()["embeddings"][0]


# 5. 문서 분할 함수
def split_text(text, chunk_size=500, overlap=100):

    chunks = []
    start = 0

    while start < len(text):

        chunk = text[start:start + chunk_size]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# 6. 대화 기록 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

if "file_hash" not in st.session_state:
    st.session_state.file_hash = None


# 7. PDF 업로드
st.sidebar.header("📂 문서 관리")

uploaded_file = st.sidebar.file_uploader(
    "PDF 파일을 선택하세요.",
    type=["pdf"]
)

collection = None
indexed = False


# 8. PDF 문서 확인
if uploaded_file is not None:

    pdf_bytes = uploaded_file.getvalue()

    file_hash = hashlib.sha256(
        pdf_bytes
    ).hexdigest()

    collection_name = "pdf_" + file_hash[:32]

    if st.session_state.file_hash != file_hash:

        st.session_state.file_hash = file_hash
        st.session_state.messages = []

    collection = db.get_or_create_collection(
        name=collection_name
    )

    st.sidebar.write(uploaded_file.name)

    # 기존 문서 분석 완료 여부 확인
    metadata = collection.metadata or {}

    indexed = (
        metadata.get("complete") == True
        and collection.count() > 0
    )

    if indexed:

        st.sidebar.success("기존 저장 문서 불러오기 완료")

        st.sidebar.write(
            f"저장된 문서 조각: {collection.count()}개"
        )

    else:

        # 9. 처음 업로드한 문서 분석
        if st.sidebar.button("문서 분석 시작"):

            try:

                # 이전에 중단된 분석 데이터 초기화
                db.delete_collection(collection_name)

                collection = db.create_collection(
                    name=collection_name,
                    metadata={"complete": False}
                )

                reader = PdfReader(
                    io.BytesIO(pdf_bytes)
                )

                documents = []

                for i, page in enumerate(reader.pages):

                    text = page.extract_text() or ""

                    chunks = split_text(text)

                    for chunk in chunks:

                        documents.append({
                            "page": i + 1,
                            "content": chunk
                        })

                progress = st.progress(0)
                status = st.empty()

                for number, document in enumerate(documents):

                    embedding = get_embedding(
                        document["content"]
                    )

                    collection.add(
                        ids=[str(number)],
                        documents=[document["content"]],
                        embeddings=[embedding],
                        metadatas=[
                            {"page": document["page"]}
                        ]
                    )

                    progress.progress(
                        (number + 1) / len(documents)
                    )

                    status.write(
                        f"문서 저장 중: "
                        f"{number + 1}/{len(documents)}"
                    )

                if documents:

                    collection.modify(
                        metadata={"complete": True}
                    )

                    indexed = True

                    st.sidebar.success("문서 분석 완료!")

                else:

                    st.warning("추출된 텍스트가 없습니다.")

            except Exception as e:

                st.error(f"문서 분석 오류: {e}")

else:

    if st.session_state.file_hash is not None:

        st.session_state.file_hash = None
        st.session_state.messages = []


# 10. 대화 초기화
if st.sidebar.button("대화 초기화"):

    st.session_state.messages = []
    st.rerun()


# 11. 이전 대화 출력
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# 12. 질문 입력
question = st.chat_input(
    "PDF 문서에 대해 질문하세요."
)

if question:

    if not indexed:

        st.warning(
            "PDF를 업로드하고 문서 분석을 먼저 진행하세요."
        )

    else:

        with st.chat_message("user"):

            st.markdown(question)

        try:

            # 13. 질문 임베딩
            question_embedding = get_embedding(question)

            # 14. 관련 문서 검색
            results = collection.query(
                query_embeddings=[question_embedding],
                n_results=min(3, collection.count())
            )

            context = ""

            # 15. 검색 결과 확인
            with st.expander("🔎 검색된 문서 확인"):

                for document, metadata in zip(
                    results["documents"][0],
                    results["metadatas"][0]
                ):

                    page = metadata["page"]

                    context += f"[페이지 {page}]\n"
                    context += document + "\n\n"

                    st.markdown(f"**페이지 {page}**")
                    st.write(document)
                    st.divider()

            # 16. AI 답변 생성
            with st.chat_message("assistant"):

                answer_box = st.empty()
                answer = ""

                response = client.chat.completions.create(

                    model="qwen2.5:1.5b",

                    messages=[
                        {
                            "role": "system",
                            "content": """
                            너는 한국어 문서 분석 AI야.
                            반드시 자연스러운 한국어로 답변해.
                            제공된 문서를 근거로 답변해.
                            문서에 없는 내용은 추측하지 마.
                            답변의 근거 페이지를 알려줘.
                            """
                        }
                    ] + st.session_state.messages[-6:] + [
                        {
                            "role": "user",
                            "content": f"""
                            참고 문서:
                            {context}

                            질문:
                            {question}
                            """
                        }
                    ],

                    temperature=0.2,
                    stream=True
                )

                # 17. 실시간 답변 출력
                for chunk in response:

                    if chunk.choices:

                        content = (
                            chunk.choices[0].delta.content or ""
                        )

                        answer += content

                        answer_box.markdown(answer + "▌")

                answer_box.markdown(answer)

            # 18. 대화 저장
            st.session_state.messages.append({
                "role": "user",
                "content": question
            })

            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:

            st.error(f"AI 처리 오류: {e}")
