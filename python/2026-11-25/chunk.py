from pypdf import PdfReader

def split_text(text, chunk_size=500, overlap=100):
    chunks = []
    start = 0

    while start < len(text):
        chunk = text[start:start + chunk_size]
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


reader = PdfReader("test.pdf")

documents = []

for i, page in enumerate(reader.pages):
    text = page.extract_text() or ""

    chunks = split_text(text)

    for chunk in chunks:
        documents.append({
            "page": i + 1,
            "content": chunk
        })

print(documents)
print("전체 문서 조각 수 :", len(documents))