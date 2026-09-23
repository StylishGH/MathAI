import sqlite3
c = sqlite3.connect('data/mathai.db')
schema = [x[0] for x in c.execute("SELECT sql FROM sqlite_master WHERE type='table'") if x[0]]
with open('schema.txt', 'w', encoding='utf-8') as f:
    f.write('\n\n'.join(schema))
