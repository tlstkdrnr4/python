# 밑에 꺼 까지 같이 컴파일 해달라고 할 때는 : 을 붙인다.
# 들여쓰기 는 같은 코드 묶음을 나타내는 공백이다

total = 30000
is_meber = False
if total < 0 :
    message = "금액오류"
elif total >= 30000 and is_meber :
    message = "무료배송"
else :
    message = "배송비 3000원"
print(message)