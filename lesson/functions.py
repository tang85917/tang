def get_todos(filepath='todos.txt'):
    with open(filepath, 'r') as f:
        todos = f.readlines()
    return todos

def write_todos( todos_arg, filepath='todos.txt'):
    with open(filepath, 'w') as f:
        f.writelines(todos_arg)


    
