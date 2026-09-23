import sys

files = ["scripts/ingest_efomm.py", "scripts/ingest_notion_cederj.py"]

for file in files:
    with open(file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Simple replace to remove known emojis from print statements
    content = content.replace("🚀 ", "")
    content = content.replace("🧠 ", "")
    content = content.replace("✅ ", "")
    content = content.replace("❌ ", "")
    content = content.replace("💾 ", "")
    content = content.replace("🎉 ", "")
    content = content.replace("Ys? ", "") # The broken unicode from powershell
    
    # Add a fallback just in case
    content = "import sys\nimport io\nsys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')\n" + content
    
    with open(file, "w", encoding="utf-8") as f:
        f.write(content)

print("Fixed!")
