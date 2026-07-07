import sys
sys.stdout.reconfigure(encoding='utf-8')

# Search for renderStep in v1.1
with open("simulador_v1.1.html", "r", encoding="utf-8") as f:
    content1 = f.read()

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content2 = f.read()

def print_around(content, query):
    idx = content.find(query)
    if idx != -1:
        start_line = content[:idx].count("\n")
        lines = content.split("\n")
        print(f"=== Found '{query}' ===")
        for i in range(max(0, start_line - 10), min(len(lines), start_line + 30)):
            print(f"{i+1}: {lines[i]}")
        print("========================")

print("--- SIMULADOR v1.1 ---")
print_around(content1, "function renderStep()")

print("\n--- SIMULADOR v1.2 ---")
print_around(content2, "function renderStep()")
