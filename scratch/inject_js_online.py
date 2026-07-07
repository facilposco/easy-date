import sys
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "simulador_v1.2.html"

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# ====================================================================
# Inject the AI health check + online/offline logic + enter key fix
# at the END of the script, just before </script>
# ====================================================================

JS_ADDITIONS = """
    // ================================================================
    // AI STATUS CHECKER - Online / Offline Indicator
    // ================================================================
    let AI_ONLINE = false;

    async function checkAIStatus() {
        const indicator = document.getElementById('ai-status-indicator');
        try {
            const response = await fetch(BACKEND_URL.replace('/api/evaluate', '/health'), {
                method: 'GET',
                signal: AbortSignal.timeout(3000)
            });
            if (response.ok) {
                AI_ONLINE = true;
                indicator.className = 'online';
                indicator.innerHTML = '<span class="dot"></span>ONLINE';
                // Re-enable send button if it was blocked
                const btn = document.getElementById('btn-send');
                if (btn) btn.disabled = false;
                // Remove offline overlay if present
                const overlay = document.querySelector('.input-disabled-overlay');
                if (overlay) overlay.remove();
            } else {
                setOffline(indicator);
            }
        } catch (e) {
            // Also try /api/evaluate with HEAD (some servers don't have /health)
            try {
                const response2 = await fetch(BACKEND_URL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ level: 1, history: [], user_message: 'ping' }),
                    signal: AbortSignal.timeout(3000)
                });
                if (response2.ok) {
                    AI_ONLINE = true;
                    indicator.className = 'online';
                    indicator.innerHTML = '<span class="dot"></span>ONLINE';
                    const btn = document.getElementById('btn-send');
                    if (btn) btn.disabled = false;
                    const overlay = document.querySelector('.input-disabled-overlay');
                    if (overlay) overlay.remove();
                    return;
                }
            } catch (e2) {}
            setOffline(indicator);
        }
    }

    function setOffline(indicator) {
        AI_ONLINE = false;
        if (indicator) {
            indicator.className = 'offline';
            indicator.innerHTML = '<span class="dot"></span>OFFLINE';
        }
        // Disable send button
        const btn = document.getElementById('btn-send');
        if (btn) {
            btn.disabled = true;
            btn.title = 'Servidor de IA desconectado';
        }
        // Show overlay on input wrapper
        const wrapper = document.querySelector('.input-wrapper');
        if (wrapper && !wrapper.querySelector('.input-disabled-overlay')) {
            const overlay = document.createElement('div');
            overlay.className = 'input-disabled-overlay';
            overlay.innerHTML = '⚡ IA Desconectada — Inicia el servidor para jugar';
            wrapper.appendChild(overlay);
        }
    }

    // Run check every 5 seconds
    checkAIStatus();
    setInterval(checkAIStatus, 5000);

    // ================================================================
    // ENTER KEY - Send message with Enter, new line with Shift+Enter
    // ================================================================
    document.addEventListener('DOMContentLoaded', () => {
        const textarea = document.getElementById('user-free-text');
        if (textarea) {
            textarea.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    if (!AI_ONLINE) return; // Block if offline
                    const btn = document.getElementById('btn-send');
                    if (btn && !btn.disabled) btn.click();
                }
            });
            // Auto-resize textarea as user types
            textarea.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 100) + 'px';
            });
        }
    });
"""

# Find the closing </script> and insert before it
last_script_close = content.rfind("</script>")
if last_script_close != -1:
    # Make sure we don't insert in the TINDER UI block we added before
    # (which already has </script> at the end too if any)
    content = content[:last_script_close] + JS_ADDITIONS + "\n    </script>" + content[last_script_close + len("</script>"):]
    print("JS online/offline + Enter key logic injected.")
else:
    print("ERROR: </script> not found!")

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("DONE.")
