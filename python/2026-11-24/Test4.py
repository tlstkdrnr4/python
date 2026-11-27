number = 0
aaa = 0
for total in range(1,11):
    if total %2 != 0:
        continue
    number += total
print(number) 
print("---------------------------")

a = 0
while a < 10 :
    a += 1
    if a %2 == 0:
        continue
    aaa += a
print(aaa)
print("--------------------------")

for total in range(1,11):
    if total %2 != 0:
        print(total)
print("---------------------")


for total in range(1,11):
    if total %2 == 0:
        print(total)
print("----------------------")