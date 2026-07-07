import os
import re

file_path = "c:/desarrollos/antigravity/text game youtube estudio ejemplos/simulador_v1.2.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace the footer
old_footer = """            <footer class="bottom-panel">
                <div class="options-grid" id="options-grid">
                    <!-- Options -->
                </div>
                
                <div class="time-selector">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <label class="time-label">Tardas en responder:</label>
                        <span id="slider-time-display" style="font-size: 0.8rem; font-weight: bold; color: #3b82f6;">Ahora mismo</span>
                    </div>
                    <div class="slider-wrapper">
                        <input type="range" min="0" max="7" value="0" class="time-slider" id="time-slider" style="width:100%;">
                        <div class="slider-ticks-labels">
                            <span>Ahora</span><span>15m</span><span>1h</span><span>2h</span><span>4h</span><span>12h</span><span>24h</span><span>2d</span>
                        </div>
                    </div>
                </div>
                
                <div class="action-row" style="display: flex; flex-direction: column; gap: 4px; width: 100%;">
                    <!-- Fila Inferior: Reiniciar (izquierda) y Estudiar Casos (derecha) — más delgada -->
                    <div style="display: flex; gap: 5px; width: 100%;">
                        <button onclick="resetGame()" class="btn-reset" id="btn-reset" style="flex: 1; height: 26px; margin: 0; padding: 0; font-size: 0.8rem; border-radius: 8px;">Reiniciar</button>
                        <button onclick="showScreen('study')" class="btn-study-highlight" style="flex: 1; height: 26px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 8px; font-weight: bold; font-family: Outfit, sans-serif; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 0.8rem; margin: 0;">📚 Estudiar</button>
                    </div>
                    <!-- Fila Superior: ENVIAR RESPUESTA — doble de alto que la fila de secundarios -->
                    <button class="btn-send" id="btn-send" style="width: 100%; height: 52px; font-size: 1rem; font-weight: 800; margin: 0; background: var(--accent-gradient); letter-spacing: 0.03em;">ENVIAR RESPUESTA</button>
                </div>
            </footer>"""

new_footer = """            <footer class="bottom-panel">
                <div class="input-container" style="display: flex; gap: 8px; align-items: stretch; margin-bottom: 8px;">
                    <textarea id="user-free-text" placeholder="Escribe tu mensaje aquí..." style="flex: 1; height: 60px; background: #252533; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: white; padding: 8px; font-family: inherit; font-size: 0.95rem; resize: none; outline: none;"></textarea>
                    <button class="btn-send" id="btn-send" style="width: 80px; height: auto; font-size: 0.9rem; font-weight: 800; margin: 0; background: var(--accent-gradient); border-radius: 8px; cursor: pointer; border: none; color: white; display: flex; align-items: center; justify-content: center;">ENVIAR</button>
                </div>
                
                <div class="action-row" style="display: flex; flex-direction: column; gap: 4px; width: 100%;">
                    <div style="display: flex; gap: 5px; width: 100%;">
                        <button onclick="resetGame()" class="btn-reset" id="btn-reset" style="flex: 1; height: 26px; margin: 0; padding: 0; font-size: 0.8rem; border-radius: 8px;">Reiniciar</button>
                        <button onclick="showScreen('study')" class="btn-study-highlight" style="flex: 1; height: 26px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 8px; font-weight: bold; font-family: Outfit, sans-serif; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 0.8rem; margin: 0;">📚 Estudiar</button>
                    </div>
                </div>
            </footer>"""

content = content.replace(old_footer, new_footer)

# 2. Add download buttons
old_retry_btn = '<button class="btn-premium" id="gameover-retry-btn" style="background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);">REINTENTAR NIVEL ⟳</button>'
new_retry_btn = '<button class="btn-premium" id="gameover-retry-btn" style="background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); margin-bottom: 8px;">REINTENTAR NIVEL ⟳</button>\n                <button class="btn-premium" onclick="downloadHistory()" style="background: #252533; border: 1px solid rgba(255,255,255,0.1); font-size: 0.85rem; margin-top: 0; padding: 10px;">Descargar Historial 📝</button>'
content = content.replace(old_retry_btn, new_retry_btn)

old_play_btn = '<button class="btn-premium" onclick="resetGame()" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">VOLVER A JUGAR 🎮</button>'
new_play_btn = '<button class="btn-premium" onclick="resetGame()" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); margin-bottom: 8px;">VOLVER A JUGAR 🎮</button>\n                <button class="btn-premium" onclick="downloadHistory()" style="background: #252533; border: 1px solid rgba(255,255,255,0.1); font-size: 0.85rem; margin-top: 0; padding: 10px;">Descargar Historial 📝</button>'
content = content.replace(old_play_btn, new_play_btn)


# 3. Modify renderStep
old_renderStep = """    function renderStep() {
        const level = gameData.levels[gameState.level_index];
        const step = level.steps[gameState.step_index];
        
        // Actualizar UI de cabecera
        document.getElementById('level-progress-display').innerText = `${level.girl_name} (${gameState.step_index + 1}/${level.steps.length})`;
        updateTopBarStats();
        
        // Cargar opciones de respuesta
        const optsGrid = document.getElementById('options-grid');
        optsGrid.innerHTML = '';
        
        step.options.forEach((opt, idx) => {
            const letter = String.fromCharCode(65 + idx);
            const label = document.createElement('label');
            label.className = 'option-card';
            
            const input = document.createElement('input');
            input.type = 'radio';
            input.name = 'reply_opt';
            input.value = JSON.stringify(opt);
            
            const card = document.createElement('span');
            card.className = 'card-content';
            card.innerHTML = `<span class="letter">${letter}</span> <span class="text-content">${opt.text}</span>`;
            
            label.appendChild(input);
            label.appendChild(card);
            optsGrid.appendChild(label);
        });
        
        document.getElementById('btn-send').disabled = false;
        document.getElementById('btn-send').style.opacity = '1';
        document.getElementById('time-slider').value = 0;
        document.getElementById('slider-time-display').innerText = TIME_TICKS[0];
    }"""

new_renderStep = """    function renderStep() {
        const level = gameData.levels[gameState.level_index];
        
        // Actualizar UI de cabecera
        let stepCount = level.steps ? level.steps.length : "?";
        document.getElementById('level-progress-display').innerText = `${level.girl_name} (${gameState.step_index + 1}/${stepCount})`;
        updateTopBarStats();
        
        document.getElementById('user-free-text').value = '';
        
        document.getElementById('btn-send').disabled = false;
        document.getElementById('btn-send').style.opacity = '1';
        document.getElementById('btn-send').innerText = 'ENVIAR';
    }"""
content = content.replace(old_renderStep, new_renderStep)


# 4. Modify evaluateSelection
old_evaluate = """    function evaluateSelection() {
        const selected = document.querySelector('input[name="reply_opt"]:checked');
        if(!selected) {
            alert("Selecciona un mensaje primero");
            return;
        }
        
        document.getElementById('btn-send').disabled = true;
        document.getElementById('btn-send').style.opacity = '0.5';
        
        const opt = JSON.parse(selected.value);
        const sliderVal = parseInt(document.getElementById('time-slider').value);
        const chosenTime = TIME_TICKS[sliderVal];
        
        const level = gameData.levels[gameState.level_index];
        const step = level.steps[gameState.step_index];
        
        const chatArea = document.getElementById('chat-area');
        
        // Añadir mensaje del usuario
        const userMsg = document.createElement('div');
        userMsg.className = 'message user';
        let userTimeHtml = `<br><span class="message-time-highlight">(Tardaste: ${chosenTime})</span>`;
        userMsg.innerHTML = `<div class="bubble">${opt.text}${userTimeHtml}</div>`;
        chatArea.appendChild(userMsg);
        
        gameState.history.push({
            sender: 'user', 
            text: opt.text, 
            timeText: chosenTime, 
            levelIndex: gameState.level_index
        });
        saveState();
        scrollToBottom();
        
        // Evaluar lógica de vidas, atracción y timing
        // REGLA v1.1: El tiempo permitido es igual o mayor al de ella. "Ahora mismo" (índice 0) NUNCA está permitido.
        let isCorrect = opt.is_correct;
        let minAllowed = Math.min(...step.allowed_time_indices);
        // El usuario puede elegir ese índice mínimo o cualquier valor mayor (pero no 0 = Ahora mismo)
        let isTimeCorrect = (sliderVal >= minAllowed) && (sliderVal > 0);
        
        let feedbackTitle = "";
        let feedbackText = "";
        let audioType = "";
        
        if (isCorrect && isTimeCorrect) {
            // Excelente!
            gameState.attraction = Math.min(100, gameState.attraction + 10);
            feedbackTitle = "¡Excelente Respuesta!";
            feedbackText = step.coach_feedback_correct;
            audioType = "success";
        } else if (isCorrect && !isTimeCorrect) {
            // Mensaje correcto, pero timing incorrecto
            gameState.attraction = Math.min(100, gameState.attraction + 3);
            feedbackTitle = "Buen Mensaje, Pero Fallaste el Tiempo";
            feedbackText = "⏱️ " + step.coach_feedback_time_incorrect + "\\n\\n💬 El mensaje era correcto: " + step.coach_feedback_correct;
            audioType = "warning";
        } else if (!isCorrect && isTimeCorrect) {
            // Timing bien, mensaje incorrecto
            gameState.attraction = Math.max(0, gameState.attraction - 15);
            gameState.lives -= 1;
            feedbackTitle = "Respuesta Incorrecta";
            feedbackText = "❌ " + step.coach_feedback_incorrect + "\\n\\n✅ Sí respondiste en buen momento."; 
            audioType = "error";
        } else {
            // Doble error: ni respuesta ni tiempo
            gameState.attraction = Math.max(0, gameState.attraction - 20);
            gameState.lives -= 1;
            feedbackTitle = "Doble Error — Respuesta y Tiempo";
            feedbackText = "❌ RESPUESTA INCORRECTA: " + step.coach_feedback_incorrect + "\\n\\n⏱️ TAMBIÉN FALLASTE EL TIEMPO: " + step.coach_feedback_time_incorrect;
            audioType = "error";
        }
        
        updateTopBarStats();
        
        // Mostrar Modal de Feedback del Coach
        showCoachModal(feedbackTitle, feedbackText, audioType, () => {
            if (gameState.lives <= 0) {
                showGameOverModal();
                return;
            }
            
            // Avanzar al siguiente paso o terminar nivel
            gameState.step_index += 1;
            
            if (gameState.step_index < level.steps.length) {
                // Siguiente paso: mostrar mensaje de la chica
                const nextStep = level.steps[gameState.step_index];
                
                const msgDiv = document.createElement('div');
                msgDiv.className = 'message her';
                
                const avaDiv = document.createElement('div');
                avaDiv.className = 'avatar';
                avaDiv.style.backgroundImage = `url("${levelAvatars[gameState.level_index]}")`;
                avaDiv.addEventListener('click', () => openLightbox(levelAvatars[gameState.level_index]));
                
                const timeHtml = `<span class="message-time-highlight">(${nextStep.her_time})</span>`;
                
                const bubDiv = document.createElement('div');
                bubDiv.className = 'bubble';
                bubDiv.innerHTML = nextStep.her_message + `<br>${timeHtml}`;
                
                msgDiv.appendChild(avaDiv);
                msgDiv.appendChild(bubDiv);
                chatArea.appendChild(msgDiv);
                
                gameState.history.push({
                    sender: 'her',
                    text: nextStep.her_message,
                    timeText: nextStep.her_time,
                    levelIndex: gameState.level_index
                });
                saveState();
                scrollToBottom();
                
                // Cargar opciones del siguiente paso
                renderStep();
            } else {
                // Fin del nivel! Celebración!
                showLevelUpModal();
            }
        });
    }"""

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
            let isCorrect = !data.evaluation.includes("error") && !data.evaluation.toLowerCase().includes("débil");
            
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

content = content.replace(old_evaluate, new_evaluate)

# 5. Remove time slider event listener
content = re.sub(r'document\.getElementById\(\'time-slider\'\)\.addEventListener\(.*?\}\);', '', content, flags=re.DOTALL)

# 6. Add downloadHistory function
download_history_fn = """    function downloadHistory() {
        let historyText = "HISTORIAL DE JUEGO\\n================\\n\\n";
        gameState.history.forEach(item => {
            let sender = item.sender === 'user' ? "Tú" : "Ella";
            historyText += `[${sender}]: ${item.text}\\n\\n`;
        });
        
        const blob = new Blob([historyText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `historial_chat.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
"""
content = content.replace("function saveState() {", download_history_fn + "\n    function saveState() {")

# 7. Button listeners binding (ensure btn-send calls evaluateSelection)
# It's currently in window.onload: document.getElementById('btn-send').addEventListener('click', evaluateSelection);
# I should ensure there is no conflict. It should still work.

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("HTML modified successfully.")
