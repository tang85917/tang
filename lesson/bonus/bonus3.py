import random

try:
    low = int(input("Enter the lower bound: "))
    high = int(input("Enter the upper bound: "))
    
    if low > high:
        print("⚠️ 上限は下限以上にしてください。")
    else:
        print(random.randint(low, high))
except ValueError:
    print("⚠️ 数字を入力してください。")