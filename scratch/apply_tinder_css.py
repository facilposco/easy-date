import sys
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Remove old Tinder UI enhancements if they exist
start_str = "/* Tinder UI Enhancements"
if start_str in content:
    idx = content.find(start_str)
    end_idx = content.find("</style>", idx)
    content = content[:idx] + content[end_idx:]

tinder_css = """
    /* Tinder Dark Mode UI Enhancements */
    :root {
        --bubble-me: #e5d5d5; /* Pinkish grey for user */
        --bubble-me-text: #000000;
        --bubble-her: #151515; /* Dark grey for NPC */
        --bubble-her-text: #ffffff;
    }
    
    /* Backgrounds */
    body, .app-container {
        background-color: #000000;
    }
    
    /* Header */
    .top-bar {
        background-color: #000000;
        border-bottom: 1px solid #1a1a1a;
    }
    
    /* Bubbles */
    .message.user .bubble {
        background: var(--bubble-me) !important;
        color: var(--bubble-me-text) !important;
        box-shadow: none !important;
        border-radius: 20px 20px 4px 20px !important;
        padding: 10px 14px !important;
        font-weight: 400 !important;
    }
    
    .message.her .bubble {
        background: var(--bubble-her) !important;
        color: var(--bubble-her-text) !important;
        box-shadow: none !important;
        border: 1px solid #222 !important;
        border-radius: 20px 20px 20px 4px !important;
        padding: 10px 14px !important;
        font-weight: 400 !important;
    }
    
    /* Time Text inside bubbles */
    .message-time-highlight {
        font-size: 0.65rem !important;
        opacity: 0.5;
        display: block;
        text-align: right;
        margin-top: 4px;
    }
    .message.user .message-time-highlight {
        color: #000000;
    }
    
    /* Input Box at the Bottom */
    .options-container {
        background: #000000 !important;
        border-top: none !important;
        padding: 10px 15px !important;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    #user-free-text {
        background: #1a1a1a !important;
        color: #ffffff !important;
        border: 1px solid #333 !important;
        border-radius: 24px !important;
        padding: 12px 16px !important;
        box-shadow: none !important;
        flex: 1; /* Take most space */
    }
    #user-free-text::placeholder {
        color: #666;
    }
    
    #btn-send {
        background: transparent !important;
        color: #fe3c72 !important;
        box-shadow: none !important;
        padding: 0 !important;
        width: auto !important;
        flex: 0 0 auto !important;
        font-size: 0.95rem !important;
        letter-spacing: 0 !important;
    }
    #btn-send:disabled {
        opacity: 0.3 !important;
    }
"""

content = content.replace("</style>", tinder_css + "\n</style>")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)
print("Applied Tinder Dark Mode CSS successfully.")
