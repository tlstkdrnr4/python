# and 미포함 range 초기값 포함 끝값 제외
# 반복변수 초기화 조건 증감

total = 0
for quantity in [1, 0 ,3]:
    if quantity == 0 :
        continue
    total += quantity
print(total)

attempts = 0
while attempts < 3 :
    attempts += 1
    if attempts == 2:
        break
print(attempts)

for number in range(1,5) :
    if number %2 != 0 :
        continue
    total += number
print(total)