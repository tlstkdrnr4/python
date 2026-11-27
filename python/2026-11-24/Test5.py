def area(a , b):
    return a * b

total = int(input("가로를 입력하세요 : ").strip())
table = int(input("세로를 입력하세요 : ").strip())

b = area(total , table)
print(b)