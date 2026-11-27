import json
student = {"name" : "지호" , "score" : 90 , "name1" : "민기" , "score" : 70}
text = json.dumps(student , ensure_ascii=False)
print(json.loads(text)["score"])

a = {"과학" , "수학" , "영어" , "체육"}
b = {"국어" , "과학" , "한자" , "영어"}

print(a & b)
print(a - b)