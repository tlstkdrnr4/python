
import streamlit as st
import chromadb
import requests
import hashlib
import io

from pypdf import PdfReader
from openai import OpenAI


# 1. 웹사이트 설정
st.set_page_config(
    page_title="AI 통합 문서 검색",
    page_icon="📚",
    layout="wide"
)

st.title("📚 AI 통합 문서 검색 시스템")
st.caption("Ollama + Qwen + ChromaDB + Multi PDF RAG")


# 2. Ollama 연결
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


# 3. 벡터 DB 연결
@st.cache_resource
def get_db():
    return chromadb.PersistentClient(
        path="./multi_chroma_db"
    )

db = get_db()

collection = db.get_or_create_collection(
    name="multi_documents"
)


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


# 6. 대화 기록 생성
if "messages" not in st.session_state:
    st.session_state.messages = []

if "file_keys" not in st.session_state:
    st.session_state.file_keys = []


# 7. 사이드바 설정
st.sidebar.header("📂 문서 관리")

uploaded_files = st.sidebar.file_uploader(
    "PDF 파일을 선택하세요.",
    type=["pdf"],
    accept_multiple_files=True
)

top_k = st.sidebar.slider(
    "검색할 문서 조각 수",
    min_value=1,
    max_value=5,
    value=3
)


# 8. 업로드한 파일 정보 생성
files = []

for uploaded_file in uploaded_files:

    pdf_bytes = uploaded_file.getvalue()

    file_hash = hashlib.sha256(
        pdf_bytes
    ).hexdigest()

    file_key = hashlib.sha256(
        (uploaded_file.name + file_hash).encode("utf-8")
    ).hexdigest()

    files.append({
        "name": uploaded_file.name,
        "bytes": pdf_bytes,
        "file_key": file_key
    })


file_keys = sorted([
    file["file_key"] for file in files
])

# 업로드한 문서가 변경되면 대화 초기화
if st.session_state.file_keys != file_keys:

    st.session_state.file_keys = file_keys
    st.session_state.messages = []


# 9. 문서 분석 및 벡터 DB 저장
if st.sidebar.button("전체 문서 분석 시작"):

    if not files:

        st.sidebar.warning("PDF를 먼저 업로드하세요.")

    else:

        progress = st.progress(0)

        for i, file in enumerate(files):

            file_name = file["name"]
            file_key = file["file_key"]

            try:

                # 문서 분석 완료 여부 확인
                existing = collection.get(
                    where={"file_key": file_key},
                    include=["metadatas"]
                )

                if any(
                    m.get("complete") == True
                    for m in existing["metadatas"]
                ):

                    st.success(f"{file_name}: 기존 문서 재사용")

                else:

                    # 이전에 중단된 데이터 삭제
                    if existing["ids"]:

                        collection.delete(
                            ids=existing["ids"]
                        )

                    reader = PdfReader(
                        io.BytesIO(file["bytes"])
                    )

                    documents = []

                    for page_num, page in enumerate(
                        reader.pages, start=1
                    ):

                        text = page.extract_text() or ""

                        chunks = split_text(text)

                        for chunk in chunks:

                            documents.append({
                                "page": page_num,
                                "content": chunk
                            })

                    if not documents:

                        st.warning(
                            f"{file_name}: 텍스트 추출 실패"
                        )

                        continue

                    status = st.empty()

                    for number, document in enumerate(documents):

                        embedding = get_embedding(
                            document["content"]
                        )

                        collection.add(
                            ids=[
                                f"{file_key}_{number}"
                            ],

                            documents=[
                                document["content"]
                            ],

                            embeddings=[
                                embedding
                            ],

                            metadatas=[{
                                "file_name": file_name,
                                "file_key": file_key,
                                "page": document["page"],
                                "complete": (
                                    number == len(documents) - 1
                                )
                            }]
                        )

                        status.write(
                            f"{file_name} 분석 중: "
                            f"{number + 1}/{len(documents)}"
                        )

                    status.success(
                        f"{file_name}: 분석 완료!"
                    )

            except Exception as e:

                st.error(
                    f"{file_name} 분석 오류: {e}"
                )

            finally:

                progress.progress(
                    (i + 1) / len(files)
                )


# 10. 분석된 문서 확인
ready_files = []

for file in files:

    existing = collection.get(
        where={"file_key": file["file_key"]},
        include=["metadatas"]
    )

    if any(
        m.get("complete") == True
        for m in existing["metadatas"]
    ):

        ready_files.append(file["file_key"])

        st.sidebar.success(
            f"{file['name']} : 검색 가능"
        )

    else:

        st.sidebar.warning(
            f"{file['name']} : 분석 필요"
        )


st.sidebar.metric(
    "검색 가능한 PDF",
    len(ready_files)
)

st.sidebar.metric(
    "DB 전체 문서 조각",
    collection.count()
)


# 11. 대화 초기화
if st.sidebar.button("대화 초기화"):

    st.session_state.messages = []
    st.rerun()


# 12. 이전 대화 출력
for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# 13. 사용자 질문 입력
question = st.chat_input(
    "업로드한 PDF에 대해 질문하세요."
)

if question:

    if not ready_files:

        st.warning(
            "먼저 PDF를 업로드하고 분석해 주세요."
        )

    else:

        with st.chat_message("user"):

            st.markdown(question)

        try:

            # 14. 질문 임베딩
            question_embedding = get_embedding(question)

            # 15. 현재 업로드한 문서만 통합 검색
            selected = collection.get(
                where={
                    "file_key": {"$in": ready_files}
                },
                include=[]
            )

            results = collection.query(
                query_embeddings=[
                    question_embedding
                ],

                n_results=min(
                    top_k,
                    len(selected["ids"])
                ),

                where={
                    "file_key": {"$in": ready_files}
                }
            )

            context = ""
            sources = []

            # 16. 검색 결과 및 출처 확인
            with st.expander("🔎 AI가 검색한 문서 확인"):

                for document, metadata in zip(
                    results["documents"][0],
                    results["metadatas"][0]
                ):

                    file_name = metadata["file_name"]
                    page = metadata["page"]

                    context += (
                        f"[파일명: {file_name}]\n"
                        f"[페이지: {page}]\n"
                        f"{document}\n\n"
                    )

                    sources.append(
                        f"{file_name} - {page}페이지"
                    )

                    st.markdown(
                        f"**{file_name} / {page}페이지**"
                    )

                    st.write(document)
                    st.divider()


            # 17. AI 답변 생성
            with st.chat_message("assistant"):

                answer_box = st.empty()
                answer = ""

                response = client.chat.completions.create(

                    model="qwen2.5:1.5b",

                    messages=[
                        {
                            "role": "system",
                            "content": """
너는 한국어 전문 문서 분석 AI야.

1. 반드시 자연스러운 한국어로 답변해.
2. 제공된 문서를 근거로 답변해.
3. 문서에 없는 내용은 추측하지 마.
4. 답변의 근거 파일명과 페이지를 표시해.
5. 여러 문서의 내용이 다르면 구분해서 설명해.
                            """
                        }
                    ] + st.session_state.messages[-6:] + [
                        {
                            "role": "user",
                            "content": f"""
참고 문서:
{context}

사용자 질문:
{question}
                            """
                        }
                    ],

                    temperature=0.2,
                    stream=True
                )

                # 실시간 답변 출력
                for chunk in response:

                    if chunk.choices:

                        content = (
                            chunk.choices[0].delta.content or ""
                        )

                        answer += content

                        answer_box.markdown(
                            answer + "▌"
                        )

                answer_box.markdown(answer)

                # 실제 검색된 출처 출력
                st.markdown("#### 📎 검색된 참고 문서")

                for source in dict.fromkeys(sources):

                    st.write(source)


            # 18. 대화 기록 저장
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
