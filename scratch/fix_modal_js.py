import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

target_loose = "document.getElementById('coach-title').innerText = title;\n        document.getElementById('coach-msg-text').innerText = msg;"
replacement_loose = """document.getElementById('coach-title').innerText = title;
        document.getElementById('coach-msg-text').innerHTML = parseMarkdown(msg);"""

if target_loose in content:
    content = content.replace(target_loose, replacement_loose)
    
    func_def = """    // Helper function for basic markdown parsing
    function parseMarkdown(text) {
        if (!text) return "";
        let html = text.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
        html = html.replace(/\\*(.*?)\\*/g, '<em>$1</em>');
        html = html.replace(/\\n/g, '<br>');
        return html;
    }
    
    function showCoachModal(title, msg, audioType, onClose) {"""
    
    content = content.replace("function showCoachModal(title, msg, audioType, onClose) {", func_def)
    print("Success: Markdown parsing added for showCoachModal.")
else:
    print("Error: Could not find target JS string in simulador_v1.2.html.")

with open("simulador_v1.2.html", "w", encoding="utf-8") as f:
    f.write(content)
