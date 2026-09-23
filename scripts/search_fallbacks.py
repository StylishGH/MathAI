import os
import re

for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.readlines()
            for i, line in enumerate(content):
                if re.search(r'aluno_id.*?=\s*1|get\([\'"]id[\'"],\s*1\)', line):
                    print(f"{path}:{i+1}: {line.strip()}")
