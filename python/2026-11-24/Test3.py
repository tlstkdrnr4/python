total = int(input("점수를 입력해주세요 : ").strip())

if total < 0 or total > 100 :
    print("오류 값")
elif total >= 90:
    print("A")
elif total >= 80:
    print("B")
else :
    print("C")