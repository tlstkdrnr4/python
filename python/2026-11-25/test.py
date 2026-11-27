
import streamlit as st
from openai import OpenAI
from pypdf import PdfReader
import chromadb
import requests
import hashlib
import io

# ==================================
# 1. 기본 설정
# ==================================

st.set_page_config(
    page_title="AI RAG 챗봇",
    page_icon="📚"
)

st.title("📚 나만의 AI RAG 챗봇")
st.caption("PDF 문서 검색 + Ollama + Qwen")

OLLAMA_URL = "http://localhost:11434"
CHAT_MODEL = "qwen2.5:1.5b"
EMBED_MODEL = "nomic-embed-text"

# ==================================
# 2. AI 연결
# ==================================

client = OpenAI(
    base_url=f"{OLLAMA_URL}/v1",
    api_key="ollama"
)

# ==================================
# 3. 벡터 데이터베이스 연결
# ==================================

@st.cache_resource
def get_db():
    return chromadb.PersistentClient(
        path="./chroma_db"
    )

db = get_db()

# ==================================
# 4. 임베딩 함수
# ==================================

def get_embeddings(texts):

    # 최신 Ollama API 사용
    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={
            "model": EMBED_MODEL,
            "input": texts
        },
        timeout=300
    )

    # 구버전 API 호환
    if response.status_code in (404, 405):

        embeddings = []

        for text in texts:

            old_response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={
                    "model": EMBED_MODEL,
                    "prompt": text
                },
                timeout=300
            )

            old_response.raise_for_status()

            embeddings.append(
                old_response.json()["embedding"]
            )

        return embeddings

    response.raise_for_status()

    return response.json()["embeddings"]


# ==================================
# 5. 문서 분할 함수
# ==================================

def split_text(text, chunk_size=900, overlap=150):

    chunks = []

    start = 0

    while start < len(text):

        chunk = text[start:start + chunk_size]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# ==================================
# 6. 세션 상태 생성
# ==================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "file_hash" not in st.session_state:
    st.session_state.file_hash = None

if "collection_name" not in st.session_state:
    st.session_state.collection_name = None

if "indexed" not in st.session_state:
    st.session_state.indexed = False


# ==================================
# 7. PDF 업로드
# ==================================

st.sidebar.header("📂 PDF 문서")

uploaded_file = st.sidebar.file_uploader(
    "PDF 파일을 업로드하세요.",
    type=["pdf"]
)

if uploaded_file is not None:

    pdf_bytes = uploaded_file.getvalue()

    current_hash = hashlib.sha256(
        pdf_bytes
    ).hexdigest()

    if current_hash != st.session_state.file_hash:

        st.session_state.file_hash = current_hash
        st.session_state.collection_name = None
        st.session_state.indexed = False
        st.session_state.messages = []

    st.sidebar.write(uploaded_file.name)

    # ==================================
    # 8. 문서 분석 및 저장
    # ==================================

    if st.sidebar.button("문서 분석 시작"):

        try:

            reader = PdfReader(
                io.BytesIO(pdf_bytes)
            )

            chunks = []
            metadatas = []

            # 페이지별 텍스트 추출
            for page_num, page in enumerate(
                reader.pages, start=1
            ):

                page_text = page.extract_text() or ""

                page_chunks = split_text(page_text)

                for chunk in page_chunks:

                    chunks.append(chunk)

                    metadatas.append({
                        "page": page_num
                    })

            if not chunks:

                st.sidebar.error(
                    "PDF에서 텍스트를 추출하지 못했습니다."
                )

            else:

                collection_name = (
                    "pdf_" + current_hash[:16]
                )

                # 기존 동일 문서 데이터 삭제
                try:
                    db.delete_collection(
                        collection_name
                    )
                except Exception:
                    pass

                collection = db.create_collection(
                    name=collection_name,
                    metadata={"hnsw:space": "cosine"}
                )

                progress = st.progress(0)

                status = st.empty()

                batch_size = 16

                # 문서를 임베딩하여 저장
                for start in range(
                    0, len(chunks), batch_size
                ):

                    batch = chunks[
                        start:start + batch_size
                    ]

                    embeddings = get_embeddings(batch)

                    batch_metadata = metadatas[
                        start:start + batch_size
                    ]

                    ids = [
                        f"chunk_{i}"
                        for i in range(
                            start, start + len(batch)
                        )
                    ]

                    collection.add(
                        ids=ids,
                        documents=batch,
                        embeddings=embeddings,
                        metadatas=batch_metadata
                    )

                    progress.progress(
                        min(
                            (start + len(batch)) / len(chunks),
                            1.0
                        )
                    )

                    status.write(
                        f"문서 분석 중: "
                        f"{min(start + len(batch), len(chunks))}"
                        f"/{len(chunks)}"
                    )

                st.session_state.collection_name = (
                    collection_name
                )

                st.session_state.indexed = True

                st.session_state.messages = []

                st.sidebar.success(
                    f"분석 완료! 총 {len(chunks)}개 문서 조각"
                )

        except Exception as e:

            st.sidebar.error(
                f"문서 분석 오류: {e}"
            )


# ==================================
# 9. 문서 검색 함수
# ==================================

def search_documents(question, collection):

    question_embedding = get_embeddings(
        [question]
    )[0]

    result = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(4, collection.count())
    )

    documents = result["documents"][0]
    metadatas = result["metadatas"][0]

    context = ""

    for document, metadata in zip(
        documents, metadatas
    ):

        context += (
            f"\n[페이지 {metadata['page']}]\n"
            f"{document}\n"
        )

    return context, documents, metadatas


# ==================================
# 10. 이전 대화 출력
# ==================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# ==================================
# 11. 대화 초기화
# ==================================

if st.sidebar.button("대화 초기화"):

    st.session_state.messages = []

    st.rerun()


# ==================================
# 12. 사용자 질문 입력
# ==================================

question = st.chat_input(
    "PDF 문서에 대해 질문하세요."
)

if question:

    if not st.session_state.indexed:

        st.warning(
            "먼저 PDF를 업로드하고 문서 분석을 실행하세요."
        )

    else:

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):

            st.markdown(question)

        try:

            collection = db.get_collection(
                st.session_state.collection_name
            )

            # 관련 문서 검색
            context, documents, metadatas = (
                search_documents(
                    question, collection
                )
            )

            # 검색 결과 확인
            with st.expander("🔎 AI가 검색한 문서 확인"):

                for document, metadata in zip(
                    documents, metadatas
                ):

                    st.markdown(
                        f"**페이지 {metadata['page']}**"
                    )

                    st.write(document)

            # AI 시스템 프롬프트
            system_prompt = f"""
너는 한국어 전문 PDF 문서 분석 AI야.

다음 규칙을 반드시 지켜.

1. 모든 답변은 자연스러운 한국어로 작성해.
2. 중국어와 일본어를 사용하지 마.
3. 한자 대신 가능한 한글로 설명해.
4. 검색된 문서 내용을 근거로 답변해.
5. 문서에 없는 내용은 추측하지 마.
6. 답변에 근거가 된 페이지 번호를 표시해.

[검색된 PDF 내용]
{context}
"""

            # AI 답변 생성
            with st.chat_message("assistant"):

                answer_box = st.empty()

                answer = ""

                response = client.chat.completions.create(
                    model=CHAT_MODEL,

                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt
                        }
                    ] + st.session_state.messages,

                    temperature=0.2,
                    stream=True
                )

                # 실시간 답변 출력
                for chunk in response:

                    content = (
                        chunk.choices[0].delta.content or ""
                    )

                    answer += content

                    answer_box.markdown(
                        answer + "▌"
                    )

                answer_box.markdown(answer)

            # AI 답변 저장
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as e:

            st.error(f"AI 처리 오류: {e}")

            st.session_state.messages.pop()
