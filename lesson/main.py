from functions import get_todos, write_todos
import time

now = time.strftime('%Y-%m-%d %a %H:%M:%S')
print(now)

while True:
    user_action = input("Type add, show, edit, complete or exit: ")
    user_action = user_action.strip()
    
    if "add" in user_action:
        todo = user_action[4:]
        
        todos = get_todos()
                        
        todos.append(todo + '\n')
        
        write_todos(todos)
        
    elif "show" in user_action:
        todos = get_todos()
        
        for i, todo in enumerate(todos):
            todo = todo.strip('\n')
            print(f'{i+1}-{todo}')
            
    elif "edit" in user_action:
        try:
            number = int(user_action[5:])
            print(number)
            number = number - 1
            
            todos = get_todos()
                
            new_todo = input("Enter new todo: ")
            todos[number] = new_todo + '\n'
            
            write_todos(todos)
                
        except ValueError:
            print("Your command is not valid.")
            continue
            
    elif "complete" in user_action: 
        try:
            number = int(user_action[9:])
            
            print(number)
            todos = get_todos()
                
            todo_to_remove = todos[number - 1].strip('\n')
            todos.pop(number - 1)
            
            write_todos(todos)
                
            message = f"Todo {todo_to_remove} was removed from the list."
            print(message)
        except IndexError:
            print("There is no item with that number.")
            continue
            
    elif "exit" in user_action:
        break
    
    else:
        print('Command is not valid')
        
print("Bye!")

