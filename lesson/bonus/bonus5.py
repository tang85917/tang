import json

with open(r'code\lesson\bonus\json1.json', 'r') as f:
    content = f.read()
    
data = json.loads(content)

score = 0
for i, (key, q) in enumerate(data.items()):
    print(f"{key} - {q['question']}")
    for c in q['choice']:
        print(c)
        
    user_answer = input("Enter your choice number: ")
    if user_answer == q['answer']:
        score += 1
        
    print(f"Your answer: {user_answer}\nCorrect answer: {q['answer']}")
    
print(score, '/', len(data))
