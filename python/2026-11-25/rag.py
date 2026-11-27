
import chromadb
import requests
from pypdf import PdfReader
from openai import OpenAI


# 1. Ollama 연결
client = OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="ollama"
)


# 2. 임베딩 함수
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


# 3. 문서 분할 함수
def split_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start:start + chunk_size]

        if chunk.strip():
            chunks.append(chunk)

        start += chunk_size - overlap

    return chunks


# 4. ChromaDB 생성
db = chromadb.PersistentClient(path="./chroma_db")

collection = db.get_or_create_collection(
    name="pdf_documents"
)


# 5. PDF 읽기
reader = PdfReader("test.pdf")

number = 0

for i, page in enumerate(reader.pages):

    text = page.extract_text() or ""

    chunks = split_text(text)

    for chunk in chunks:

        embedding = get_embedding(chunk)

        collection.add(
            ids=[str(number)],
            documents=[chunk],
            embeddings=[embedding],
            metadatas=[{"page": i + 1}]
        )

        number += 1

        print(f"문서 {number}개 저장 완료")


print("PDF 문서 분석 완료")


# 6. 사용자 질문
while True:

    question = input("질문 : ")

    if question == "종료":
        break

    if collection.count() == 0:
        print("저장된 문서가 없습니다.")
        break

    question_embedding = get_embedding(question)

    # 7. 관련 문서 검색
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(3, collection.count())
    )

    # 8. 검색된 문서 저장
    context = ""

    for document, metadata in zip(
        results["documents"][0],
        results["metadatas"][0]
    ):
        context += f"[페이지 {metadata['page']}]\n"
        context += document + "\n"

    # 9. AI에게 질문과 문서 전달
    response = client.chat.completions.create(
        model="qwen2.5:1.5b",

        messages=[
            {
                "role": "system",
                "content": """
                너는 한국어 PDF 문서 분석 AI야.
                제공된 문서를 근거로 답변해.
                문서에 없는 내용은 추측하지 마.
                가능하면 페이지 번호도 알려줘.
                반드시 한국어로 답변해.
                """
            },
            {
                "role": "user",
                "content": f"참고 문서:\n{context}\n\n질문: {question}"
            }
        ],

        temperature=0.2,
        stream=True
    )

    # 10. AI 답변 출력
    print("AI : ", end="")

    for chunk in response:
        content = chunk.choices[0].delta.content or ""
        print(content, end="", flush=True)

    print()
