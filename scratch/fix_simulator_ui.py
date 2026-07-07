with open("simulador_v1.2.html", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Fix bottom button flex layout
old_btn = '<button class="btn-send" id="btn-send" style="width: 80px; height: auto; font-size: 0.9rem; font-weight: 800; margin: 0; background: var(--accent-gradient); border-radius: 8px; cursor: pointer; border: none; color: white;">ENVIAR</button>'
new_btn = '<button class="btn-send" id="btn-send" style="flex: 0 0 90px !important; height: 60px !important; font-size: 0.9rem; font-weight: 800; margin: 0; background: var(--accent-gradient); border-radius: 8px; cursor: pointer; border: none; color: white;">ENVIAR</button>'

if old_btn in content:
    content = content.replace(old_btn, new_btn)
    print("Success: Button layout fixed.")
else:
    print("Notice: Button style already fixed or not found.")

# 2. Modify startLevel() to include system message
old_start_level = """    function startLevel() {
        document.getElementById('match-modal').classList.remove('active');
        // Inicializar vidas del nivel
        gameState.lives = levelLivesMap[gameState.level_index];
        gameState.attraction = 50;
        gameState.step_index = 0;
        document.getElementById('chat-area').innerHTML = '';
        saveState();
        renderStep();
    }"""

new_start_level = """    function startLevel() {
        document.getElementById('match-modal').classList.remove('active');
        // Inicializar vidas del nivel
        gameState.lives = levelLivesMap[gameState.level_index];
        gameState.attraction = 50;
        gameState.step_index = 0;
        
        const chatArea = document.getElementById('chat-area');
        chatArea.innerHTML = '';
        
        const level = gameData.levels[gameState.level_index];
        const sysMsg = document.createElement('div');
        sysMsg.style = "text-align: center; color: rgba(255,255,255,0.4); font-size: 0.8rem; margin: 15px auto; font-style: italic; max-width: 80%; line-height: 1.3;";
        sysMsg.innerHTML = `¡Has hecho match con ${level.girl_name} (${level.description})! Ella está esperando tu primer mensaje para empezar...`;
        chatArea.appendChild(sysMsg);
        
        saveState();
        renderStep();
    }"""

if old_start_level in content:
    content = content.replace(old_start_level, new_start_level)
    print("Success: startLevel updated with system message.")
else:
    # Let's inspect the whitespace in startLevel of simulador_v1.2.html to see why it didn't match
    print("Notice: startLevel exact string match failed.")
    # Try a looser replacement
    target_loose = "document.getElementById('chat-area').innerHTML = '';\n        saveState();\n        renderStep();"
    replacement_loose = """document.getElementById('chat-area').innerHTML = '';
        
        const level = gameData.levels[gameState.level_index];
        const sysMsg = document.createElement('div');
        sysMsg.style = "text-align: center; color: rgba(255,255,255,0.4); font-size: 0.8rem; margin: 15px auto; font-style: italic; max-width: 80%; line-height: 1.3;";
        sysMsg.innerHTML = `¡Has hecho match con ${level.girl_name} (${level.description})! Ella está esperando tu primer mensaje para empezar...`;
        chatArea.appendChild(sysMsg);
        
        saveState();
        renderStep();"""
    
    if target_loose in content:
        content = content.replace(target_loose, replacement_loose)
        print("Success: Loose startLevel replacement succeeded.")
    else:
        print("Error: Loose startLevel replacement also failed.")

with open("simulador_v1.2.html", "w", encoding="utf-8") as f:
    f.write(content)
