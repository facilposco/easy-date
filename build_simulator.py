import os
import json
import base64
import sys
import subprocess
from io import BytesIO
from PIL import Image

MOJIBAKE_REPLACEMENTS = {
    "Ã¡": "á", "Ã©": "é", "Ã­": "í", "Ã³": "ó", "Ãº": "ú",
    "Ã": "Á", "Ã‰": "É", "Ã": "Í", "Ã“": "Ó", "Ãš": "Ú",
    "Ã±": "ñ", "Ã‘": "Ñ", "Ã¼": "ü",
    "Â¿": "¿", "Â¡": "¡", "Â«": "«", "Â»": "»", "Âº": "º", "Âª": "ª",
    "â€”": "-", "â€“": "-", "â€˜": "'", "â€™": "'", "â€œ": '"', "â€": '"',
    "â¤ï¸": "❤️", "ðŸ’”": "💔", "ðŸ“š": "📚", "ðŸŽ®": "🎮",
    "ðŸ’¬": "💬", "ðŸ’‹": "💋", "ðŸ‘": "👍", "ðŸ†": "🏆", "ðŸ‘‘": "👑",
    "ðŸ·": "🍷", "ðŸŒŸ": "🌟", "â±ï¸": "⏱️", "âœ…": "✅",
    "âŒ": "❌", "âž”": "➔", "âŸ³": "↻", "â–²": "▲", "â–¼": "▼",
    "ðŸ˜‰": "😉", "ðŸ˜": "😍", "ðŸ˜‚": "😂", "ðŸ˜‡": "😇", "ðŸ¤”": "🤔",
    "ðŸ¥º": "🥺", "ðŸ’¸": "💸",
}

def repair_mojibake_text(value):
    """Repara texto UTF-8 leido accidentalmente como Windows-1252."""
    if not isinstance(value, str):
        return value
    try:
        fixed = value.encode("cp1252").decode("utf-8")
    except UnicodeError:
        fixed = value
    for bad, good in MOJIBAKE_REPLACEMENTS.items():
        fixed = fixed.replace(bad, good)
    if "2 dias" in fixed:
        fixed = fixed.replace("2 dias", "2 días")
    if "TardÃ³" in fixed:
        fixed = fixed.replace("TardÃ³", "Tardó")
    return fixed

def repair_mojibake(value):
    if isinstance(value, dict):
        return {k: repair_mojibake(v) for k, v in value.items()}
    if isinstance(value, list):
        return [repair_mojibake(item) for item in value]
    return repair_mojibake_text(value)

def image_to_base64(filepath):
    try:
        if not os.path.exists(filepath):
            return ""
        with Image.open(filepath) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            # Los avatares del simulador son pequeÃ±os cÃ­rculos de visualizaciÃ³n. 300px de ancho es mÃ¡s que suficiente.
            max_width = 300
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_height = int((float(img.height) * float(ratio)))
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=55, optimize=True)
            encoded_string = base64.b64encode(buffer.getvalue()).decode("utf-8")
            return f"data:image/jpeg;base64,{encoded_string}"
    except Exception as e:
        print(f"Error loading/compressing image {filepath}: {e}")
        return ""

def main():
    project_root = os.path.dirname(os.path.abspath(__file__))
    print("Compilando el manual de casos reales...")
    try:
        # Intentamos compilar el HTML de casos reales si existe
        if os.path.exists("compile_html.py"):
            subprocess.run([sys.executable, "compile_html.py"], check=True)
    except Exception as e:
        print(f"Advertencia: no se pudo compilar compile_html.py ({e}). Continuando...")

    # Rutas base
    brain_dir = r"C:\Users\New\.gemini\antigravity\brain"
    conv_id = "6d7e91e0-a1e2-4881-b3d2-a9f502488a7a"
    
    css_path = os.path.join(project_root, "scratch", "game_styles.css")
    json_path = os.path.join(project_root, "scratch", "game_dialogues.json")
    cases_html_path = os.path.join(project_root, "estudio_textgame_casos_reales.html")
    
    # Base64 encode cases HTML
    cases_base64 = ""
    try:
        if os.path.exists(cases_html_path):
            with open(cases_html_path, "r", encoding="utf-8") as f:
                cases_html_content = f.read()
            cases_base64 = base64.b64encode(cases_html_content.encode("utf-8")).decode("utf-8")
            print("Dashboard de Casos Reales codificado exitosamente en Base64.")
        else:
            print("Error: No se encontrÃ³ estudio_textgame_casos_reales.html")
    except Exception as e:
        print(f"Error cargando casos reales HTML: {e}")

    # Check what images exist in the conv_id folder
    conv_folder = os.path.join(brain_dir, conv_id)
    files = os.listdir(conv_folder) if os.path.exists(conv_folder) else []
    
    coach_img = ""
    level_imgs = ["", "", "", ""]
    
    for f in files:
        if f.startswith("avatar_coach_") and f.endswith(".png"):
            coach_img = image_to_base64(os.path.join(conv_folder, f))
        elif f.startswith("avatar_level_1_") and f.endswith(".png"):
            level_imgs[0] = image_to_base64(os.path.join(conv_folder, f))
        elif f.startswith("avatar_level_2_") and f.endswith(".png"):
            level_imgs[1] = image_to_base64(os.path.join(conv_folder, f))
        elif f.startswith("avatar_level_3_") and f.endswith(".png"):
            level_imgs[2] = image_to_base64(os.path.join(conv_folder, f))
        elif f.startswith("avatar_level_4_") and f.endswith(".png"):
            level_imgs[3] = image_to_base64(os.path.join(conv_folder, f))
            
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            css_content = f.read()
    except Exception as e:
        print(f"Error css: {e}")
        css_content = ""
        
    try:
        with open(json_path, "r", encoding="utf-8-sig") as f:
            game_data = json.load(f)
            game_data = repair_mojibake(game_data)
    except Exception as e:
        print(f"Error json: {e}")
        game_data = {}

    # JavaScript code template
    js_template = """
    const gameData = __GAME_DATA__;
    const levelAvatars = __LEVEL_AVATARS__;
    const coachAvatar = "__COACH_AVATAR__";
    const studyCasesBase64 = "__STUDY_CASES_BASE64__";
    
    // Ticks de tiempo actualizados
    const TIME_TICKS = ["Ahora mismo", "15m", "1h", "2h", "4h", "12h", "24h", "2 días"];
    
    let gameState = {
        level_index: 0,
        step_index: 0,
        lives: 4,
        attraction: 50,
        history: [],
        locked: false,
        replyMode: 'free',
        selectedTimeIndex: null,
        stats: { good: 0, bad: 0, turns: [] }
    };
    
    const levelLivesMap = { 0: 4, 1: 3, 2: 2, 3: 1 };
    
    function saveState() {
        ensureStatsShape();
        const stateToSave = { ...gameState, locked: false };
        localStorage.setItem('easyDateState', JSON.stringify(stateToSave));
    }

    function ensureStatsShape() {
        if (!gameState.stats) gameState.stats = { good: 0, bad: 0, turns: [] };
        if (!Array.isArray(gameState.stats.turns)) gameState.stats.turns = [];
    }
    
    function resetGame() {
        localStorage.removeItem('easyDateState');
        gameState = {
            level_index: 0,
            step_index: 0,
            lives: levelLivesMap[0],
            attraction: 50,
            history: [],
            locked: false,
            replyMode: 'free',
            selectedTimeIndex: null,
            stats: { good: 0, bad: 0, turns: [] }
        };
        document.getElementById('chat-area').innerHTML = '';
        saveState();
        renderStep();
        showMatchModal();
    }
    
    function showMatchModal() {
        const level = gameData.levels[gameState.level_index];
        document.getElementById('match-girl-name').innerText = level.girl_name;
        document.getElementById('match-level-title').innerText = level.name;
        document.getElementById('match-girl-img').style.backgroundImage = `url("${levelAvatars[gameState.level_index]}")`;
        setInputLocked(true);
        document.getElementById('match-modal').classList.add('active');
        playSound('match');
    }
    
    function startLevel() {
        document.getElementById('match-modal').classList.remove('active');
        // Inicializar vidas del nivel
        gameState.lives = levelLivesMap[gameState.level_index];
        gameState.attraction = 50;
        gameState.step_index = 0;
        gameState.locked = false;
        gameState.stats = { good: 0, bad: 0, turns: [] };
        document.getElementById('chat-area').innerHTML = '';
        saveState();
        renderStep();
    }
    
    function renderStep() {
        ensureStatsShape();
        const level = gameData.levels[gameState.level_index];
        const step = level.steps[gameState.step_index];
        
        // Actualizar UI de cabecera
        const profileName = document.getElementById('chat-profile-name');
        const profileAvatar = document.getElementById('chat-profile-avatar');
        if (profileName) profileName.innerText = level.girl_name || 'Natalia';
        if (profileAvatar) profileAvatar.style.backgroundImage = `url("${levelAvatars[gameState.level_index]}")`;
        document.getElementById('level-progress-display').innerText = `Nivel ${level.level_id || gameState.level_index + 1} · Paso ${gameState.step_index + 1} de ${level.steps.length}`;
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
            input.addEventListener('change', () => {
                const freeInput = document.getElementById('free-reply-input');
                if (freeInput) {
                    freeInput.value = '';
                }
            });
            label.addEventListener('click', () => {
                if (gameState.locked || gameState.replyMode !== 'guided') return;
                input.checked = true;
                const freeInput = document.getElementById('free-reply-input');
                if (freeInput) freeInput.value = '';
                setTimeout(() => evaluateSelection(), 0);
            });
            
            const card = document.createElement('span');
            card.className = 'card-content';
            card.innerHTML = `<span class="letter">${letter}</span> <span class="text-content">${opt.text}</span>`;
            
            label.appendChild(input);
            label.appendChild(card);
            optsGrid.appendChild(label);
        });
        
        setInputLocked(false);
        clearTimeSelection();
        const freeInput = document.getElementById('free-reply-input');
        if (freeInput) freeInput.value = '';
        updateReplyModeUI();
    }

    function updateReplyModeUI() {
        const isFree = gameState.replyMode !== 'guided';
        const freeComposer = document.getElementById('free-composer');
        const guidedComposer = document.getElementById('guided-composer');
        const freeBtn = document.getElementById('mode-free');
        const guidedBtn = document.getElementById('mode-guided');
        if (freeComposer) freeComposer.style.display = isFree ? 'block' : 'none';
        if (guidedComposer) guidedComposer.style.display = isFree ? 'none' : 'block';
        if (freeBtn) freeBtn.classList.toggle('active', isFree);
        if (guidedBtn) guidedBtn.classList.toggle('active', !isFree);
        if (freeBtn) freeBtn.setAttribute('aria-pressed', String(isFree));
        if (guidedBtn) guidedBtn.setAttribute('aria-pressed', String(!isFree));
    }

    function setReplyMode(mode) {
        if (gameState.locked) return;
        gameState.replyMode = mode === 'guided' ? 'guided' : 'free';
        if (gameState.replyMode === 'free') {
            document.querySelectorAll('input[name="reply_opt"]').forEach((input) => {
                input.checked = false;
            });
        } else {
            const freeInput = document.getElementById('free-reply-input');
            if (freeInput) freeInput.value = '';
        }
        saveState();
        updateReplyModeUI();
    }

    function setInputLocked(isLocked) {
        gameState.locked = isLocked;
        const btnSend = document.getElementById('btn-send');
        const btnReset = document.getElementById('btn-reset');
        const btnStudy = document.getElementById('btn-study');
        const timeSlider = document.getElementById('time-slider');
        const freeInput = document.getElementById('free-reply-input');
        const modeFree = document.getElementById('mode-free');
        const modeGuided = document.getElementById('mode-guided');
        const options = document.querySelectorAll('input[name="reply_opt"]');
        const emojiButtons = document.querySelectorAll('.emoji-chip');
        [btnSend, btnReset, btnStudy, timeSlider, freeInput, modeFree, modeGuided].forEach((el) => {
            if (el) el.disabled = isLocked;
        });
        options.forEach((input) => input.disabled = isLocked);
        emojiButtons.forEach((button) => button.disabled = isLocked);
        if (btnSend) btnSend.style.opacity = isLocked ? '0.5' : '1';
        if (!isLocked && btnSend && /pensando/i.test(btnSend.innerText || '')) {
            btnSend.innerText = 'Enviar';
        }
    }

    function hasActiveBlockingModal() {
        return ['modal-overlay', 'gameover-modal', 'levelup-modal', 'match-modal', 'final-modal', 'help-modal']
            .some((id) => {
                const el = document.getElementById(id);
                return el && el.classList.contains('active');
            });
    }

    function insertEmoji(emoji) {
        if (gameState.locked) return;
        const input = document.getElementById('free-reply-input');
        if (!input) return;
        const start = input.selectionStart ?? input.value.length;
        const end = input.selectionEnd ?? input.value.length;
        const prefix = input.value.slice(0, start);
        const suffix = input.value.slice(end);
        const needsSpaceBefore = prefix && !/\\s$/.test(prefix) ? ' ' : '';
        const needsSpaceAfter = suffix && !/^\\s/.test(suffix) ? ' ' : '';
        input.value = `${prefix}${needsSpaceBefore}${emoji}${needsSpaceAfter}${suffix}`;
        const cursor = (prefix + needsSpaceBefore + emoji).length + needsSpaceAfter.length;
        input.focus();
        input.setSelectionRange(cursor, cursor);
    }

    function insertGifCue() {
        insertEmoji('[GIF: risa]');
    }

    function clearTimeSelection() {
        gameState.selectedTimeIndex = null;
        const slider = document.getElementById('time-slider');
        const display = document.getElementById('slider-time-display');
        const selector = document.querySelector('.time-selector');
        if (slider) {
            slider.value = 0;
            slider.dataset.selected = 'false';
        }
        if (display) display.innerText = 'Toca para seleccionar';
        if (selector) {
            selector.classList.add('time-unselected');
            selector.classList.remove('time-selected');
        }
    }

    function setSelectedTimeIndex(index) {
        const slider = document.getElementById('time-slider');
        const display = document.getElementById('slider-time-display');
        const selector = document.querySelector('.time-selector');
        const safeIndex = Math.max(0, Math.min(TIME_TICKS.length - 1, Number(index || 0)));
        gameState.selectedTimeIndex = safeIndex;
        if (slider) {
            slider.value = safeIndex;
            slider.dataset.selected = 'true';
        }
        if (display) display.innerText = `Rango seleccionado: ${TIME_TICKS[safeIndex]}`;
        if (selector) {
            selector.classList.remove('time-unselected');
            selector.classList.add('time-selected');
        }
    }
    
    function updateTopBarStats() {
        // Vidas
        let hearts = "";
        for (let i = 0; i < gameState.lives; i++) {
            hearts += "â¤ï¸";
        }
        if (hearts === "") hearts = "ðŸ’”";
        document.getElementById('rank-display').innerText = `Vidas: ${hearts}`;
        
        // Barra de atracciÃ³n
        document.getElementById('calibration-text').innerText = `AtracciÃ³n: ${gameState.attraction}%`;
        const barFill = document.getElementById('calibration-bar-fill');
        barFill.style.width = `${gameState.attraction}%`;
        
        // Color segÃºn rango
        if (gameState.attraction >= 70) {
            barFill.style.backgroundColor = '#10b981';
        } else if (gameState.attraction >= 40) {
            barFill.style.backgroundColor = '#f59e0b';
        } else {
            barFill.style.backgroundColor = '#ef4444';
        }
    }
    
    function normalizeReply(text) {
        return (text || '')
            .toLowerCase()
            .normalize('NFD')
            .replace(/[\\u0300-\\u036f]/g, '')
            .replace(/[^a-z0-9ñ\\s]/g, ' ')
            .replace(/\\s+/g, ' ')
            .trim();
    }

    function similarityScore(a, b) {
        const left = new Set(normalizeReply(a).split(' ').filter((word) => word.length > 2));
        const right = new Set(normalizeReply(b).split(' ').filter((word) => word.length > 2));
        if (!left.size || !right.size) return 0;
        let overlap = 0;
        left.forEach((word) => {
            if (right.has(word)) overlap += 1;
        });
        return overlap / Math.max(left.size, right.size);
    }

    function evaluateFreeReply(step, replyText) {
        const correct = (step.options || []).find((opt) => opt.is_correct) || {};
        const normalizedReply = normalizeReply(replyText);
        const normalizedCorrect = normalizeReply(correct.text || '');
        const exactOrContained = normalizedReply === normalizedCorrect ||
            normalizedReply.includes(normalizedCorrect) ||
            normalizedCorrect.includes(normalizedReply);
        const isClose = similarityScore(replyText, correct.text || '') >= 0.55;
        return {
            text: replyText,
            is_correct: exactOrContained || isClose,
            reference_text: correct.text || ''
        };
    }

    function apiEndpoint() {
        if (location.port === '8000') return '/api/simulate-turn';
        return 'http://127.0.0.1:8000/api/simulate-turn';
    }

    function buildVisibleContext(step) {
        const lastNatalia = [...gameState.history].reverse().find((turn) => turn.sender === 'her');
        const lastUser = [...gameState.history].reverse().find((turn) => turn.sender === 'user');
        const snapshot = gameState.history
            .slice(-8)
            .map((turn) => `${turn.sender === 'her' ? 'Natalia' : 'Hombre'}: ${turn.text}`)
            .join('\\n');
        return {
            evaluated_step_id: step ? step.step_id : null,
            evaluated_step_index: gameState.step_index,
            last_natalia_message: lastNatalia ? lastNatalia.text : '',
            last_user_message: lastUser ? lastUser.text : '',
            chat_snapshot: snapshot
        };
    }

    function formatMessageTime(sender, timeText) {
        const raw = String(timeText || '').trim();
        if (/^tard/i.test(raw)) return raw;
        const label = sender === 'user' ? 'Tardaste' : 'Tardó';
        return `${label}: ${raw || '15 min'}`;
    }

    function appendUserMessage(text, chosenTime) {
        const chatArea = document.getElementById('chat-area');
        const userMsg = document.createElement('div');
        userMsg.className = 'message user';
        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.appendChild(document.createTextNode(text));
        const time = document.createElement('span');
        time.className = 'message-time-highlight';
        time.innerText = `(${formatMessageTime('user', chosenTime)})`;
        bubble.appendChild(document.createElement('br'));
        bubble.appendChild(time);
        userMsg.appendChild(bubble);
        chatArea.appendChild(userMsg);
    }

    function appendNataliaMessage(text, timeText) {
        const level = gameData.levels[gameState.level_index];
        const chatArea = document.getElementById('chat-area');
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message her';

        const avaDiv = document.createElement('div');
        avaDiv.className = 'avatar';
        avaDiv.style.backgroundImage = `url("${levelAvatars[gameState.level_index]}")`;
        avaDiv.addEventListener('click', () => openLightbox(levelAvatars[gameState.level_index]));

        const bubDiv = document.createElement('div');
        bubDiv.className = 'bubble';
        bubDiv.appendChild(document.createTextNode(text));
        const time = document.createElement('span');
        time.className = 'message-time-highlight';
        time.innerText = `(${formatMessageTime('her', timeText)})`;
        bubDiv.appendChild(document.createElement('br'));
        bubDiv.appendChild(time);

        msgDiv.appendChild(avaDiv);
        msgDiv.appendChild(bubDiv);
        chatArea.appendChild(msgDiv);
    }

    function mockSimulationTurn(payload) {
        return localEmergencySimulationTurn(payload, null);
    }

    function localEmergencySimulationTurn(payload, error) {
        const message = (payload.user_message || '').trim();
        const lowered = message.toLowerCase();
        const history = payload.history || [];
        const lastNatalia = [...history].reverse().find((turn) => turn.sender === 'her');
        const lastNataliaText = payload.visible_context?.last_natalia_message || lastNatalia?.text || '';
        let score = 6;
        let reason = 'conecta con el contexto visible, pero puede ser mas especifico y jugueton.';

        if (lastNataliaText.includes('?') && (message.length < 8 || /^(hola|hey|ok|si|no)$/i.test(message))) {
            score = 3;
            reason = 'no responde realmente a lo que Natalia acaba de preguntar.';
        } else if (message.length < 8) {
            score = 3;
            reason = 'la respuesta es demasiado corta y le deja todo el trabajo a Natalia.';
        } else if (/numero|whatsapp|tel[eé]fono|celular/.test(lowered) && payload.step_index < 6) {
            score = 4;
            reason = 'pedir el contacto tan pronto puede sentirse apresurado.';
        } else if (/casa|hotel|sexo|cama/.test(lowered)) {
            score = 2;
            reason = 'el mensaje sube la intensidad demasiado rapido para este nivel.';
        } else if (/[?¿]/.test(message) && message.length <= 140) {
            score = 7;
            reason = 'hace avanzar la conversacion con una pregunta facil de responder.';
        }

        const nataliaMessage = buildEmergencyNataliaReply(message, lowered, payload, lastNatalia);
        return Promise.resolve({
            natalia_message: nataliaMessage,
            natalia_time: 'Tardó: 15 min',
            coach_title: score >= 8 ? 'Buena respuesta' : score >= 6 ? 'Respuesta aceptable' : 'Respuesta incorrecta',
            coach_feedback: [
                `${score < 5 ? 'Mensaje falla por' : 'Mensaje'}: ${reason}`,
                '',
                `Tiempo de respuesta: ${payload.chosen_time || 'no indicado'}. Evita responder de inmediato si ella tardó más.`,
                '',
                `Objetivo: ${inferStepObjective(gameData.levels[payload.level - 1]?.steps[payload.step_index] || {})}.`,
                '',
                'Sugerencias:',
                'A. Responde a lo último que ella dijo con una frase corta y concreta.',
                'B. Agrega un toque de humor ligero antes de preguntar algo nuevo.',
                'C. Si ya hay buena energia, avanza suavemente hacia un plan.'
            ].join('\\n'),
            score,
            lose_life: score < 5,
            attraction_delta: score >= 8 ? 8 : score >= 6 ? 4 : -10,
            suggestions: [
                'Responde a lo último que ella dijo con una frase corta y concreta.',
                'Agrega un toque de humor ligero antes de preguntar algo nuevo.',
                'Si ya hay buena energia, avanza suavemente hacia un plan.'
            ],
            fallback: true,
            error: error ? String(error.message || error) : ''
        });
    }

    function buildEmergencyNataliaReply(message, lowered, payload, lastNatalia) {
        const lastText = payload.visible_context?.last_natalia_message || lastNatalia?.text || '';
        const lastLower = lastText.toLowerCase();
        if (lastText.includes('?') && (message.length < 8 || /^(hola|hey|ok|si|no)$/i.test(message))) {
            return 'jaja respondiste, pero me dejaste la pregunta en el aire.';
        }
        if (/numero|whatsapp|tel[eé]fono|celular/.test(lowered)) {
            return payload.attraction >= 65 || payload.step_index >= 7
                ? 'Mmm, va... pero usalo bien. Si el plan es bueno, te respondo 😉'
                : 'Jajaja vas un poco rapido, primero convenceme de que no eres aburrido.';
        }
        if (/entrevista/.test(lowered)) {
            return 'Eso me gusta. Odio cuando el chat parece formulario, prefiero algo con chispa.';
        }
        if (/semana|d[ií]a|que tal|qué tal|c[oó]mo va/.test(lowered)) {
            return 'Mi semana va bien, algo movida pero llevadera. ¿La tuya va con mucho caos o todo bajo control?';
        }
        if (/caf[eé]/.test(lowered)) {
            if (lastLower.includes('caf')) {
                return 'Jaja ok, entonces ya te puse tarea: quiero nombre del lugar y por qué vale la pena.';
            }
            return 'Ok, señor experto en cafés, ahora necesito saber si tu recomendación es de verdad buena.';
        }
        if (/m[uú]sica|canci[oó]n|playlist|bailar|reggaeton|salsa/.test(lowered)) {
            return 'Me gusta la música con buena energía, pero depende del mood. ¿Tú eres más de bailar o de escuchar tranquilo?';
        }
        if (/comida|comer|restaurante|sushi|pizza|tacos|postre/.test(lowered)) {
            return 'Me gusta comer rico sin hacerlo complicado. Si eliges buen lugar, eso suma puntos jaja.';
        }
        if (/viaje|viajar|playa|monta[ñn]a|vacaciones/.test(lowered)) {
            return 'Me gustan los viajes con plan, pero dejando espacio para improvisar. ¿Tú eres más playa o ciudad?';
        }
        if (/perro|perros|gato|gatos|mascota|mascotas/.test(lowered)) {
            return 'Me gustan, pero necesito ver si tu mascota aprueba mi filtro también jaja. ¿Tienes perro o gato?';
        }
        if (/familia|hermano|hermana|mam[aá]|pap[aá]/.test(lowered)) {
            return 'Soy cercana con mi gente, pero no soy de contar toda mi vida en el primer chat. ¿Tú cómo eres con tu familia?';
        }
        if (/(trato hecho|te escribo|lo cuadramos|sin discurso|listo)/.test(lowered) && (/whatsapp|usalo/.test(lastLower) || payload.step_index >= 8)) {
            return 'Jaja bien, así sí. Me gusta cuando el plan queda claro sin tanta vuelta.';
        }
        if (/bogot[aá]|vivo|trabaj/.test(lowered)) {
            if (/trabaj/.test(lowered) && /bogot[aá]|vivo/.test(lowered)) {
                return 'Jaja Bogotá me queda claro. Hago marketing visual para restaurantes; ahora dime qué haces fuera de rutina.';
            }
            if (/d[oó]nde|vives|eres de/.test(lastLower)) {
                return 'Ok, eso me ubica. Y cuando no estás trabajando, ¿qué plan te gusta?';
            }
            return 'Jaja Bogotá tiene su encanto. Yo hago marketing visual para restaurantes, pero me interesa más saber cómo te diviertes.';
        }
        if (/vino|copa|salir|plan|cita/.test(lowered)) {
            if (payload.step_index >= 8 || payload.attraction >= 80) {
                return 'Ok, eso ya suena a plan real. Te paso mi WhatsApp y lo cuadramos.';
            }
            if (/jueves|viernes|s[aá]bado|domingo|lunes|martes|mi[eé]rcoles/.test(lowered)) {
                return 'Jueves puede funcionar. Me gusta que lo aterrices sin hacerlo intenso.';
            }
            if (payload.step_index >= 6) {
                return 'Mmm me gusta. ¿Y qué día dices tú?';
            }
            if (/vino|plan/.test(lastLower)) {
                return 'Jaja eso sí suena más interesante. ¿Qué tienes en mente?';
            }
            if (/energ[ií]a/.test(lastLower)) {
                return 'Jaja vas vendiendo el plan poco a poco, eso me gusta.';
            }
            return 'Eso suena mejor. Me gustan los planes simples cuando la conversación tiene buena energía.';
        }
        if (/zona/.test(lowered)) {
            return 'Por Brickell puede ser. Ahora dime qué lugar tienes en mente.';
        }
        if (/lugar/.test(lowered)) {
            return 'Me gusta que lo concretes. Dime el lugar y te digo si pasa mi filtro jaja.';
        }
        if (/gym|gimnas|entren/.test(lowered)) {
            return 'Me gusta esa disciplina, aunque espero que no hables solo de rutina y proteína jaja.';
        }
        if (lastNatalia && lastNatalia.text) {
            return 'Jaja ok, eso me da curiosidad. Cuéntame un poco más, pero sin hacerlo entrevista.';
        }
        return 'Jaja, eso estuvo mejor. Sigue, quiero ver si de verdad tienes buena conversación.';
    }

    async function requestSimulationTurn(payload) {
        if (window.easyDateForceMockApi) return mockSimulationTurn(payload);
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 18000);
        try {
            const response = await fetch(apiEndpoint(), {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            if (!response.ok) {
                throw new Error(`Backend IA respondió ${response.status}`);
            }
            return response.json();
        } catch (error) {
            console.warn('Natalia IA fallback local:', error);
            return localEmergencySimulationTurn(payload, error);
        } finally {
            clearTimeout(timeoutId);
        }
    }

    async function evaluateSelection() {
        if (gameState.locked || document.getElementById('modal-overlay').classList.contains('active')) {
            return;
        }
        const timeSlider = document.getElementById('time-slider');
        if (!timeSlider || timeSlider.dataset.selected !== 'true') {
            alert("Selecciona cuánto tardas en responder antes de enviar.");
            if (timeSlider) timeSlider.focus();
            return;
        }
        const sliderVal = parseInt(timeSlider.value);
        const chosenTime = TIME_TICKS[sliderVal];
        
        const level = gameData.levels[gameState.level_index];
        const step = level.steps[gameState.step_index];
        let opt = null;
        const freeInput = document.getElementById('free-reply-input');
        const replyText = (freeInput ? freeInput.value : '').trim();
        if (replyText) {
            opt = evaluateFreeReply(step, replyText);
        } else if (gameState.replyMode === 'guided') {
            const selected = document.querySelector('input[name="reply_opt"]:checked');
            if(!selected) {
                alert("Escribe tu respuesta o toca una sugerencia primero");
                return;
            }
            opt = JSON.parse(selected.value);
        } else {
            alert("Escribe tu respuesta primero");
            if (freeInput) freeInput.focus();
            return;
        }
        const evaluatedLevelIndex = gameState.level_index;
        const evaluatedStepIndex = gameState.step_index;
        const evaluatedStepId = step.step_id;
        setInputLocked(true);
        const btnSend = document.getElementById('btn-send');
        const originalSendText = btnSend ? btnSend.innerText : '';
        if (btnSend) btnSend.innerText = 'Natalia está pensando...';

        appendUserMessage(opt.text, chosenTime);
        
        gameState.history.push({
            sender: 'user', 
            text: opt.text, 
            timeText: chosenTime, 
            levelIndex: gameState.level_index
        });
        saveState();
        scrollToBottom();

        let payload = {
            level: gameState.level_index + 1,
            step_index: gameState.step_index,
            evaluated_step_id: evaluatedStepId,
            lives: gameState.lives,
            attraction: gameState.attraction,
            history: gameState.history,
            user_message: opt.text,
            chosen_time: chosenTime,
            visible_context: buildVisibleContext(step)
        };
        let simulation = null;
        try {
            simulation = await requestSimulationTurn(payload);
        } catch (error) {
            simulation = await localEmergencySimulationTurn(payload, error);
        } finally {
            if (btnSend) btnSend.innerText = originalSendText;
        }

        const score = Number(simulation.score || 5);
        const loseLife = Boolean(simulation.lose_life);
        const attractionDelta = Number(simulation.attraction_delta || 0);
        gameState.attraction = Math.max(0, Math.min(100, gameState.attraction + attractionDelta));
        if (loseLife) {
            gameState.lives -= 1;
            gameState.stats.bad += 1;
        } else {
            gameState.stats.good += 1;
        }
        recordTurnTelemetry(opt.text, score, loseLife, simulation.coach_feedback || '');
        updateTopBarStats();
        const feedbackTitle = simulation.coach_title || (score >= 6 ? "Respuesta aceptable" : "Respuesta incorrecta");
        const feedbackText = {
            raw: simulation.coach_feedback || "Natalia-Coach no devolvió feedback.",
            metrics: simulation.turn_metrics || null,
            suggestions: Array.isArray(simulation.suggestions) ? simulation.suggestions : [],
            step,
            chosenTime
        };
        const audioType = score >= 8 ? "success" : score >= 6 ? "warning" : "error";
        
        // Mostrar Modal de Feedback del Coach
        showCoachModal(feedbackTitle, feedbackText, audioType, () => {
            if (gameState.level_index !== evaluatedLevelIndex || gameState.step_index !== evaluatedStepIndex) {
                setInputLocked(false);
                return;
            }
            if (gameState.lives <= 0) {
                showGameOverModal();
                return;
            }

            const nataliaMessage = simulation.natalia_message || "jaja ok, continúa.";
            const nataliaTime = simulation.natalia_time || "Tardó: 15 min";
            appendNataliaMessage(nataliaMessage, nataliaTime);
            gameState.history.push({
                sender: 'her',
                text: nataliaMessage,
                timeText: nataliaTime,
                levelIndex: gameState.level_index
            });

            gameState.step_index += 1;
            if (gameState.step_index < level.steps.length) {
                saveState();
                scrollToBottom();
                renderStep();
            } else {
                saveState();
                scrollToBottom();
                showLevelUpModal();
            }
        });
    }

    function inferStepObjective(step) {
        const her = (step.her_message || '').toLowerCase();
        const correct = ((step.options || []).find((opt) => opt.is_correct) || {}).text || '';
        const target = `${her} ${correct}`.toLowerCase();
        if (target.includes('número') || target.includes('whatsapp')) return 'sacar el número sin sonar necesitado';
        if (target.includes('libre') || target.includes('noches') || target.includes('botella') || target.includes('vino')) return 'mover la conversación hacia una cita concreta';
        if (target.includes('buscando') || target.includes('soltero')) return 'responder con estabilidad y mantener el marco';
        if (target.includes('dónde vives') || target.includes('brickell')) return 'mantener el juego sin convertirlo en entrevista logística';
        if (step.step_id === 1) return 'abrir con curiosidad y diferenciarte del resto';
        return 'mantener coherencia con el mensaje visible y avanzar un poco la conversación';
    }

    function buildCoachFeedback(step, opt, chosenTime, isMessageCorrect, isTimeCorrect) {
        const objective = inferStepObjective(step);
        const allowed = (step.allowed_time_indices || []).map((idx) => TIME_TICKS[idx]).join(' / ');
        const quality = isMessageCorrect
            ? step.coach_feedback_correct
            : step.coach_feedback_incorrect;
        const timing = isTimeCorrect
            ? `Tiempo elegido: ${chosenTime}. Está dentro del rango esperado (${allowed}).`
            : `Tiempo elegido: ${chosenTime}. ${step.coach_feedback_time_incorrect}`;
        const nextMove = isMessageCorrect
            ? 'Repite este patrón: poco texto, marco claro y avance suave.'
            : 'Mejor alternativa: elige una opción que responda al mensaje visible sin justificarte ni entrevistarla.';
        return [
            `Objetivo visible: ${objective}.`,
            '',
            `Calidad del mensaje: ${quality}`,
            '',
            `Contexto de la conversación: ${timing}`,
            '',
            `Siguiente ajuste: ${isMessageCorrect ? 'lo cubriste' : 'todavía falta'}; ${nextMove}`
        ].join('\\n');
    }

    function formatTurnMetricsForCoach(metrics) {
        if (!metrics || typeof metrics !== 'object') return '';
        const quality = metrics.message_quality || {};
        const context = metrics.context || {};
        const objective = metrics.objective || {};
        const tone = metrics.tone || {};
        const timing = metrics.timing || {};
        const risks = [
            `generico ${quality.generic_risk ?? '-'}/10`,
            `necesidad ${quality.neediness_risk ?? '-'}/10`,
            `sobreinversion ${quality.overinvestment_risk ?? '-'}/10`
        ].join(', ');
        const lines = [
            `Contexto: ${context.context_congruence ?? '-'} / 10`,
            `Objetivo: ${objective.intent || 'conversacion'} - avance a cita/numero: ${objective.moves_toward_contact_or_date ? 'si' : 'no'}`,
            `Riesgos: ${risks}`,
            timing.too_immediate ? 'Timing: respondiste demasiado rapido.' : ''
        ];
        if ((tone.emoji_count ?? 0) > 0 || !/sin emojis|sin lectura/i.test(tone.emoji_calibration || '')) {
            lines.splice(2, 0, `Emojis: ${tone.emoji_count ?? 0} - ${tone.emoji_calibration || 'sin lectura'}`);
        }
        return lines.filter(Boolean).join('\\n');
    }

    function stripCoachPrefix(text) {
        return String(text || '')
            .replace(/^(calidad del mensaje|mensaje falla por|mensaje|contexto de la conversación|contexto de la conversacion|tiempo elegido|tiempo de respuesta|objetivo del paso|objetivo visible|objetivo|emojis|siguiente ajuste|mejor alternativa)\\s*:\\s*/i, '')
            .trim();
    }

    function compactCoachText(text, maxLength = 142) {
        const clean = String(text || '').replace(/\\s+/g, ' ').trim();
        if (clean.length <= maxLength) return clean;
        const slice = clean.slice(0, maxLength - 3);
        const cut = slice.lastIndexOf(' ');
        return `${slice.slice(0, cut > 70 ? cut : slice.length)}...`;
    }

    function pushCoachSection(sections, key, text) {
        const clean = compactCoachText(stripCoachPrefix(text));
        if (!clean) return;
        const existing = sections.find((section) => section.key === key);
        if (existing) {
            existing.text = compactCoachText(`${existing.text} ${clean}`, 180);
        } else {
            sections.push({ key, text: clean });
        }
    }

    function parseCoachFeedback(raw) {
        const sections = [];
        const suggestions = [];
        let collectingSuggestions = false;
        String(raw || '').split('\\n').map((line) => line.trim()).filter(Boolean).forEach((line) => {
            const normalized = line.normalize('NFD').replace(/[\\u0300-\\u036f]/g, '').toLowerCase();
            if (/^(opciones mejores|podrias decir algo como|sugerencias)/i.test(line)) {
                collectingSuggestions = true;
                return;
            }
            const optionMatch = line.match(/^[A-C][\\).:-]\\s*(.+)$/i);
            if (collectingSuggestions || optionMatch) {
                const suggestion = compactCoachText(optionMatch ? optionMatch[1] : line, 120);
                if (suggestion && !suggestions.includes(suggestion)) suggestions.push(suggestion);
                return;
            }
            if (normalized.startsWith('calidad del mensaje') || normalized.startsWith('mensaje falla') || normalized.startsWith('tu mensaje')) {
                pushCoachSection(sections, 'message', line);
                return;
            }
            if (normalized.startsWith('contexto de la conversacion') || normalized.startsWith('tiempo elegido') || normalized.startsWith('tiempo de respuesta') || normalized.startsWith('timing')) {
                pushCoachSection(sections, 'time', line);
                return;
            }
            if (normalized.startsWith('emojis')) {
                const noEmojiObservation = /emojis:\\s*0\\b/i.test(line) && /sin emojis|no uso emojis|sin lectura/i.test(line);
                if (!noEmojiObservation) pushCoachSection(sections, 'emoji', line);
                return;
            }
            if (normalized.startsWith('objetivo')) {
                pushCoachSection(sections, 'objective', line);
                return;
            }
            if (normalized.startsWith('siguiente ajuste') || normalized.startsWith('mejor alternativa')) {
                const suggestion = compactCoachText(stripCoachPrefix(line), 120);
                if (suggestion && !suggestions.includes(suggestion)) suggestions.push(suggestion);
                return;
            }
            pushCoachSection(sections, 'message', line);
        });
        return { sections, suggestions };
    }

    function successfulExamplesForStep(step, explicitSuggestions) {
        const examples = [];
        const add = (text) => {
            const clean = compactCoachText(text, 115);
            if (clean && !examples.includes(clean) && examples.length < 3) examples.push(clean);
        };
        (explicitSuggestions || []).forEach(add);
        ((step || {}).options || [])
            .filter((option) => option && option.is_correct)
            .forEach((option) => add(option.text));
        [
            'Responde a lo último que ella dijo con una frase corta y concreta.',
            'Agrega humor ligero sin convertir el chat en entrevista.',
            'Si hay buena energia, avanza suave hacia un plan.'
        ].forEach(add);
        return examples.slice(0, 3);
    }

    function coachSectionMeta(key, title = '') {
        const isIncorrect = /incorrecta|error|fall/i.test(String(title || ''));
        return {
            message: { label: isIncorrect ? 'Mensaje falla por' : 'Mensaje', className: 'coach-card-message' },
            time: { label: 'Tiempo de respuesta', className: 'coach-card-time' },
            emoji: { label: 'Emojis', className: 'coach-card-emoji' },
            objective: { label: 'Objetivo', className: 'coach-card-objective' }
        }[key] || { label: 'Mensaje', className: 'coach-card-message' };
    }

    function renderCoachFeedback(payload, title = '') {
        const container = document.getElementById('coach-msg-text');
        if (!container) return;
        container.innerHTML = '';
        const data = typeof payload === 'object' && payload !== null ? payload : { raw: payload };
        const parsed = parseCoachFeedback(data.raw || '');
        const metricText = formatTurnMetricsForCoach(data.metrics);
        if (metricText) {
            parseCoachFeedback(metricText).sections.forEach((section) => pushCoachSection(parsed.sections, section.key, section.text));
        }
        const orderedKeys = ['message', 'time', 'emoji', 'objective'];
        const orderedSections = orderedKeys
            .map((key) => parsed.sections.find((section) => section.key === key))
            .filter(Boolean);
        orderedSections.forEach((section) => {
            const meta = coachSectionMeta(section.key, title);
            const card = document.createElement('section');
            card.className = `coach-feedback-card ${meta.className}`;
            const label = document.createElement('div');
            label.className = 'coach-feedback-label';
            label.textContent = meta.label;
            const text = document.createElement('p');
            text.textContent = section.text;
            card.appendChild(label);
            card.appendChild(text);
            container.appendChild(card);
        });

        const suggestions = successfulExamplesForStep(data.step, [
            ...parsed.suggestions,
            ...(Array.isArray(data.suggestions) ? data.suggestions : [])
        ]);
        if (suggestions.length) {
            const card = document.createElement('section');
            card.className = 'coach-feedback-card coach-card-suggestions';
            const label = document.createElement('div');
            label.className = 'coach-feedback-label';
            label.textContent = 'Sugerencias';
            const list = document.createElement('ol');
            suggestions.forEach((suggestion) => {
                const item = document.createElement('li');
                item.textContent = suggestion;
                list.appendChild(item);
            });
            card.appendChild(label);
            card.appendChild(list);
            container.appendChild(card);
        }
    }
    
    function showCoachModal(title, msg, audioType, onClose) {
        document.getElementById('coach-title').innerText = title;
        renderCoachFeedback(msg, title);
        
        const coachImgEl = document.getElementById('coach-img-el');
        coachImgEl.src = coachAvatar || '';
        
        const overlay = document.getElementById('modal-overlay');
        overlay.onCloseCallback = onClose;
        overlay.style.display = 'flex';
        overlay.style.pointerEvents = 'auto';
        overlay.classList.add('active');
        overlay.setAttribute('aria-hidden', 'false');
        
        playSound(audioType);

        const closeButton = document.getElementById('btn-close-modal');
        if (closeButton) {
            closeButton.disabled = false;
            setTimeout(() => closeButton.focus(), 0);
        }
    }
    
    function closeCoachModal() {
        const overlay = document.getElementById('modal-overlay');
        const wasActive = overlay.classList.contains('active');
        const callback = overlay.onCloseCallback;
        if (!wasActive && !callback) return;
        overlay.onCloseCallback = null;
        overlay.classList.remove('active');
        overlay.setAttribute('aria-hidden', 'true');
        overlay.style.display = 'none';
        overlay.style.pointerEvents = 'none';
        try {
            if (callback) callback();
        } finally {
            if (!hasActiveBlockingModal()) {
                setInputLocked(false);
            }
        }
    }

    function shortMessage(text) {
        const clean = String(text || '').replace(/\\s+/g, ' ').trim();
        return clean.length > 86 ? `${clean.slice(0, 83)}...` : clean;
    }

    function firstFeedbackLine(text) {
        return String(text || '').split('\\n').map((line) => line.trim()).find(Boolean) || 'Sin razon registrada.';
    }

    function recordTurnTelemetry(message, score, loseLife, feedback) {
        ensureStatsShape();
        gameState.stats.turns.push({
            step: gameState.step_index + 1,
            message: String(message || ''),
            score: Number(score || 0),
            loseLife: Boolean(loseLife),
            reason: firstFeedbackLine(feedback)
        });
    }

    function bestAndWorstTurns() {
        ensureStatsShape();
        const turns = [...gameState.stats.turns];
        if (!turns.length) return { best: null, worst: null };
        turns.sort((a, b) => {
            if (b.score !== a.score) return b.score - a.score;
            return Number(a.loseLife) - Number(b.loseLife);
        });
        const best = turns[0];
        turns.sort((a, b) => {
            if (a.score !== b.score) return a.score - b.score;
            return Number(b.loseLife) - Number(a.loseLife);
        });
        return { best, worst: turns[0] };
    }
    
    function levelSummaryText(passed) {
        ensureStatsShape();
        const level = gameData.levels[gameState.level_index];
        const totalSteps = (level && level.steps ? level.steps.length : 10);
        const startingLives = levelLivesMap[gameState.level_index] || gameState.lives || 0;
        const good = gameState.stats?.good || 0;
        const bad = gameState.stats?.bad || 0;
        const { best, worst } = bestAndWorstTurns();
        const livesLost = Math.max(0, startingLives - gameState.lives);
        const accuracy = totalSteps ? Math.round((good / totalSteps) * 100) : 0;
        const pattern = bad > 0
            ? 'Patron a mejorar: responde primero al mensaje visible antes de avanzar o justificarte.'
            : 'Patron fuerte: mantuviste contexto, tono ligero y avance sin sonar intenso.';
        const next = passed
            ? 'Siguiente foco: conserva esta naturalidad cuando la chica sea mas selectiva.'
            : 'Antes de repetir, estudia casos reales y compara como los hombres calibran contexto, tiempo y cierre.';
        return [
            `Resumen: ${good} buenas, ${bad} por mejorar, ${livesLost} vidas perdidas.`,
            `Precision del nivel: ${accuracy}%. Vidas restantes: ${gameState.lives}.`,
            best ? `Mejor mensaje: P${best.step} (${best.score}/10) "${shortMessage(best.message)}"` : '',
            worst ? `Mensaje a corregir: P${worst.step} (${worst.score}/10) "${shortMessage(worst.message)}"` : '',
            pattern,
            next
        ].filter(Boolean).join('\\n');
    }

    function updateLevelSummary(targetId, passed) {
        const target = document.getElementById(targetId);
        if (target) target.innerText = levelSummaryText(passed);
    }

    function showGameOverModal() {
        setInputLocked(true);
        dismissCoachOverlay();
        updateLevelSummary('gameover-summary', false);
        document.getElementById('gameover-modal').classList.add('active');
        playSound('gameover');
    }
    
    function retryLevel() {
        document.getElementById('gameover-modal').classList.remove('active');
        startLevel();
    }
    
    function showLevelUpModal() {
        const level = gameData.levels[gameState.level_index];
        dismissCoachOverlay();
        document.getElementById('levelup-girl-name').innerText = level.girl_name;
        document.getElementById('levelup-girl-img').style.backgroundImage = `url("${levelAvatars[gameState.level_index]}")`;
        updateLevelSummary('levelup-summary', true);
        setInputLocked(true);
        document.getElementById('levelup-modal').classList.add('active');
        
        // Activar serpentinas
        startCelebrationConfetti();
        playSound('levelup');
    }
    
    function nextLevel() {
        // Detener serpentinas
        stopCelebrationConfetti();
        document.getElementById('levelup-modal').classList.remove('active');
        
        gameState.level_index += 1;
        if (gameState.level_index < gameData.levels.length) {
            showMatchModal();
        } else {
            showFinalWinModal();
        }
    }
    
    function showFinalWinModal() {
        setInputLocked(true);
        document.getElementById('final-modal').classList.add('active');
        playSound('levelup');
    }

    function dismissCoachOverlay() {
        const overlay = document.getElementById('modal-overlay');
        if (!overlay) return;
        overlay.onCloseCallback = null;
        overlay.classList.remove('active');
        overlay.setAttribute('aria-hidden', 'true');
        overlay.style.display = 'none';
        overlay.style.pointerEvents = 'none';
    }
    
    function scrollToBottom() {
        const chatArea = document.getElementById('chat-area');
        chatArea.scrollTop = chatArea.scrollHeight;
    }
    
    function scrollChat(direction) {
        const chatArea = document.getElementById('chat-area');
        const scrollAmount = 150;
        if (direction === 'up') {
            chatArea.scrollTop -= scrollAmount;
        } else {
            chatArea.scrollTop += scrollAmount;
        }
    }
    
    // Lightbox
    function openLightbox(url) {
        if (!url) return;
        const lightbox = document.getElementById('lightbox-overlay');
        const img = document.getElementById('lightbox-img');
        img.src = url;
        lightbox.classList.add('active');
    }
    
    function closeLightbox() {
        document.getElementById('lightbox-overlay').classList.remove('active');
    }
    
    // Web Audio API Sound Synthesizer (No requiere archivos locales de audio!)
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    
    function playSound(type) {
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        
        const now = audioCtx.currentTime;
        
        if (type === 'success') {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain); gain.connect(audioCtx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(523.25, now); // C5
            osc.frequency.exponentialRampToValueAtTime(880, now + 0.15); // A5
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.linearRampToValueAtTime(0.01, now + 0.15);
            osc.start(now);
            osc.stop(now + 0.15);
        } else if (type === 'warning') {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain); gain.connect(audioCtx.destination);
            osc.type = 'triangle';
            osc.frequency.setValueAtTime(330, now); // E4
            osc.frequency.setValueAtTime(392, now + 0.08); // G4
            gain.gain.setValueAtTime(0.12, now);
            gain.gain.linearRampToValueAtTime(0.01, now + 0.2);
            osc.start(now);
            osc.stop(now + 0.2);
        } else if (type === 'error') {
            const osc = audioCtx.createOscillator();
            const gain = audioCtx.createGain();
            osc.connect(gain); gain.connect(audioCtx.destination);
            osc.type = 'sawtooth';
            osc.frequency.setValueAtTime(220, now);
            osc.frequency.linearRampToValueAtTime(110, now + 0.25);
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.linearRampToValueAtTime(0.01, now + 0.25);
            osc.start(now);
            osc.stop(now + 0.25);
        } else if (type === 'match') {
            // Campanitas mÃ¡gicas / Arpa rÃ¡pida
            const notes = [261.63, 329.63, 392.00, 523.25, 659.25, 783.99]; // Acorde C
            notes.forEach((freq, idx) => {
                const noteTime = now + (idx * 0.04);
                const localOsc = audioCtx.createOscillator();
                const localGain = audioCtx.createGain();
                localOsc.connect(localGain);
                localGain.connect(audioCtx.destination);
                localOsc.type = 'sine';
                localOsc.frequency.setValueAtTime(freq, noteTime);
                localGain.gain.setValueAtTime(0.08, noteTime);
                localGain.gain.exponentialRampToValueAtTime(0.001, noteTime + 0.3);
                localOsc.start(noteTime);
                localOsc.stop(noteTime + 0.35);
            });
        } else if (type === 'levelup') {
            // Fanfarria festiva alegre
            const melody = [523.25, 659.25, 783.99, 1046.50];
            melody.forEach((freq, idx) => {
                const noteTime = now + (idx * 0.12);
                const localOsc = audioCtx.createOscillator();
                const localGain = audioCtx.createGain();
                localOsc.connect(localGain);
                localGain.connect(audioCtx.destination);
                localOsc.type = 'sine';
                localOsc.frequency.setValueAtTime(freq, noteTime);
                localGain.gain.setValueAtTime(0.1, noteTime);
                localGain.gain.exponentialRampToValueAtTime(0.001, noteTime + 0.4);
                localOsc.start(noteTime);
                localOsc.stop(noteTime + 0.45);
            });
        } else if (type === 'gameover') {
            // MelodÃ­a triste descendente
            const failMelody = [293.66, 277.18, 261.63, 196.00];
            failMelody.forEach((freq, idx) => {
                const noteTime = now + (idx * 0.15);
                const localOsc = audioCtx.createOscillator();
                const localGain = audioCtx.createGain();
                localOsc.connect(localGain);
                localGain.connect(audioCtx.destination);
                localOsc.type = 'sawtooth';
                localOsc.frequency.setValueAtTime(freq, noteTime);
                localGain.gain.setValueAtTime(0.1, noteTime);
                localGain.gain.linearRampToValueAtTime(0.001, noteTime + 0.25);
                localOsc.start(noteTime);
                localOsc.stop(noteTime + 0.3);
            });
        }
    }
    
    // Canvas Confetti Serpentinas / Bombs
    let confettiInterval = null;
    const canvas = document.getElementById('celebration-canvas');
    const ctx = canvas.getContext('2d');
    let particles = [];
    
    function resizeCanvas() {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
    }
    
    function startCelebrationConfetti() {
        canvas.style.display = 'block';
        resizeCanvas();
        particles = [];
        
        // Spawnear partÃ­culas iniciales
        for (let i = 0; i < 80; i++) {
            particles.push(createParticle());
        }
        
        confettiInterval = requestAnimationFrame(updateConfetti);
    }
    
    function stopCelebrationConfetti() {
        canvas.style.display = 'none';
        cancelAnimationFrame(confettiInterval);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    }
    
    function createParticle() {
        return {
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height - canvas.height,
            r: Math.random() * 6 + 4,
            d: Math.random() * canvas.height,
            color: `hsl(${Math.random() * 360}, 100%, 50%)`,
            tilt: Math.random() * 10 - 5,
            tiltAngleIncremental: Math.random() * 0.07 + 0.02,
            tiltAngle: 0
        };
    }
    
    function updateConfetti() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        particles.forEach((p, idx) => {
            p.tiltAngle += p.tiltAngleIncremental;
            p.y += (Math.cos(p.d) + 3 + p.r / 2) / 2;
            p.x += Math.sin(p.tiltAngle);
            p.tilt = Math.sin(p.tiltAngle - idx/3) * 15;
            
            ctx.beginPath();
            ctx.lineWidth = p.r;
            ctx.strokeStyle = p.color;
            ctx.moveTo(p.x + p.tilt + p.r / 2, p.y);
            ctx.lineTo(p.x + p.tilt, p.y + p.tilt + p.r / 2);
            ctx.stroke();
            
            // Loop de partÃ­culas al salir de pantalla
            if (p.y > canvas.height) {
                particles[idx] = createParticle();
                particles[idx].y = -20;
            }
        });
        
        confettiInterval = requestAnimationFrame(updateConfetti);
    }
    
    // NavegaciÃ³n de Pantallas
    function showScreen(screenId) {
        if (screenId === 'study') {
            document.body.classList.add('study-mode');
            document.getElementById('screen-game').style.display = 'none';
            document.getElementById('screen-study').style.display = 'flex';
            
            const studyIframe = document.getElementById('study-iframe');
            if (studyIframe && studyIframe.srcdoc === '' && studyCasesBase64 !== '') {
                try {
                    // Decodificar Base64 a UTF-8 de forma segura e inyectarlo usando srcdoc para evitar bloqueos del navegador local
                    studyIframe.srcdoc = decodeURIComponent(escape(atob(studyCasesBase64)));
                } catch(e) {
                    console.error("Error decodificando casos reales:", e);
                }
            }
        } else {
            document.body.classList.remove('study-mode');
            document.getElementById('screen-study').style.display = 'none';
            document.getElementById('screen-game').style.display = 'flex';
        }
    }
    
    // Modal de Ayuda (botÃ³n ?)
    function showHelpModal() {
        setInputLocked(true);
        document.getElementById('help-modal').classList.add('active');
    }
    function closeHelpModal() {
        document.getElementById('help-modal').classList.remove('active');
        if (!hasActiveBlockingModal()) {
            setInputLocked(false);
        }
    }

    function installCoachModalKeyboardControls() {
        document.addEventListener('keydown', (event) => {
            const overlay = document.getElementById('modal-overlay');
            if (!overlay || !overlay.classList.contains('active')) return;
            if (event.key === 'Enter' || event.key === ' ' || event.key === 'Escape') {
                event.preventDefault();
                closeCoachModal();
            }
        });
    }

    function installTestHooks() {
        window.easyDateTest = {
            getState: () => JSON.parse(JSON.stringify(gameState)),
            getProgressText: () => document.getElementById('level-progress-display').innerText,
            isCoachOpen: () => document.getElementById('modal-overlay').classList.contains('active'),
            isLevelUpOpen: () => document.getElementById('levelup-modal').classList.contains('active'),
            openGameOverForTest: (good, bad, lives = 0, turns = []) => {
                gameState.stats = { good, bad, turns };
                gameState.lives = lives;
                showGameOverModal();
                return {
                    open: document.getElementById('gameover-modal').classList.contains('active'),
                    summary: document.getElementById('gameover-summary').innerText
                };
            },
            runLevel1HappyPath: async () => {
                window.easyDateForceMockApi = true;
                localStorage.removeItem('easyDateState');
                gameState = {
                    level_index: 0,
                    step_index: 0,
                    lives: levelLivesMap[0],
                    attraction: 50,
                    history: [],
                    locked: false,
                    replyMode: 'free',
                    stats: { good: 0, bad: 0, turns: [] }
                };
                document.getElementById('match-modal').classList.remove('active');
                document.getElementById('gameover-modal').classList.remove('active');
                document.getElementById('levelup-modal').classList.remove('active');
                document.getElementById('chat-area').innerHTML = '';
                renderStep();

                const level = gameData.levels[0];
                const visited = [];
                for (let i = 0; i < level.steps.length; i++) {
                    const currentStep = level.steps[gameState.step_index];
                    visited.push({
                        progress: document.getElementById('level-progress-display').innerText,
                        stepId: currentStep.step_id
                    });
                    const correctOption = Array.from(document.querySelectorAll('input[name="reply_opt"]'))
                        .find((input) => JSON.parse(input.value).is_correct);
                    if (!correctOption) throw new Error(`No hay opcion correcta para paso ${currentStep.step_id}`);
                    const correctText = JSON.parse(correctOption.value).text;
                    const freeInput = document.getElementById('free-reply-input');
                    if (!freeInput) throw new Error('No existe campo de escritura libre');
                    freeInput.value = correctText;
                    const minAllowed = Math.max(1, Math.min(...currentStep.allowed_time_indices));
                    setSelectedTimeIndex(minAllowed);
                    await evaluateSelection();
                    if (!document.getElementById('modal-overlay').classList.contains('active')) {
                        throw new Error(`El Coach no abrio en paso ${currentStep.step_id}`);
                    }
                    closeCoachModal();
                }

                return {
                    visited,
                    levelUpOpen: document.getElementById('levelup-modal').classList.contains('active'),
                    levelUpSummary: document.getElementById('levelup-summary').innerText,
                    coachOpen: document.getElementById('modal-overlay').classList.contains('active'),
                    coachDisplay: getComputedStyle(document.getElementById('modal-overlay')).display,
                    coachPointerEvents: getComputedStyle(document.getElementById('modal-overlay')).pointerEvents,
                    state: JSON.parse(JSON.stringify(gameState))
                };
            },
            runContextCoherenceSmoke: async () => {
                const week = await localEmergencySimulationTurn({
                    level: 1,
                    step_index: 0,
                    attraction: 50,
                    history: [
                        { sender: 'user', text: 'Hola Natalia, que lindo tu perfil. Que tal tu semana?', timeText: '15m' }
                    ],
                    user_message: 'Hola Natalia, que lindo tu perfil. Que tal tu semana?',
                    chosen_time: '15m',
                    visible_context: {
                        last_natalia_message: ''
                    }
                });
                const exercise = await localEmergencySimulationTurn({
                    level: 1,
                    step_index: 1,
                    attraction: 50,
                    history: [
                        { sender: 'her', text: 'esa soy yo totalmente jaja ¿cómo va tu día?', timeText: 'Tardó: 15 min' },
                        { sender: 'user', text: 'bien en el gimnasio y a ti te gusta hacer ejercicio?', timeText: '15m' }
                    ],
                    user_message: 'bien en el gimnasio y a ti te gusta hacer ejercicio?',
                    chosen_time: '15m',
                    visible_context: {
                        last_natalia_message: 'esa soy yo totalmente jaja ¿cómo va tu día?'
                    }
                });
                const work = await localEmergencySimulationTurn({
                    level: 1,
                    step_index: 2,
                    attraction: 50,
                    history: [
                        { sender: 'her', text: 'me gusta eso, perfecto ¿dónde vives? yo en brickell ¿y tú?', timeText: 'Tardó: 20 min' },
                        { sender: 'user', text: 'yo vivo en bogota y en que trabajas?', timeText: '1h' }
                    ],
                    user_message: 'yo vivo en bogota y en que trabajas?',
                    chosen_time: '1h',
                    visible_context: {
                        last_natalia_message: 'me gusta eso, perfecto ¿dónde vives? yo en brickell ¿y tú?'
                    }
                });
                const music = await localEmergencySimulationTurn({
                    level: 1,
                    step_index: 3,
                    attraction: 65,
                    history: [{ sender: 'her', text: 'jaja ok, eso me da curiosidad.', timeText: 'Tardó: 15 min' }],
                    user_message: 'Y a ti que música te gusta?',
                    chosen_time: '15m',
                    visible_context: { last_natalia_message: 'jaja ok, eso me da curiosidad.' }
                });
                const food = await localEmergencySimulationTurn({
                    level: 1,
                    step_index: 3,
                    attraction: 65,
                    history: [{ sender: 'her', text: 'jaja ok, eso me da curiosidad.', timeText: 'Tardó: 15 min' }],
                    user_message: 'Qué comida te gusta?',
                    chosen_time: '15m',
                    visible_context: { last_natalia_message: 'jaja ok, eso me da curiosidad.' }
                });
                const travel = await localEmergencySimulationTurn({
                    level: 1,
                    step_index: 3,
                    attraction: 65,
                    history: [{ sender: 'her', text: 'jaja ok, eso me da curiosidad.', timeText: 'Tardó: 15 min' }],
                    user_message: 'Te gusta viajar o eres más de quedarte?',
                    chosen_time: '15m',
                    visible_context: { last_natalia_message: 'jaja ok, eso me da curiosidad.' }
                });
                const pets = await localEmergencySimulationTurn({
                    level: 1,
                    step_index: 3,
                    attraction: 65,
                    history: [{ sender: 'her', text: 'jaja ok, eso me da curiosidad.', timeText: 'Tardó: 15 min' }],
                    user_message: 'Tienes perro o gato?',
                    chosen_time: '15m',
                    visible_context: { last_natalia_message: 'jaja ok, eso me da curiosidad.' }
                });
                const family = await localEmergencySimulationTurn({
                    level: 1,
                    step_index: 3,
                    attraction: 65,
                    history: [{ sender: 'her', text: 'jaja ok, eso me da curiosidad.', timeText: 'Tardó: 15 min' }],
                    user_message: 'Eres cercana con tu familia?',
                    chosen_time: '15m',
                    visible_context: { last_natalia_message: 'jaja ok, eso me da curiosidad.' }
                });
                return { week, exercise, work, music, food, travel, pets, family };
            }
        };
    }
    
    // Carga Inicial
    window.onload = () => {
        window.addEventListener('resize', resizeCanvas);
        installCoachModalKeyboardControls();
        installTestHooks();
        
        // Manejador del rango de tiempo: no hay valor seleccionado por defecto.
        const slider = document.getElementById('time-slider');
        slider.addEventListener('pointerdown', () => {
            if (slider.dataset.selected !== 'true') {
                setSelectedTimeIndex(parseInt(slider.value));
            }
        });
        slider.addEventListener('keydown', (event) => {
            if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown', 'Home', 'End'].includes(event.key) && slider.dataset.selected !== 'true') {
                setSelectedTimeIndex(parseInt(slider.value));
            }
        });
        slider.addEventListener('input', (e) => {
            setSelectedTimeIndex(parseInt(e.target.value));
        });
        clearTimeSelection();

        const freeInput = document.getElementById('free-reply-input');
        if (freeInput) {
            freeInput.addEventListener('keydown', (event) => {
                if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
                    event.preventDefault();
                    event.stopPropagation();
                    evaluateSelection();
                }
            });
        }
        
        // Cargar estado previo
        if (new URLSearchParams(window.location.search).has('reset')) {
            localStorage.removeItem('easyDateState');
        }
        const savedState = localStorage.getItem('easyDateState');
        if (savedState) {
            gameState = JSON.parse(savedState);
            gameState.replyMode = 'free';
            ensureStatsShape();
            if (gameState.locked && gameState.history && gameState.history.length) {
                const lastTurn = gameState.history[gameState.history.length - 1];
                if (lastTurn && lastTurn.sender === 'user') {
                    gameState.history.pop();
                }
            }
            gameState.locked = false;
            
            // Si el historial estÃ¡ vacÃ­o, forzar reset e inicio fresco para que salga el modal
            if (!gameState.history || gameState.history.length === 0) {
                resetGame();
            } else if (gameState.level_index >= gameData.levels.length) {
                showFinalWinModal();
            } else if (gameState.step_index >= gameData.levels[gameState.level_index].steps.length) {
                gameState.step_index = gameData.levels[gameState.level_index].steps.length - 1;
                saveState();
                renderStep();
                showLevelUpModal();
            } else {
                // Reconstruir chat anterior
                const chatArea = document.getElementById('chat-area');
                chatArea.innerHTML = '';
                
                gameState.history.forEach(h => {
                    const msgDiv = document.createElement('div');
                    msgDiv.className = `message ${h.sender}`;
                    
                    if (h.sender === 'her') {
                        const avaDiv = document.createElement('div');
                        avaDiv.className = 'avatar';
                        avaDiv.style.backgroundImage = `url("${levelAvatars[h.levelIndex]}")`;
                        avaDiv.addEventListener('click', () => openLightbox(levelAvatars[h.levelIndex]));
                        msgDiv.appendChild(avaDiv);
                    }
                    
                    const bubDiv = document.createElement('div');
                    bubDiv.className = 'bubble';
                    bubDiv.appendChild(document.createTextNode(h.text || ''));
                    const timeSpan = document.createElement('span');
                    timeSpan.className = 'message-time-highlight';
                    timeSpan.innerText = `(${formatMessageTime(h.sender, h.timeText)})`;
                    bubDiv.appendChild(document.createElement('br'));
                    bubDiv.appendChild(timeSpan);
                    
                    msgDiv.appendChild(bubDiv);
                    chatArea.appendChild(msgDiv);
                });
                
                scrollToBottom();
                renderStep();
                const restoredInput = document.getElementById('free-reply-input');
                if (restoredInput) restoredInput.focus();
            }
        } else {
            resetGame();
        }
        
        const sendButton = document.getElementById('btn-send');
        if (sendButton) sendButton.addEventListener('click', evaluateSelection);
        const closeModalButton = document.getElementById('btn-close-modal');
        closeModalButton.addEventListener('click', closeCoachModal);
        closeModalButton.addEventListener('pointerdown', (event) => {
            event.preventDefault();
            closeCoachModal();
        });
        closeModalButton.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                closeCoachModal();
            }
        });
        document.getElementById('lightbox-overlay').addEventListener('click', closeLightbox);
        document.getElementById('match-start-btn').addEventListener('click', startLevel);
        document.getElementById('levelup-next-btn').addEventListener('click', nextLevel);
        document.getElementById('gameover-retry-btn').addEventListener('click', retryLevel);
        document.getElementById('btn-close-help').addEventListener('click', closeHelpModal);
    };
    """

    # Perform placeholder replacements
    js_final = js_template.replace("__GAME_DATA__", json.dumps(game_data))
    js_final = js_final.replace("__LEVEL_AVATARS__", json.dumps(level_imgs))
    js_final = js_final.replace("__COACH_AVATAR__", coach_img)
    js_final = js_final.replace("__STUDY_CASES_BASE64__", cases_base64)

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Easy Date V2 - Real Text Game</title>
    <style>
        {css_content}

        .modal-overlay {{
            display: none;
        }}
        .modal-overlay.active {{
            display: flex;
        }}
        
        /* Ajuste tipogrÃ¡fico y mÃ³vil compatible con iPhone 15 Pro */
        body, html {{
            margin: 0; padding: 0; width: 100%; height: 100dvh; min-height: 100svh;
            background-color: #05070c; overflow: hidden;
            display: flex; justify-content: center; align-items: center;
        }}
        .app-container {{
            width: min(100vw, 430px);
            max-width: 430px;
            height: 100dvh;
            max-height: 100dvh;
            background-color: #0b0f19;
            box-shadow: 0 10px 50px rgba(0,0,0,0.8);
            border: 1px solid rgba(255,255,255,0.05);
            font-size: 1.05rem; /* Letra un poco mÃ¡s grande */
            overflow: hidden;
        }}
        .chat-area {{
            height: auto !important;
            max-height: none !important;
            flex: 1 1 auto !important;
            min-height: 0 !important;
            overflow-y: auto;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            padding: 6px 12px !important;
        }}
        .top-bar {{
            display: flex !important;
            flex-direction: column !important;
            gap: 5px !important;
            padding: calc(6px + env(safe-area-inset-top)) 10px 6px !important;
            background: #211c1c !important;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        }}
        .profile-bar {{
            display: grid;
            grid-template-columns: 28px 38px minmax(0, 1fr) 28px;
            align-items: center;
            gap: 8px;
            min-height: 38px;
        }}
        .profile-icon-btn {{
            width: 28px;
            height: 28px;
            border: 0;
            background: transparent;
            color: #f8fafc;
            font-size: 1.4rem;
            line-height: 1;
            display: grid;
            place-items: center;
            cursor: pointer;
        }}
        .chat-profile-avatar {{
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background-size: cover;
            background-position: center;
            border: 2px solid rgba(255, 60, 110, 0.95);
        }}
        .chat-profile-title {{
            min-width: 0;
            display: flex;
            align-items: center;
            gap: 5px;
            color: #f8fafc;
            font-family: Outfit, sans-serif;
            font-weight: 900;
            font-size: 1rem;
            overflow: hidden;
            white-space: nowrap;
            text-overflow: ellipsis;
        }}
        .verified-dot {{
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #3b82f6;
            color: white;
            font-size: 0.62rem;
            display: grid;
            place-items: center;
            flex: 0 0 auto;
        }}
        .game-status-row {{
            display: grid;
            grid-template-columns: auto auto minmax(74px, 1fr);
            align-items: center;
            gap: 6px;
            min-width: 0;
        }}
        .game-status-row .rank,
        .game-status-row .level-progress {{
            font-size: 0.7rem !important;
            line-height: 1 !important;
            padding: 5px 8px !important;
            white-space: nowrap;
        }}
        .game-status-row .calibration-section {{
            min-width: 0;
            justify-content: end;
        }}
        .game-status-row .investment-text {{
            font-size: 0.68rem !important;
            white-space: nowrap;
        }}
        .bottom-panel {{
            flex: 0 0 auto !important;
            min-height: 0 !important;
            max-height: min(42dvh, 330px) !important;
            overflow-y: auto !important;
            overscroll-behavior: contain;
            display: flex !important;
            flex-direction: column !important;
            justify-content: flex-start !important;
            padding: 6px 10px calc(8px + env(safe-area-inset-bottom)) 10px !important;
            gap: 6px !important;
        }}
        .bubble {{
            font-size: 0.95rem !important;
            line-height: 1.4 !important;
        }}
        .options-grid {{
            gap: 4px !important;
            max-height: 18dvh;
            overflow-y: auto;
            padding-right: 2px;
        }}
        .reply-mode-toggle {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px;
            margin-bottom: 0;
        }}
        .reply-mode-btn {{
            height: 26px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.12);
            background: rgba(255,255,255,0.06);
            color: #cbd5e1;
            font-family: Outfit, sans-serif;
            font-weight: 700;
            cursor: pointer;
        }}
        .reply-mode-btn.active {{
            background: var(--accent-gradient);
            color: white;
            border-color: rgba(255, 60, 110, 0.8);
        }}
        .free-reply-input {{
            width: 100%;
            min-height: 40px;
            max-height: 68px;
            resize: none;
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 20px;
            background: #050505;
            color: #f8fafc;
            font-family: Outfit, sans-serif;
            font-size: 0.95rem;
            line-height: 1.25;
            padding: 10px 12px;
            outline: none;
        }}
        .free-reply-input:focus {{
            border-color: #ff3c6e;
            box-shadow: 0 0 0 3px rgba(255, 60, 110, 0.16);
        }}
        .free-composer-shell {{
            display: block;
        }}
        .reply-mode-btn:focus-visible,
        .emoji-chip:focus-visible {{
            outline: 2px solid rgba(255, 60, 110, 0.9);
            outline-offset: 2px;
        }}
        .emoji-rail {{
            display: flex;
            gap: 5px;
            overflow-x: auto;
            padding: 4px 1px 0;
            scrollbar-width: none;
        }}
        .emoji-rail::-webkit-scrollbar {{
            display: none;
        }}
        .emoji-chip {{
            flex: 0 0 auto;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            border: 1px solid rgba(255,255,255,0.10);
            background: rgba(255,255,255,0.06);
            color: #f8fafc;
            font-size: 0.95rem;
            cursor: pointer;
            display: grid;
            place-items: center;
        }}
        .emoji-chip:hover,
        .emoji-chip:focus {{
            border-color: rgba(255, 60, 110, 0.75);
            background: rgba(255, 60, 110, 0.16);
            outline: none;
        }}
        .emoji-chip:disabled {{
            opacity: 0.45;
            cursor: not-allowed;
        }}
        .reply-mode-btn:disabled,
        .free-reply-input:disabled,
        .btn-reset:disabled,
        .btn-study-highlight:disabled,
        .time-slider:disabled {{
            opacity: 0.5;
            cursor: not-allowed !important;
        }}
        .option-card {{
            padding: 3px 6px !important;
            min-height: 36px !important;
        }}
        .option-card .text-content {{
            font-size: 0.78rem !important;
            line-height: 1.15 !important;
            font-weight: 500;
            min-width: 0;
            overflow-wrap: anywhere;
        }}
        .time-label {{
            font-size: 0.75rem !important;
            color: #94a3b8;
            margin-bottom: 1px;
            display: block;
        }}
        .time-selector {{
            margin: 0 !important;
            border-radius: 10px;
            padding: 4px 6px;
            transition: background 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
        }}
        .time-selector > div:first-child {{
            line-height: 1;
        }}
        .slider-wrapper {{
            padding-top: 2px !important;
        }}
        .time-slider {{
            height: 12px !important;
        }}
        .slider-ticks-labels {{
            font-size: 0.62rem !important;
            line-height: 1 !important;
            margin-top: 0 !important;
        }}
        .time-selector.time-unselected {{
            background: rgba(239, 68, 68, 0.12);
            box-shadow: inset 0 0 0 1px rgba(239, 68, 68, 0.62);
        }}
        .time-selector.time-unselected #slider-time-display {{
            color: #fca5a5 !important;
        }}
        .time-selector.time-unselected .time-slider {{
            accent-color: #ef4444;
        }}
        .time-selector.time-selected {{
            background: rgba(16, 185, 129, 0.12);
            box-shadow: inset 0 0 0 1px rgba(16, 185, 129, 0.62);
        }}
        .time-selector.time-selected #slider-time-display {{
            color: #34d399 !important;
        }}
        .time-selector.time-selected .time-slider {{
            accent-color: #10b981;
        }}
        .action-row {{
            gap: 5px !important;
            display: grid !important;
            grid-template-columns: 1fr 1fr !important;
            align-items: center;
        }}
        @media (max-width: 430px) {{
            .options-grid {{
                grid-template-columns: 1fr !important;
            }}
        }}
        @media (max-height: 700px) {{
            .top-bar {{
                padding-top: 4px !important;
                padding-bottom: 4px !important;
            }}
            .chat-area {{
                padding: 4px 10px !important;
            }}
            .bottom-panel {{
                max-height: 43dvh !important;
                padding: 5px 8px calc(6px + env(safe-area-inset-bottom)) 8px !important;
                gap: 4px !important;
            }}
            .reply-mode-btn {{
                height: 24px !important;
                font-size: 0.78rem !important;
            }}
            .free-reply-input {{
                min-height: 38px !important;
                max-height: 52px !important;
                padding: 8px 10px !important;
            }}
            .emoji-rail {{
                padding-top: 2px !important;
            }}
            .emoji-chip {{
                width: 25px !important;
                height: 25px !important;
                font-size: 0.82rem !important;
            }}
            .time-label,
            #slider-time-display {{
                font-size: 0.68rem !important;
            }}
            .slider-ticks-labels {{
                font-size: 0.55rem !important;
            }}
            .btn-reset,
            .btn-study-highlight {{
                height: 28px !important;
                font-size: 0.72rem !important;
            }}
            .coach-modal {{
                width: calc(100vw - 22px) !important;
                max-height: calc(100svh - 18px) !important;
                padding: 12px !important;
            }}
            .coach-avatar {{
                width: 54px !important;
                height: 54px !important;
            }}
            .coach-feedback-card {{
                padding: 7px 8px !important;
            }}
            .coach-feedback-card p,
            .coach-feedback-card ol {{
                font-size: 0.82rem !important;
                line-height: 1.25 !important;
            }}
        }}
        
        /* Ajustes especÃ­ficos para el avatar redondo del Coach y su tamaÃ±o de modal */
        .coach-avatar {{
            width: 68px !important;
            height: 68px !important;
            border-radius: 50% !important;
            overflow: hidden !important;
            border: 3px solid var(--accent-primary) !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            box-shadow: 0 4px 15px rgba(255, 60, 110, 0.3) !important;
            flex-shrink: 0 !important;
        }}
        .coach-avatar img {{
            width: 100% !important;
            height: 100% !important;
            object-fit: cover !important;
            border-radius: 50% !important;
        }}
        .coach-modal {{
            width: min(92vw, 380px) !important;
            max-width: 380px !important;
            max-height: calc(100svh - 28px) !important;
            overflow-y: auto !important;
            overscroll-behavior: contain;
            padding: 16px !important;
            border-radius: 18px !important;
            background: #141928 !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
        }}
        .coach-header {{
            flex-direction: row !important;
            justify-content: flex-start !important;
            align-items: center !important;
            gap: 12px !important;
            text-align: left !important;
            margin-bottom: 10px !important;
        }}
        .coach-message {{
            display: grid !important;
            gap: 8px !important;
            margin-bottom: 12px !important;
        }}
        .coach-feedback-card {{
            border-left: 4px solid rgba(255, 255, 255, 0.18);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.055);
            padding: 9px 10px;
        }}
        .coach-feedback-card p,
        .coach-feedback-card ol {{
            margin: 4px 0 0 0;
            color: #e2e8f0;
            font-size: 0.9rem;
            line-height: 1.35;
        }}
        .coach-feedback-card ol {{
            padding-left: 20px;
        }}
        .coach-feedback-card li {{
            margin: 3px 0;
        }}
        .coach-feedback-label {{
            font-size: 0.7rem;
            line-height: 1;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 0;
        }}
        .coach-card-message {{
            border-left-color: #ef4444;
            background: rgba(239, 68, 68, 0.09);
        }}
        .coach-card-message .coach-feedback-label {{
            color: #fca5a5;
        }}
        .coach-card-time {{
            border-left-color: #f59e0b;
            background: rgba(245, 158, 11, 0.1);
        }}
        .coach-card-time .coach-feedback-label {{
            color: #fcd34d;
        }}
        .coach-card-emoji {{
            border-left-color: #a855f7;
            background: rgba(168, 85, 247, 0.1);
        }}
        .coach-card-emoji .coach-feedback-label {{
            color: #d8b4fe;
        }}
        .coach-card-objective {{
            border-left-color: #10b981;
            background: rgba(16, 185, 129, 0.1);
        }}
        .coach-card-objective .coach-feedback-label {{
            color: #6ee7b7;
        }}
        .coach-card-suggestions {{
            border-left-color: #3b82f6;
            background: rgba(59, 130, 246, 0.1);
        }}
        .coach-card-suggestions .coach-feedback-label {{
            color: #93c5fd;
        }}
        .btn-close-modal {{
            padding: 10px !important;
            font-size: 0.95rem !important;
            border-radius: var(--border-radius-md) !important;
        }}
        
        /* Red, bold, and larger text for waiting/respond times (+30%) */
        .message-time-highlight {{
            font-weight: 600;
            font-size: 0.94rem !important; /* ~30% mÃ¡s grande que 0.72rem */
            display: block;
            margin-top: 4px;
            text-align: right;
            font-style: italic;
        }}
        .message.user .message-time-highlight {{
            color: rgba(255, 255, 255, 0.95) !important; /* MÃ¡s contraste en globo del hombre */
        }}
        .message.her .message-time-highlight {{
            color: rgba(255, 255, 255, 0.8) !important;
        }}
        
        /* Estilos para el modo estudio a pantalla completa */
        body.study-mode .app-container {{
            max-width: 100% !important;
            height: 100vh !important;
            max-height: 100vh !important;
            border-radius: 0 !important;
            border: none !important;
            width: 100% !important;
        }}
        
        /* Modales Premium */
        .match-modal-container, .levelup-modal-container {{
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(11, 15, 25, 0.96);
            z-index: 2000;
            display: none;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            padding: 30px;
            text-align: center;
            box-sizing: border-box;
        }}
        .match-modal-container.active, .levelup-modal-container.active {{
            display: flex;
        }}
        .match-card {{
            background: #141928;
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 24px;
            padding: 30px;
            width: 100%;
            max-width: 320px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.5);
            animation: popUp 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }}
        .match-girl-avatar-circle {{
            width: 140px;
            height: 140px;
            border-radius: 50%;
            border: 4px solid #ff3c6e;
            margin: 0 auto 20px auto;
            background-size: cover;
            background-position: center;
            box-shadow: 0 0 25px rgba(255, 60, 110, 0.4);
        }}
        .match-pulse-avatar {{
            animation: pulseZoom 2.5s infinite ease-in-out;
        }}
        .match-title-gradient {{
            font-family: Outfit, sans-serif;
            font-size: 2.2rem;
            font-weight: 800;
            margin: 10px 0;
            background: linear-gradient(135deg, #ff3c6e 0%, #ff7854 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .btn-premium {{
            background: var(--accent-gradient);
            color: white;
            border: none;
            padding: 14px 28px;
            border-radius: 30px;
            font-weight: 800;
            font-family: Outfit, sans-serif;
            font-size: 1rem;
            cursor: pointer;
            width: 100%;
            margin-top: 20px;
            box-shadow: 0 5px 15px rgba(255, 60, 110, 0.4);
            transition: transform 0.2s;
        }}
        .btn-premium:active {{
            transform: scale(0.97);
        }}
        
        /* Animaciones */
        @keyframes popUp {{
            from {{ transform: scale(0.7); opacity: 0; }}
            to {{ transform: scale(1); opacity: 1; }}
        }}
        @keyframes pulseZoom {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.08); box-shadow: 0 0 35px rgba(255, 60, 110, 0.6); }}
            100% {{ transform: scale(1); }}
        }}
        
        /* Slider de tiempo simplificado de 8 ticks */
        .slider-wrapper {{
            margin: 10px 0;
        }}
        .slider-ticks-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.65rem;
            color: #94a3b8;
            margin-top: 4px;
        }}
    </style>
</head>
<body>
    <div class="app-container">
        
        <!-- PANTALLA DE JUEGO -->
        <div id="screen-game" class="app-screen" style="display: flex; flex-direction: column; height: 100%;">
            <header class="top-bar">
                <div class="profile-bar">
                    <button type="button" class="profile-icon-btn" aria-label="Volver al chat">‹</button>
                    <div class="chat-profile-avatar" id="chat-profile-avatar"></div>
                    <div class="chat-profile-title">
                        <span id="chat-profile-name">Natalia</span>
                        <span class="verified-dot">✓</span>
                    </div>
                    <button type="button" class="profile-icon-btn" aria-label="Opciones">⋯</button>
                </div>
                <div class="stats game-status-row">
                    <span class="rank" id="rank-display">Vidas: â¤ï¸â¤ï¸â¤ï¸â¤ï¸</span>
                    <span class="level-progress" id="level-progress-display">Cargando...</span>
                    <div class="calibration-section" style="display: flex; align-items: center; gap: 6px;">
                        <span class="investment-text" id="calibration-text" style="color: #10b981;">AtracciÃ³n: 50%</span>
                        <div class="progress-bar" style="width: 50px; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden;">
                            <div class="progress" id="calibration-bar-fill" style="width: 50%; height: 100%; background: #10b981; transition: width 0.3s;"></div>
                        </div>
                        <button onclick="showHelpModal()" style="background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); color: white; width: 22px; height: 22px; border-radius: 50%; font-size: 0.75rem; font-weight: bold; cursor: pointer; flex-shrink: 0; display: flex; align-items: center; justify-content: center;">?</button>
                    </div>
                </div>
            </header>

            <main class="chat-area" id="chat-area">
                <!-- Chat bubbles -->
            </main>

            <!-- BOTONES DE SCROLL FLOTANTES -->
            <div class="scroll-buttons-container">
                <button onclick="scrollChat('up')" class="scroll-btn scroll-btn-up">â–²</button>
                <button onclick="scrollChat('down')" class="scroll-btn scroll-btn-down">â–¼</button>
            </div>

            <footer class="bottom-panel">
                <div class="reply-mode-toggle">
                    <button type="button" class="reply-mode-btn active" id="mode-free" onclick="setReplyMode('free')" aria-pressed="true">Mensaje</button>
                    <button type="button" class="reply-mode-btn" id="mode-guided" onclick="setReplyMode('guided')" aria-pressed="false">Sugerencias</button>
                </div>
                <div id="free-composer">
                    <div class="free-composer-shell">
                        <div>
                            <textarea id="free-reply-input" class="free-reply-input" placeholder="Mensaje..." aria-label="Mensaje de Tinder"></textarea>
                            <div class="emoji-rail" aria-label="Emojis rápidos">
                                <button type="button" class="emoji-chip" onclick="insertEmoji('😉')" title="Guiño calibrado" aria-label="Insertar guiño calibrado">😉</button>
                                <button type="button" class="emoji-chip" onclick="insertEmoji('😂')" title="Humor" aria-label="Insertar risa">😂</button>
                                <button type="button" class="emoji-chip" onclick="insertEmoji('😅')" title="Ligero" aria-label="Insertar sonrisa nerviosa ligera">😅</button>
                                <button type="button" class="emoji-chip" onclick="insertEmoji('😊')" title="Cálido" aria-label="Insertar sonrisa calida">😊</button>
                                <button type="button" class="emoji-chip" onclick="insertEmoji('😌')" title="Tranquilo" aria-label="Insertar gesto tranquilo">😌</button>
                                <button type="button" class="emoji-chip" onclick="insertEmoji('🔥')" title="Intenso, usar con cuidado" aria-label="Insertar fuego intenso">🔥</button>
                                <button type="button" class="emoji-chip" onclick="insertEmoji('🙃')" title="Juguetón" aria-label="Insertar gesto jugueton">🙃</button>
                            </div>
                        </div>
                    </div>
                </div>
                <div id="guided-composer" style="display: none;">
                    <div class="options-grid" id="options-grid">
                        <!-- Options -->
                    </div>
                </div>
                
                <div class="time-selector">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <label class="time-label">Tardas en responder:</label>
                        <span id="slider-time-display" style="font-size: 0.8rem; font-weight: bold; color: #fca5a5;">Toca para seleccionar</span>
                    </div>
                    <div class="slider-wrapper">
                        <input type="range" min="0" max="7" value="0" class="time-slider" id="time-slider" style="width:100%;">
                        <div class="slider-ticks-labels">
                            <span>Ahora</span><span>15m</span><span>1h</span><span>2h</span><span>4h</span><span>12h</span><span>24h</span><span>2d</span>
                        </div>
                    </div>
                </div>
                
                <div class="action-row" style="width: 100%;">
                    <button onclick="resetGame()" class="btn-reset" id="btn-reset" style="height: 32px; margin: 0; padding: 0; font-size: 0.78rem; border-radius: 10px;">Reiniciar</button>
                    <button onclick="showScreen('study')" class="btn-study-highlight" id="btn-study" style="height: 32px; background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: white; border: none; border-radius: 10px; font-weight: bold; font-family: Outfit, sans-serif; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 4px; font-size: 0.78rem; margin: 0;">Estudiar</button>
                </div>
            </footer>
        </div>

        <!-- PANTALLA DE ESTUDIO -->
        <div id="screen-study" class="app-screen" style="display: none; height: 100%; flex-direction: column;">
            <div class="study-bar" style="background: rgba(20, 25, 40, 0.95); padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.08); flex-shrink: 0;">
                <span style="font-weight: 800; font-size: 1.05rem; color: #ff3c6e; font-family: Outfit, sans-serif;">Casos Reales</span>
                <button onclick="showScreen('game')" style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); color: white; border: none; padding: 8px 16px; border-radius: var(--border-radius-md); font-weight: bold; font-size: 0.8rem; font-family: Outfit, sans-serif;">Volver al Juego ðŸŽ®</button>
            </div>
            <div style="flex: 1; overflow: hidden; background: #0b0f19;">
                <iframe id="study-iframe" style="width: 100%; height: 100%; border: none;"></iframe>
            </div>
        </div>

        <!-- CANVAS DE CELEBRACION -->
        <canvas id="celebration-canvas" style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; pointer-events: none; z-index: 1500; display: none;"></canvas>

        <!-- MODAL DE MATCH (App de Citas) -->
        <div class="match-modal-container" id="match-modal">
            <div class="match-card">
                <div class="match-title-gradient">Â¡Es un Match!</div>
                <div class="match-girl-avatar-circle match-pulse-avatar" id="match-girl-img"></div>
                <h3 style="font-family: Outfit; font-size: 1.6rem; margin: 5px 0;" id="match-girl-name">Natalia</h3>
                <p style="color: #94a3b8; font-size: 0.88rem; margin: 5px 0 20px 0;" id="match-level-title">Nivel 1</p>
                <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.5; margin: 15px 0;">Acabas de hacer match. Ella espera que tomes la iniciativa. Â¡El hombre da el primer paso!</p>
                <button class="btn-premium" id="match-start-btn">COMENZAR A HABLAR ðŸ’¬</button>
            </div>
        </div>

        <!-- MODAL DE LEVEL UP (Beso y Cita) -->
        <div class="levelup-modal-container" id="levelup-modal">
            <div class="match-card">
                <div class="match-title-gradient">Â¡Cita Lograda!</div>
                <div class="match-girl-avatar-circle match-pulse-avatar" id="levelup-girl-img"></div>
                <h3 style="font-family: Outfit; font-size: 1.6rem; margin: 5px 0;">Â¡Genial nos vemos en la cita!</h3>
                <p style="color: #a7f3d0; font-size: 0.95rem; font-weight: bold; margin: 15px 0;" id="levelup-girl-name">Natalia</p>
                <p id="levelup-summary" style="white-space: pre-line; color: #cbd5e1; font-size: 0.86rem; line-height: 1.35; margin: 8px 0 12px 0; text-align: left;"></p>
                <div style="font-size: 3rem; margin: 10px 0; animation: bounce 1.5s infinite;">ðŸ’‹</div>
                <button class="btn-premium" id="levelup-next-btn" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">SIGUIENTE NIVEL âž”</button>
            </div>
        </div>

        <!-- MODAL DE GAME OVER -->
        <div class="match-modal-container" id="gameover-modal">
            <div class="match-card" style="border-color: #ef4444;">
                <div class="match-title-gradient" style="background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">ConversaciÃ³n Muerta</div>
                <div style="font-size: 4rem; margin: 20px 0;">ðŸ’”</div>
                <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.5; margin: 15px 0;">Te has quedado sin vidas. Ella ha perdido el interÃ©s por completo en el chat.</p>
                <p id="gameover-summary" style="white-space: pre-line; color: #cbd5e1; font-size: 0.86rem; line-height: 1.35; margin: 8px 0 12px 0; text-align: left;"></p>
                <button class="btn-premium" onclick="document.getElementById('gameover-modal').classList.remove('active'); showScreen('study');" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); margin-bottom: 8px;">ESTUDIAR CASOS REALES ðŸ“š</button>
                <button class="btn-premium" id="gameover-retry-btn" style="background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);">REINTENTAR NIVEL âŸ³</button>
            </div>
        </div>

        <!-- MODAL DE FINAL WIN -->
        <div class="match-modal-container" id="final-modal">
            <div class="match-card" style="border-color: #f59e0b;">
                <div class="match-title-gradient" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Â¡Leyenda del Juego!</div>
                <div style="font-size: 4rem; margin: 20px 0;">ðŸ†ðŸ‘‘ðŸ·</div>
                <p style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.5; margin: 15px 0;">Â¡Has completado todos los niveles reales! Has demostrado un marco de hierro, control logÃ­stico y gran calibraciÃ³n de tiempos.</p>
                <button class="btn-premium" onclick="resetGame()" style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);">VOLVER A JUGAR ðŸŽ®</button>
            </div>
        </div>

        <!-- LIGHTBOX OVERLAY -->
        <div class="lightbox-overlay" id="lightbox-overlay">
            <img class="lightbox-img" id="lightbox-img" src="" alt="Ampliado">
        </div>

        <!-- MODAL DE AYUDA (botÃ³n ?) -->
        <div class="match-modal-container" id="help-modal" style="z-index: 3500;">
            <div class="match-card" style="max-width: 340px; text-align: left;">
                <div class="match-title-gradient" style="font-size: 1.6rem; margin-bottom: 8px;">ðŸ“š CÃ³mo Jugar</div>
                <p style="color: #94a3b8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin: 12px 0 4px;">Modo guiado</p>
                <p style="color: #e2e8f0; font-size: 0.9rem; line-height: 1.5; margin: 0 0 10px;">Practica conversaciones reales de apps de citas respondiendo a lo que ella acaba de decir y eligiendo un tiempo creíble para enviarlo.</p>
                
                <p style="color: #94a3b8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin: 12px 0 4px;">â¤ï¸ Vidas</p>
                <p style="color: #e2e8f0; font-size: 0.9rem; line-height: 1.5; margin: 0 0 10px;">Cada nivel tiene vidas limitadas. Si pierdes todas, debes reiniciar el nivel. Las vidas disminuyen con errores de respuesta.</p>
                
                <p style="color: #94a3b8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin: 12px 0 4px;">â±ï¸ Tiempo de Respuesta</p>
                <p style="color: #e2e8f0; font-size: 0.9rem; line-height: 1.5; margin: 0 0 10px;">El slider indica cuÃ¡nto tardas en responder. Regla de oro: responde igual o mÃ¡s tarde que ella. <strong style="color: #ff3c6e;">Nunca respondas de inmediato.</strong></p>
                
                <p style="color: #94a3b8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin: 12px 0 4px;">ðŸ’¬ El Coach</p>
                <p style="color: #e2e8f0; font-size: 0.9rem; line-height: 1.5; margin: 0 0 10px;">DespuÃ©s de cada respuesta, el Coach te explica exactamente quÃ© hiciste bien o mal y cÃ³mo mejorar.</p>
                
                <p style="color: #94a3b8; font-size: 0.82rem; font-weight: 600; text-transform: uppercase; margin: 12px 0 4px;">ðŸŒŸ AtracciÃ³n</p>
                <p style="color: #e2e8f0; font-size: 0.9rem; line-height: 1.5; margin: 0 0 16px;">La barra de atracciÃ³n sube con respuestas perfectas y baja con errores. Comienza al 50%.</p>
                
                <button id="btn-close-help" class="btn-premium" style="margin-top: 4px;">ENTENDIDO ðŸ‘</button>
            </div>
        </div>

        <!-- COACH FEEDBACK OVERLAY -->
        <div class="modal-overlay" id="modal-overlay">
            <div class="coach-modal">
                <div class="coach-header">
                    <div class="coach-avatar"><img id="coach-img-el" src="" alt="Coach"></div>
                    <div>
                        <h3 id="coach-title" style="margin: 0; font-family: Outfit; font-size: 1.15rem; color: #ff3c6e;">Coach Feedback</h3>
                        <span style="font-size: 0.72rem; color: var(--text-secondary);">Natalia-Coach</span>
                    </div>
                </div>
                <div class="coach-message" id="coach-msg-text"></div>
                <button class="btn-close-modal" id="btn-close-modal">ENTENDIDO</button>
            </div>
        </div>
        
    </div>

    <script>
        {js_final}
    </script>
</body>
</html>
"""

    # Guardar el simulador principal en el directorio raiz.
    output_html_path = os.path.join(project_root, "simulador_v1.2.html")
    html = repair_mojibake_text(html)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Compilador completado con exito. Simulador guardado en: {output_html_path}")

if __name__ == "__main__":
    main()
