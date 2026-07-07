import sys
import os
import json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from process_helper import save_case

def main():
    with open("scratch/temp_post.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    save_case(
        post_id=data["post_id"],
        title_es=data["titulo"],
        resumen_estrategico=data["resumen_estrategico"],
        scoring=data["scoring"],
        justificacion_scoring=data["justificacion_scoring"],
        mensajes=data["mensajes"],
        girl_profile_type=data["girl_profile_type"],
        transcription_text=data["transcription_text"]
    )

if __name__ == "__main__":
    main()
