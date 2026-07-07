import os
import re

file_path = "c:/desarrollos/antigravity/text game youtube estudio ejemplos/simulador_v1.2.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the slider logic entirely from window.onload
slider_logic = """        // Manejador del Slider Ticks — bloquear índice 0 (Ahora mismo)
        const slider = document.getElementById('time-slider');
        slider.addEventListener('input', (e) => {
            let val = parseInt(e.target.value);
            if (val === 0) {
                val = 1; // Nunca permitir 'Ahora mismo'
                slider.value = 1;
            }
            document.getElementById('slider-time-display').innerText = TIME_TICKS[val];
        });
        // Forzar valor mínimo en 1 al cargar
        slider.value = 1;
        document.getElementById('slider-time-display').innerText = TIME_TICKS[1];"""

content = content.replace(slider_logic, "")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Slider logic removed.")
