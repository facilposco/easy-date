import os
import re

file_path = "c:/desarrollos/antigravity/text game youtube estudio ejemplos/simulador_v1.2.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace evaluateSelection
new_evaluate = """    async function evaluateSelection() {
        const textElement = document.getElementById('user-free-text');
        const userText = textElement.value.trim();
        if(!userText) {
            alert("Escribe un mensaje primero");
            return;
        }
        
        const btnSend = document.getElementById('btn-send');
        btnSend.disabled = true;
        btnSend.style.opacity = '0.5';
        btnSend.innerText = '⏳';
        
        const level = gameData.levels[gameState.level_index];
        const chatArea = document.getElementById('chat-area');
        
        // Añadir mensaje del usuario
        const userMsg = document.createElement('div');
        userMsg.className = 'message user';
        userMsg.innerHTML = `<div class="bubble">${userText}</div>`;
        chatArea.appendChild(userMsg);
        
        gameState.history.push({
            sender: 'user', 
            text: userText,
            levelIndex: gameState.level_index
        });
        saveState();
        scrollToBottom();
        
        // Preparar payload para API
        const payload = {
            level: gameState.level_index + 1,
            history: gameState.history.map(h => ({
                role: h.sender === 'user' ? 'user' : 'assistant',
                content: h.text
            })),
            user_message: userText
        };
        
        try {
            const response = await fetch('http://localhost:8000/api/evaluate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                throw new Error("Error en el servidor");
            }
            
            const data = await response.json();
            
            // Evaluar (Mockeado: se asume buena respuesta si evaluation es positivo)
            // Por simplicidad, aumentaremos atracción siempre a menos que sea un error
            let isCorrect = !data.evaluation.toLowerCase().includes("error") && !data.evaluation.toLowerCase().includes("débil");
            
            let feedbackTitle = isCorrect ? "¡Buena Respuesta!" : "Atención";
            let audioType = isCorrect ? "success" : "warning";
            
            if(isCorrect) {
                gameState.attraction = Math.min(100, gameState.attraction + 10);
            } else {
                gameState.attraction = Math.max(0, gameState.attraction - 10);
                gameState.lives -= 1;
            }
            updateTopBarStats();
            
            showCoachModal(feedbackTitle, data.evaluation, audioType, () => {
                textElement.value = '';
                
                if (gameState.lives <= 0) {
                    showGameOverModal();
                    return;
                }
                
                gameState.step_index += 1;
                
                // Mostrar mensaje de la chica
                let nextMsgText = "Interesante..."; // Fallback
                if (data.new_history && data.new_history.length > 0) {
                    let lastMsg = data.new_history[data.new_history.length - 1];
                    if (lastMsg.role === "assistant") {
                        nextMsgText = lastMsg.content.replace("[MOCK NPC RESPONSE] ", "");
                    }
                }
                
                const msgDiv = document.createElement('div');
                msgDiv.className = 'message her';
                
                const avaDiv = document.createElement('div');
                avaDiv.className = 'avatar';
                avaDiv.style.backgroundImage = `url("${levelAvatars[gameState.level_index]}")`;
                avaDiv.addEventListener('click', () => openLightbox(levelAvatars[gameState.level_index]));
                
                const bubDiv = document.createElement('div');
                bubDiv.className = 'bubble';
                bubDiv.innerHTML = nextMsgText;
                
                msgDiv.appendChild(avaDiv);
                msgDiv.appendChild(bubDiv);
                chatArea.appendChild(msgDiv);
                
                gameState.history.push({
                    sender: 'her',
                    text: nextMsgText,
                    levelIndex: gameState.level_index
                });
                saveState();
                scrollToBottom();
                
                // Si llegamos a WAITING_USER, renderizamos paso de nuevo. Si es fin, levelup.
                if (data.next_state === "WIN" || gameState.step_index >= 5) {
                    // Forzamos 5 turnos de victoria para el demo
                    showLevelUpModal();
                } else {
                    renderStep();
                }
            });
            
        } catch (error) {
            console.error(error);
            alert("Error conectando con el backend local.");
            btnSend.disabled = false;
            btnSend.style.opacity = '1';
            btnSend.innerText = 'ENVIAR';
        }
    }"""

# Using regex to replace the old evaluateSelection function completely
# It starts with "function evaluateSelection() {" and ends before "function showCoachModal"
pattern = re.compile(r'    function evaluateSelection\(\) \{.*?    \}\n    \n    function showCoachModal', re.DOTALL)
content = pattern.sub(new_evaluate + '\n    \n    function showCoachModal', content)

# Fix window.onload history render
onload_history_pattern = re.compile(r'const timeHighlight = h\.sender === \'user\' \? \'Tardaste\' : \'Tardó\';.*?const bubDiv = document\.createElement\(\'div\'\);', re.DOTALL)
new_onload_history = """                    let timeHtml = "";
                    if (h.timeText) {
                        const timeHighlight = h.sender === 'user' ? 'Tardaste' : 'Tardó';
                        timeHtml = `<br><span class="message-time-highlight">(${timeHighlight}: ${h.timeText})</span>`;
                    }
                    const bubDiv = document.createElement('div');"""
content = onload_history_pattern.sub(new_onload_history, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("evaluateSelection replaced and onload fixed.")
