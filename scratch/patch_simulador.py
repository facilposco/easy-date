import os

def patch_html():
    source = "simulador_v1.0.html"
    target = "simulador_v2.0.html"
    
    with open(source, "r", encoding="utf-8") as f:
        html = f.read()
        
    # Inyectamos el textarea en el options-container y cambiamos el estilo.
    # Pero lo más limpio es inyectar un nuevo script al final del body que haga monkey-patching.
    
    patch_script = """
    <!-- FASE 2: PATCH DE RESPUESTA LIBRE CON RAG -->
    <style>
        #free-text-area {
            width: 100%;
            height: 100px;
            background-color: #2b2b2b;
            color: #fff;
            border: 1px solid #444;
            border-radius: 8px;
            padding: 10px;
            font-size: 1rem;
            resize: none;
            margin-bottom: 15px;
            font-family: inherit;
        }
        #free-text-area:focus {
            outline: none;
            border-color: #ff3366;
        }
        .rag-loading {
            color: #ff3366;
            font-size: 0.9rem;
            text-align: center;
            display: none;
            margin-bottom: 10px;
        }
    </style>
    <script>
        // Monkey-patching renderStep
        const originalRenderStep = window.renderStep || renderStep;
        
        renderStep = function() {
            // Llama al original para actualizar barras, chats de la chica, etc.
            originalRenderStep();
            
            // Reemplaza las opciones por el textarea
            const container = document.getElementById('options-container');
            container.innerHTML = `
                <textarea id="free-text-area" placeholder="Escribe tu respuesta libre aquí..."></textarea>
                <div class="rag-loading" id="rag-loading">Natalia está analizando tu respuesta...</div>
            `;
            
            // Cambiar comportamiento del botón Enviar
            const btnSend = document.getElementById('btn-send');
            const newBtn = btnSend.cloneNode(true); // Remover event listeners
            btnSend.parentNode.replaceChild(newBtn, btnSend);
            
            newBtn.addEventListener('click', evaluateFreeText);
        };
        
        async function evaluateFreeText() {
            const textarea = document.getElementById('free-text-area');
            const userInput = textarea.value.trim();
            if(!userInput) {
                alert("Debes escribir algo antes de enviar.");
                return;
            }
            
            const btnSend = document.getElementById('btn-send');
            const loader = document.getElementById('rag-loading');
            
            btnSend.disabled = true;
            loader.style.display = 'block';
            
            const currentLevel = gameData.levels[gameState.level_index];
            const profile = currentLevel.girl_name === "Natalia" ? "coqueta" : 
                           (currentLevel.girl_name === "Sofía" ? "ocupada" : "indecisa");
            
            // Recopilar historial
            let historyStr = gameState.history.map(h => 
                (h.sender === 'ella' ? "Ella: " : "Tú: ") + h.text
            ).join("\\n");
            
            try {
                const response = await fetch('/evaluate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_input: userInput,
                        girl_profile: profile,
                        context_history: historyStr
                    })
                });
                
                const result = await response.json();
                
                if(response.ok) {
                    loader.style.display = 'none';
                    
                    // Actualizar chat con lo que el usuario escribió
                    addMessageToChat(userInput, 'yo');
                    
                    // Actualizar barra de vida
                    const impact = result.investment_impact || 0;
                    gameState.attraction = Math.max(0, Math.min(100, gameState.attraction + impact));
                    document.getElementById('attraction-fill').style.width = gameState.attraction + '%';
                    
                    // Mostrar feedback del coach
                    showCoachFeedback(result.analysis_feedback + "<br><br><b>Impacto:</b> " + (impact > 0 ? "+"+impact : impact), impact > 0);
                    
                    // Añadir respuesta de la chica al historial pero no renderizar aún hasta que el usuario cierre el feedback (o renderizar en el siguiente paso)
                    // Para simplificar, lo añadiremos directo al chat
                    setTimeout(() => {
                        addMessageToChat(result.her_response, 'ella');
                        // Scroll down
                        const cb = document.getElementById('chat-box');
                        cb.scrollTop = cb.scrollHeight;
                    }, 1500);
                    
                } else {
                    alert("Error en la evaluación RAG: " + result.error);
                    btnSend.disabled = false;
                    loader.style.display = 'none';
                }
            } catch(e) {
                alert("Error de conexión con el backend.");
                btnSend.disabled = false;
                loader.style.display = 'none';
            }
        }
    </script>
    </body>
    """
    
    html = html.replace("</body>", patch_script)
    
    with open(target, "w", encoding="utf-8") as f:
        f.write(html)
        
    print(f"Parche aplicado. Archivo generado: {target}")

if __name__ == "__main__":
    patch_html()
