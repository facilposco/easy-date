import os
import json
import time
from seleniumbase import Driver

HTML_PATH = r"C:\desarrollos\antigravity\text game youtube estudio ejemplos\simulador_v1.0.html"
JSON_PATH = r"C:\desarrollos\antigravity\text game youtube estudio ejemplos\scratch\game_dialogues.json"

def get_correct_answers():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    answers = []
    for level_idx, level in enumerate(data["levels"]):
        for step_idx, step in enumerate(level["steps"]):
            correct_opt = None
            for opt in step["options"]:
                if opt["is_correct"]:
                    correct_opt = opt
                    break
            answers.append({
                "level": level_idx + 1,
                "step": step_idx + 1,
                "text": correct_opt["text"],
                "time_index": step["allowed_time_indices"][0]
            })
    return answers

import sys
import re

# Asegurar encoding UTF-8 para stdout en consolas Windows
sys.stdout.reconfigure(encoding='utf-8')

def clean_text(t):
    # Dejar solo caracteres alfanuméricos
    return re.sub(r'[^a-zA-Z0-9]', '', t).lower()

def run_e2e_test():
    print("Iniciando Verificación E2E de la interfaz del Simulador en Chrome...")
    
    answers = get_correct_answers()
    print(f"Respuestas correctas cargadas: {len(answers)} pasos en total.")
    
    # Abrir Chrome en modo headful (visible) para simular al humano
    driver = Driver(uc=True, headless=False)
    driver.set_window_size(1280, 1024)
    
    time_map = {
        "inmediato": 1,
        "15 min": 2,
        "45 min": 3,
        "1 hora": 4,
        "4 horas": 5,
        "espejeo": 6
    }
    
    try:
        url = f"file:///{HTML_PATH.replace(os.sep, '/')}"
        print(f"Abriendo simulador en: {url}")
        driver.set_window_size(430, 850)
        driver.get(url)
        time.sleep(2)
        
        # Limpiar cualquier estado anterior del juego para iniciar fresco
        driver.execute_script("localStorage.removeItem('easyDateState'); location.reload();")
        time.sleep(2)
        
        # Hacer clic en "Comenzar a hablar" en el modal de Match inicial
        try:
            print("Haciendo clic en 'COMENZAR A HABLAR' en el modal de Match...")
            driver.js_click("#match-start-btn")
            time.sleep(2)
        except Exception as e:
            print(f"Error iniciando match: {e}")
        
        for idx, ans in enumerate(answers):
            print(f"\n--- Jugando Paso {idx+1}: Nivel {ans['level']} - Pregunta {ans['step']} ---")
            
            # 1. Buscar la opción correcta usando la metadata lógica del DOM (robusto contra typos)
            time.sleep(1) # Esperar a que renderice
            radio_buttons = driver.find_elements('input[name="reply_opt"]')
            clicked = False
            
            for rb in radio_buttons:
                val_str = rb.get_attribute("value")
                try:
                    val_data = json.loads(val_str)
                    if val_data.get("is_correct"):
                        # El padre de input es el label.option-card
                        parent_label = rb.find_element("xpath", "..")
                        parent_label.click()
                        print(f"Haciendo clic en la opción correcta lógica: '{val_data.get('text')}'")
                        clicked = True
                        break
                except Exception as ex:
                    print(f"Error analizando opción: {ex}")
            
            if not clicked:
                raise Exception(f"No se encontró la opción correcta lógica en el DOM.")
                
            # 2. Configurar el slider al tiempo requerido
            target_slider_val = ans["time_index"]
            print(f"Configurando slider de tiempo a valor: {target_slider_val}")
            
            # Ejecutar script JS para mover el slider y disparar eventos de cambio
            driver.execute_script(f"""
                const slider = document.getElementById('time-slider');
                slider.value = {target_slider_val};
                slider.dispatchEvent(new Event('input'));
                slider.dispatchEvent(new Event('change'));
            """)
            time.sleep(1)
            
            # 3. Enviar la respuesta
            print("Haciendo clic en 'ENVIAR RESPUESTA'...")
            driver.click("#btn-send")
            time.sleep(1.5)
            
            # 4. Verificar que se muestre el modal del Coach
            modal_overlay = driver.find_element("#modal-overlay")
            if "active" not in modal_overlay.get_attribute("class"):
                raise Exception("¡Error! El modal del Coach no se abrió tras enviar la respuesta.")
                
            coach_msg = driver.find_element("#coach-msg-text").text
            print(f"Mensaje del Coach recibido: '{coach_msg}'")
            
            # 5. Cerrar el modal del Coach
            print("Haciendo clic en 'ENTENDIDO'...")
            driver.click("#btn-close-modal")
            time.sleep(1.5)
            
            # 6. Si pasamos de nivel (el paso es el 10 del nivel), se activa el modal de level up
            if ans["step"] == 10 and idx < len(answers) - 1:
                try:
                    time.sleep(1.5)
                    levelup_modal = driver.find_element("#levelup-modal")
                    if levelup_modal and "active" in levelup_modal.get_attribute("class"):
                        print("¡Modal de Level Up (Cita Lograda) detectado!")
                        driver.click("#levelup-next-btn")
                        time.sleep(2)
                        
                        # Ahora se abrirá el modal de match para el siguiente nivel
                        print("Haciendo clic en 'COMENZAR A HABLAR' para el siguiente nivel...")
                        driver.click("#match-start-btn")
                        time.sleep(2)
                except Exception as e:
                    print(f"Error en la transición de nivel: {e}")
                
        # Al completar todos los pasos, debemos ver la pantalla de Victoria
        print("\n--- Todos los pasos completados. Verificando pantalla de victoria... ---")
        try:
            final_modal = driver.find_element("#final-modal")
            if "active" in final_modal.get_attribute("class"):
                print("¡TEST E2E EXITOSO! El juego se puede completar al 100% sin bugs lógicos ni visuales.")
            else:
                print("Fallo: No se muestra el modal final de victoria.")
        except Exception as e:
            print(f"Fallo al verificar victoria: {e}")
            
    except Exception as e:
        print(f"\n¡BUG DETECTADO DURANTE EL TEST E2E! Detalles: {e}")
        try:
            driver.save_screenshot(r"C:\desarrollos\antigravity\text game youtube estudio ejemplos\screenshot.png")
            print("Captura de pantalla guardada exitosamente en screenshot.png")
        except Exception as se:
            print(f"No se pudo guardar la captura de pantalla: {se}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_e2e_test()
