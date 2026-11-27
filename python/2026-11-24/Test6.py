def basket_total(*args):
    return sum(args)

print(basket_total(3000 , 5000 , 6000 , 7000 , 10000))
items = [("pen" , 2000) , ("book" , 50000) , ("notebook" , 100000) , ("bag" , 5000)]
print(sorted(items, key=lambda item: item[1] , reverse=True))