# .을 붙이는건 앞에것을 끝내고 그 값으로 뒤에 메소드를 수행하라는 뜻이다
# f-string 는 안에 변수를 넣을려면 {} 중문으로 넣어야 한다 total:, 천 단위표시
# strip 은 공백 제거 
name = input("이름: ").strip()
raw_quantity = input("수량 : ").strip()
quantity = int(raw_quantity)
total = quantity * 8000
print(f"{name}님 , 총액 : {total:,} 원")
print("book , pen" .split(","))