import os
import ast

def get_imports_from_file(filepath):
    """Extract all imports from a Python file."""
    with open(filepath, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=filepath)
    
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports

def get_all_imports_from_directory(directory):
    """Get all unique imports from all Python files in the directory."""
    imports_set = set()
    
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                imports = get_imports_from_file(filepath)
                imports_set.update(imports)
    
    return sorted(imports_set)

# Directory you want to scan
current_directory = '.'

all_imports = get_all_imports_from_directory(current_directory)

# Print all the collected imports
print("Modules used in the current directory:")
for module in all_imports:
    print(module)
