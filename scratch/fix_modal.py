import sys
sys.stdout.reconfigure(encoding='utf-8')

with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Modify the CSS for the modal to support scrolling for long text
old_coach_modal = """.coach-modal {
  background: var(--bg-card);
  padding: 20px;
  border-radius: var(--border-radius-lg);
  max-width: 90%;
  width: 400px;
  text-align: center;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}"""

new_coach_modal = """.coach-modal {
  background: var(--bg-card);
  padding: 20px;
  border-radius: var(--border-radius-lg);
  max-width: 90%;
  width: 400px;
  max-height: 85vh; /* Maximum height to 85% of viewport */
  display: flex;
  flex-direction: column;
  text-align: center;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
}"""

if old_coach_modal in content:
    content = content.replace(old_coach_modal, new_coach_modal)
    print("Success: Coach modal container CSS updated.")
else:
    print("Error: Could not find exact old_coach_modal CSS.")
    # Attempt looser replacement for modal
    idx = content.find(".coach-modal {")
    if idx != -1:
        end_idx = content.find("}", idx)
        if end_idx != -1:
            content = content[:idx] + new_coach_modal + content[end_idx+1:]
            print("Success: Looser replacement for modal CSS worked.")


old_coach_message = """.coach-message {
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text-secondary);
  margin: 15px 0 25px 0;
}"""

new_coach_message = """.coach-message {
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text-secondary);
  margin: 15px 0 25px 0;
  overflow-y: auto; /* Enable vertical scrolling */
  text-align: left; /* Better for long markdown text */
  padding-right: 10px;
  flex: 1; /* Allow it to take up remaining space in flex container */
}
/* Scrollbar styling for coach message */
.coach-message::-webkit-scrollbar {
  width: 6px;
}
.coach-message::-webkit-scrollbar-thumb {
  background: rgba(255,255,255,0.2);
  border-radius: 4px;
}"""

if old_coach_message in content:
    content = content.replace(old_coach_message, new_coach_message)
    print("Success: Coach message CSS updated.")
else:
    print("Error: Could not find exact old_coach_message CSS.")
    # Attempt looser replacement for message
    idx = content.find(".coach-message {")
    if idx != -1:
        end_idx = content.find("}", idx)
        if end_idx != -1:
            content = content[:idx] + new_coach_message + content[end_idx+1:]
            print("Success: Looser replacement for coach message CSS worked.")

# The modal was missing markdown formatting parser.
# The backend sends plain text that contains Markdown like **bold**.
# Let's add a quick markdown parser inside `showCoachModal`.

old_show_coach_modal = """    function showCoachModal(title, text, type, callback) {
        document.getElementById('coach-title').innerText = title;
        document.getElementById('coach-msg-text').innerText = text;
        
        let imgEl = document.getElementById('coach-img-el');
        imgEl.src = coachAvatar;
        
        const modal = document.getElementById('modal-overlay');
        modal.classList.add('active');"""

new_show_coach_modal = """    // Helper function for basic markdown parsing
    function parseMarkdown(text) {
        if (!text) return "";
        let html = text.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
        html = html.replace(/\\*(.*?)\\*/g, '<em>$1</em>');
        html = html.replace(/\\n/g, '<br>');
        return html;
    }

    function showCoachModal(title, text, type, callback) {
        document.getElementById('coach-title').innerText = title;
        document.getElementById('coach-msg-text').innerHTML = parseMarkdown(text);
        
        let imgEl = document.getElementById('coach-img-el');
        imgEl.src = coachAvatar;
        
        const modal = document.getElementById('modal-overlay');
        modal.classList.add('active');"""

if old_show_coach_modal in content:
    content = content.replace(old_show_coach_modal, new_show_coach_modal)
    print("Success: showCoachModal updated with Markdown parsing.")
else:
    print("Error: Could not find exact showCoachModal JS.")
    target_loose = "document.getElementById('coach-title').innerText = title;\n        document.getElementById('coach-msg-text').innerText = text;"
    replacement_loose = """document.getElementById('coach-title').innerText = title;
        document.getElementById('coach-msg-text').innerHTML = parseMarkdown(text);"""
    
    if target_loose in content:
        content = content.replace(target_loose, replacement_loose)
        # Also need to inject the parseMarkdown function before it
        func_def = """    function parseMarkdown(text) {
        if (!text) return "";
        let html = text.replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>');
        html = html.replace(/\\*(.*?)\\*/g, '<em>$1</em>');
        html = html.replace(/\\n/g, '<br>');
        return html;
    }
    
    function showCoachModal(title, text, type, callback) {"""
        content = content.replace("function showCoachModal(title, text, type, callback) {", func_def)
        print("Success: Looser replacement for showCoachModal worked.")

with open("simulador_v1.2.html", "w", encoding="utf-8") as f:
    f.write(content)
