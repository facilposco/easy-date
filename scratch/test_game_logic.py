import json
import os
import sys

# Reconfigurar salida estándar para UTF-8 para soportar emojis en Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

def test_dialogue_logic():
    json_path = r"C:\desarrollos\antigravity\text game youtube estudio ejemplos\scratch\game_dialogues.json"
    
    if not os.path.exists(json_path):
        print(f"ERROR: No se encontró el archivo JSON en {json_path}")
        return False
        
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR al parsear JSON: {e}")
        return False
        
    print("--- INICIANDO TEST DE INTEGRIDAD DEL SIMULADOR V2 ---")
    print(f"Título del Juego: {data.get('game_title')}\n")
    
    valid_times = {"inmediato", "15 min", "45 min", "1 hora", "4 horas", "espejeo"}
    errors = 0
    warnings = 0
    
    levels = data.get("levels", [])
    print(f"Total de niveles encontrados: {len(levels)}")
    
    if len(levels) == 0:
        print("ERROR: El archivo JSON no tiene niveles definidos.")
        errors += 1
        
    for lvl in levels:
        lvl_id = lvl.get("level_id")
        lvl_name = lvl.get("name")
        girl_name = lvl.get("girl_name")
        steps = lvl.get("steps", [])
        
        print(f"\n[Nivel {lvl_id}] Girl: {girl_name} | {lvl_name}")
        print(f"  Pasos: {len(steps)}")
        
        if not girl_name:
            print(f"  ERROR: Nivel {lvl_id} no tiene definido 'girl_name'.")
            errors += 1
            
        if len(steps) == 0:
            print(f"  ERROR: Nivel {lvl_id} no tiene pasos.")
            errors += 1
            
        for step in steps:
            step_id = step.get("step_id")
            her_msg = step.get("her_message")
            her_time = step.get("her_time")
            options = step.get("options", [])
            
            print(f"  - Paso {step_id}:")
            print(f"    Ella responde: \"{her_msg[:40]}...\" (Tardó: {her_time})")
            
            # Verificar opciones
            correct_count = 0
            for i, opt in enumerate(options):
                text = opt.get("text")
                is_correct = opt.get("is_correct")
                req_time = opt.get("required_time")
                impact = opt.get("investment_impact")
                feedback = opt.get("coach_feedback")
                
                # Validar tiempo
                if req_time not in valid_times:
                    print(f"    ERROR: Opción {i+1} del Paso {step_id} requiere tiempo '{req_time}' que NO existe en el slider.")
                    errors += 1
                
                if is_correct:
                    correct_count += 1
                    # Comprobaciones adicionales para la correcta
                    if impact <= 0:
                        print(f"    WARNING: La opción correcta {i+1} tiene impacto no positivo ({impact}).")
                        warnings += 1
                else:
                    if impact > 0:
                        print(f"    WARNING: Opción incorrecta {i+1} tiene impacto positivo ({impact}).")
                        warnings += 1
                        
            if correct_count == 0:
                print(f"    ERROR: Paso {step_id} no tiene ninguna opción correcta (is_correct=True).")
                errors += 1
            elif correct_count > 1:
                print(f"    ERROR: Paso {step_id} tiene múltiples opciones correctas ({correct_count}).")
                errors += 1
                
    print("\n--- RESUMEN DE TEST ---")
    print(f"Errores encontrados: {errors}")
    print(f"Advertencias encontradas: {warnings}")
    
    if errors == 0:
        print("¡TODO EXCELENTE! La base de diálogos del juego está al 100% libre de errores lógicos.")
        return True
    else:
        print("SE DETECTARON ERRORES QUE DEBEN CORREGIRSE.")
        return False

if __name__ == "__main__":
    test_dialogue_logic()
