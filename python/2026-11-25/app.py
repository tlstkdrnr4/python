import sys
import json
print("Java LLM 공공 개발자 프로젝트 양성 과정")
print("수업시간 : 60")
print("실행기 정보 : " , sys.executable)

catalog = [("book" , 12000) , ("note" , 8000) , ("pen" , 1500) , ("bag" , 25000) , ("cup" , 6000)]
owned_items = {"book" , "pen"}
wish_items = {"pen", "bag"}
is_member = True
total_number = 0

order = {"book" : 3 , "pen" : 10}

itmes = {"name" : "민수" , "levle" : 100 , "Rating" : "S"}


def quote(price, quantity, shipping = 3000):
    subtotal = price * quantity
    return subtotal + shipping

def sum_values(*args):
    return sum(args)

def profiles(**kwargs):
    return kwargs
while True :
    print("=== 파이썬 스마트 스토어 & 학습 매니저 ===")
    print("1. 상품 목록 보기 (가격 정렬)")
    print("2. 주문 담기 및 견적 계산")
    print("3. 수량 일괄 정산 리포트 (컴프리헨션)")
    print("4. 보유 vs 관심 상품 비교 (집합 연산)")
    print("5. 주문 내역 JSON 저장 및 불러오기")
    print("6. 회원 프로필 / 추가메모 등록 (**kwargs)")
    print("0. 종료")
    number = int(input("번호를 입력해주세요 : "))
    if number == 1:
        profile = (sorted(catalog , key=lambda catalogs : catalogs[1] ,reverse = True))
        print(profile)
        print(f"최고가 상품은 {profile[0]}입니다")
        print(f"추천 TOP 3 {profile[:3]} 입니다")
        print(f"최저가 상품은 {profile[-1]} 입니다")
    elif number == 2:
        name = input("회원명을 입력해주세요 : ").strip()
        print(f"{name}님 환영합니다")
        member = input("회원 여부 (y/n): ").strip().lower()
        if member == "y" :
            is_member = True
        elif member == "n" :
            is_member = False
        else :
            print("y 또는 n을 입력해주세요 ")
            continue
        
        a = input("상품을 입력해주세요 : ").split(",")
        print(a)
        try:
            total = int(input("수량을 입력해주세요 : "))
        except ValueError :
            print("정수를 입력해주세요")
            continue
        b = int(input("가격을 입력해주세요 : "))
        price = quote(b , total , shipping=0)
        if price >= 30000 and is_member:
            c = quote(b , total , shipping=0)
            print(f"{c}원 무료배송")
        else :
            c = quote(b , total)
            print("배송비 3000원")
        total_number = sum_values(total_number , c) # AI 가변인자를 사용해야하는데 사용하지 않았음 
        print(f"누적 주문 금액 {total_number}원")

    elif number == 3:
            lists = [2, 3, 0 , -1 , 1]
            scores = []
            for n in lists:
                if n <= 0:
                    continue
                scores.append(n)  
            totals = [quantity * 8000 for quantity in scores]
            report = {str(i + 1) : value for i , value in enumerate(totals)}
            print(report)

                
    elif number == 4:
        a = owned_items & wish_items
        b = owned_items - wish_items
        c = owned_items | wish_items
        print(sorted(a))
        print(sorted(b))
        print(sorted(c))

    elif number == 5:
        summary ={
            "order" : order,
            "total_number" : total_number,
            "profile" : itmes
        }
        text = json.dumps(summary, ensure_ascii=False)
        load = json.loads(text)
        print(text)
        print(load["total_number"] == total_number)
    elif number == 6:
        point = (30, 40)
        x , y  = point
        print(itmes)
        print(x, y)
    elif number == 0:  # AI 0 이외의 숫자를 입력해도 종료되는 것을 0으로만 종료되게 수정
        # 요구사항에는 0을 입력했을때 종료하도록 명시하고 있다.
        print("종료합니다")
        break
    else:
        print("잘못된 번호입니다")