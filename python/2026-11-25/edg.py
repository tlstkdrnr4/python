import requests

response = requests.post(
    "http://localhost:11434/api/embed",
    json={
        "model": "nomic-embed-text",
        "input": "파이썬은 프로그래밍 언어입니다."
    }
)

response.raise_for_status()

data = response.json()

embedding = data["embeddings"][0]

print(embedding)
print(type(embedding))
print(len(embedding))