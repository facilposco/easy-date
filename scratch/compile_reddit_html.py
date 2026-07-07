import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def compile_reddit_html():
    metadata_file = "scratch/reddit_metadata.json"
    if not os.path.exists(metadata_file):
        logging.error("No existe el archivo reddit_metadata.json")
        return
        
    with open(metadata_file, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    cases = []
    for item in metadata:
        idx = item["id"]
        transcription_file = f"scratch/transcription_{idx}.json"
        if os.path.exists(transcription_file):
            try:
                with open(transcription_file, "r", encoding="utf-8") as f:
                    case_data = json.load(f)
                    # Combinar metadatos de descarga con transcripción
                    item.update(case_data)
                    cases.append(item)
            except Exception as e:
                logging.error(f"Error leyendo transcripción {idx}: {e}")
        else:
            logging.warning(f"No se encontró transcripción para post {idx}")
            
    if not cases:
        logging.error("No hay casos de Reddit transcribidos para compilar.")
        return
        
    html_template = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Estudio Reddit: {len(cases)} Casos Reales de Tinder</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #0d1117;
            --bg-panel: #161b22;
            --text-main: #c9d1d9;
            --text-muted: #8b949e;
            --accent: #58a6ff;
            --border: #30363d;
            --bubble-me: #1d4ed8;  /* Azul Hombre */
            --bubble-her: #be185d; /* Rosado Mujer */
        }}
        body {{
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            margin: 0;
            padding: 20px 10px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{ color: #fff; }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 20px;
            background: linear-gradient(145deg, var(--bg-panel), #000);
            border-radius: 12px;
            border-bottom: 3px solid var(--accent);
        }}
        .header h1 {{ font-size: 1.8rem; margin-top:0; }}
        
        .legend {{
            background: var(--bg-panel);
            padding: 15px;
            border-radius: 12px;
            border: 1px solid var(--border);
            margin-bottom: 30px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
            font-size: 0.9rem;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
        }}
        .color-box {{
            width: 16px;
            height: 16px;
            border-radius: 4px;
            margin-right: 8px;
        }}
        .c-me {{ background: var(--bubble-me); }}
        .c-her {{ background: var(--bubble-her); }}
        
        .case-card {{
            background: var(--bg-panel);
            border-radius: 12px;
            margin-bottom: 35px;
            border: 1px solid var(--border);
            overflow: hidden;
        }}
        .case-header {{
            background: rgba(255,255,255,0.02);
            padding: 15px;
            border-bottom: 1px solid var(--border);
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 10px;
        }}
        .case-title {{ margin: 0; font-size: 1.1rem; }}
        .score-badge {{
            background: rgba(59, 130, 246, 0.2);
            color: var(--accent);
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: bold;
            font-size: 0.85rem;
        }}
        
        .split-container {{
            display: flex;
            flex-direction: column;
            background: #010409;
        }}
        @media (min-width: 768px) {{
            .split-container {{
                flex-direction: row;
            }}
        }}
        
        .screenshot-side {{
            flex: 1;
            padding: 15px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-bottom: 1px solid var(--border);
        }}
        @media (min-width: 768px) {{
            .screenshot-side {{
                border-bottom: none;
                border-right: 1px solid var(--border);
            }}
        }}
        
        .screenshot-side img {{
            max-width: 100%;
            max-height: 450px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            transition: transform 0.3s;
            cursor: zoom-in;
        }}
        .screenshot-side img:hover {{
            transform: scale(1.02);
        }}
        
        .chat-side {{
            flex: 1;
            padding: 20px 15px;
            display: flex;
            flex-direction: column;
            gap: 12px;
            overflow-y: auto;
            max-height: 450px;
        }}
        
        .message-row {{
            display: flex;
            width: 100%;
        }}
        .msg-me {{ justify-content: flex-end; }}
        .msg-her {{ justify-content: flex-start; }}
        
        .bubble {{
            max-width: 85%;
            padding: 10px 14px;
            border-radius: 16px;
            font-size: 0.9rem;
            word-wrap: break-word;
        }}
        .msg-me .bubble {{
            background: var(--bubble-me);
            color: #fff;
            border-bottom-right-radius: 4px;
        }}
        .msg-her .bubble {{
            background: var(--bubble-her);
            color: #fff;
            border-bottom-left-radius: 4px;
        }}
        
        .justification {{
            padding: 15px;
            background: rgba(59, 130, 246, 0.05);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
        }}
        
        .link-source {{
            margin-top: 8px;
            font-size: 0.8rem;
            color: var(--accent);
            text-decoration: none;
            display: inline-block;
        }}
        .link-source:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Estudio Reddit: {len(cases)} Casos Reales</h1>
            <p style="font-size: 0.9rem; color: var(--text-muted);">Capturas de Pantalla Originales + Traducción Rigurosa</p>
        </div>

        <div class="legend">
            <div class="legend-item"><div class="color-box c-me"></div> Hombre (Emisor)</div>
            <div class="legend-item"><div class="color-box c-her"></div> Mujer (Receptora)</div>
        </div>

        <div id="cases-container">
"""
    
    for case in cases:
        title = case.get("title", "Post de Reddit")
        img_path = case.get("image_path", "")
        post_url = case.get("post_url", "#")
        score = case.get("scoring", 0)
        just = case.get("justificacion_scoring", "")
        
        html_template += f"""
            <div class="case-card">
                <div class="case-header">
                    <h3 class="case-title">{title}</h3>
                    <div class="score-badge">Scoring: {score}/10</div>
                </div>
                <div class="split-container">
                    <div class="screenshot-side">
                        <a href="{img_path}" target="_blank">
                            <img src="{img_path}" alt="Captura Original de Reddit">
                        </a>
                        <a class="link-source" href="{post_url}" target="_blank">🔗 Ver post original en Reddit</a>
                    </div>
                    <div class="chat-side">
        """
        
        for msg in case.get("mensajes", []):
            autor = msg.get("autor", "El").lower()
            is_me = autor in ["el", "él", "yo", "me", "emisor", "coach"]
            row_class = "msg-me" if is_me else "msg-her"
            texto = msg.get("texto", "").replace('"', '&quot;')
            
            html_template += f"""
                <div class="message-row {row_class}">
                    <div class="bubble">
                        {texto}
                    </div>
                </div>
            """
            
        html_template += f"""
                    </div>
                </div>
                <div class="justification">
                    <strong>Análisis Técnico:</strong> {just}
                </div>
            </div>
        """
        
    html_template += """
        </div>
    </div>
</body>
</html>
"""
    
    output_file = "reddit.html"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_template)
    logging.info(f"✅ HTML de Reddit compilado con éxito: {output_file}")

if __name__ == "__main__":
    compile_reddit_html()
