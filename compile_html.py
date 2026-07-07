import os
import json
import logging
import base64
import mimetypes
from io import BytesIO
from PIL import Image

compression_stats = []

def image_to_base64(filepath):
    if not os.path.exists(filepath):
        return filepath
    
    try:
        original_size = os.path.getsize(filepath)
        
        with Image.open(filepath) as img:
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            max_width = 420
            if img.width > max_width:
                ratio = max_width / float(img.width)
                new_height = int((float(img.height) * float(ratio)))
                img = img.resize((max_width, new_height), Image.Resampling.LANCZOS)
            
            buffer = BytesIO()
            img.save(buffer, format="JPEG", quality=40, optimize=True)
            compressed_data = buffer.getvalue()
            
        compressed_size = len(compressed_data)
        compression_stats.append({
            'file': os.path.basename(filepath),
            'original': original_size,
            'compressed': compressed_size
        })
        
        encoded = base64.b64encode(compressed_data).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"
    except Exception as e:
        logging.error(f"Error encodeando/comprimiendo imagen {filepath}: {e}")
        return filepath


logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def compile_html():
    parsed_dir = "parsed_cases"
    failed_dir = "failed_cases"
    
    # Cargar éxitos
    exitos = []
    if os.path.exists(parsed_dir):
        for fname in os.listdir(parsed_dir):
            if fname.endswith(".json"):
                with open(os.path.join(parsed_dir, fname), "r", encoding="utf-8") as f:
                    exitos.append(json.load(f))
                    
    # Cargar fails
    fails = []
    if os.path.exists(failed_dir):
        for fname in os.listdir(failed_dir):
            if fname.endswith(".json"):
                with open(os.path.join(failed_dir, fname), "r", encoding="utf-8") as f:
                    fails.append(json.load(f))

    # Cargar Reddit
    reddit_cases = []
    reddit_meta_path = "scratch/reddit_deep_metadata.json"
    if os.path.exists(reddit_meta_path):
        with open(reddit_meta_path, "r", encoding="utf-8") as f:
            reddit_cases = json.load(f)

    # HTML Base
    html_content = """<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>Estudio Text Game - Casos Reales</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #0b0f19;
            --text-color: #f8fafc;
            --accent-color: #3b82f6;
            
            /* Colores oficiales solicitados: morado mujer, azul oscuro hombre */
            --bubble-me: #172554;     /* Azul oscuro */
            --bubble-her: #6b21a8;    /* Morado */
            
            --glass-bg: rgba(30, 41, 59, 0.45);
            --glass-border: rgba(255, 255, 255, 0.08);
            --glass-blur: blur(16px);
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --safe-area-top: env(safe-area-inset-top, 0px);
            --safe-area-bottom: env(safe-area-inset-bottom, 0px);
        }
        
        * {
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }

        body {
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 14px;
            background-color: var(--bg-color);
            background-image: radial-gradient(circle at 50% 0%, #1e293b 0%, #0b0f19 100%);
            background-attachment: fixed;
            color: var(--text-color);
            margin: 0;
            padding: 80px 0 0 0; /* Padding superior para dar espacio a la barra persistente */
            padding-bottom: calc(var(--safe-area-bottom) + 30px);
        }

        /* --- BARRA DE ACCIONES / COMPARTIR --- */
        .action-bar {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border-bottom: 1px solid var(--glass-border);
            padding: 10px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }

        .action-bar-left {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: var(--text-secondary);
        }

        .path-input-container {
            display: flex;
            align-items: center;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--glass-border);
            border-radius: 6px;
            padding: 3px 6px;
            gap: 6px;
        }

        .path-input {
            background: transparent;
            border: none;
            color: #60a5fa;
            font-family: monospace;
            font-size: 0.8rem;
            width: 260px;
            outline: none;
        }

        .action-btn {
            background: #2563eb;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            display: flex;
            align-items: center;
            gap: 4px;
            transition: background 0.2s;
        }

        .action-btn:hover {
            background: #1d4ed8;
        }

        .action-btn.secondary {
            background: rgba(255,255,255,0.08);
            border: 1px solid var(--glass-border);
        }

        .action-btn.secondary:hover {
            background: rgba(255,255,255,0.15);
        }

        .action-bar-right {
            display: flex;
            gap: 8px;
        }

        .header {
            background: rgba(15, 23, 42, 0.45);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border-bottom: 1px solid var(--glass-border);
            padding: 20px 16px;
            text-align: center;
        }

        .header h1 {
            margin: 0;
            font-size: 1.8rem;
            font-family: 'Outfit', sans-serif;
            font-weight: 800;
            background: linear-gradient(135deg, #60a5fa 0%, #2563eb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.02em;
        }

        .tabs {
            display: flex;
            justify-content: center;
            background: rgba(11, 15, 25, 0.85);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border-bottom: 1px solid var(--glass-border);
            padding: calc(var(--safe-area-top) + 8px) 8px 8px 8px;
            position: sticky;
            top: 50px; /* Abajo de la barra persistente */
            z-index: 100;
            gap: 6px;
        }

        .tab-btn {
            background: transparent;
            border: none;
            color: var(--text-secondary);
            padding: 8px 16px;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            border-radius: 10px;
            font-family: 'Outfit', sans-serif;
            transition: all 0.2s ease;
        }

        .tab-btn:hover {
            color: var(--text-primary);
            background: rgba(255, 255, 255, 0.05);
        }

        .tab-btn.active {
            color: #fff;
            background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.35);
            font-weight: 600;
        }

        .search-wrapper {
            max-width: 600px;
            margin: 20px auto 10px auto;
            padding: 0 16px;
        }

        #globalSearchBar {
            width: 100%;
            padding: 10px 14px;
            border-radius: 10px;
            border: 1px solid rgba(255, 255, 255, 0.08);
            background: rgba(15, 23, 42, 0.6);
            color: var(--text-primary);
            font-size: 0.9rem;
            outline: none;
            transition: all 0.3s ease;
        }

        #globalSearchBar:focus {
            border-color: var(--accent-color);
            box-shadow: 0 0 10px rgba(59, 130, 246, 0.2);
        }

        .tab-content {
            display: none;
            padding: 20px 16px;
            max-width: 900px;
            margin: 0 auto;
        }

        .tab-content.active {
            display: block;
        }

        .case-card {
            background: var(--glass-bg);
            backdrop-filter: var(--glass-blur);
            -webkit-backdrop-filter: var(--glass-blur);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            margin-bottom: 24px;
            overflow: hidden;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }

        .case-header {
            padding: 16px 20px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 10px;
        }

        .case-header h2 {
            margin: 0;
            font-size: 1.15rem;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }

        .score {
            display: inline-flex;
            align-items: center;
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
        }

        .score.fail-score {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }

        /* --- SPLIT LAYOUT (REDDIT STYLE) --- */
        .split-container {
            display: flex;
            flex-direction: column;
            background: rgba(0, 0, 0, 0.2);
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        @media (min-width: 768px) {
            .split-container {
                flex-direction: row;
            }
        }

        .screenshot-side {
            flex: 1;
            padding: 15px;
            background: #000;
            max-height: 450px;
            overflow-y: auto;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        }

        /* Ocultar barra de scroll para vista limpia pero permitir scroll táctil */
        .screenshot-side::-webkit-scrollbar {
            width: 6px;
        }
        .screenshot-side::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }

        @media (min-width: 768px) {
            .screenshot-side {
                border-bottom: none;
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }
        }

        .screenshot-side img {
            width: 100%;
            height: auto;
            display: block;
            margin: 0 auto;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            cursor: zoom-in;
            transition: transform 0.2s;
        }

        .screenshot-side img:hover {
            transform: scale(1.02);
        }

        .chat-side {
            flex: 1;
            padding: 20px 15px;
            display: flex;
            flex-direction: column;
            gap: 10px;
            overflow-y: auto;
            max-height: 450px;
            background: rgba(15, 23, 42, 0.3);
        }

        /* --- BUBBLE STYLE --- */
        .chat-container {
            padding: 20px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .bubble {
            max-width: 75%;
            padding: 10px 14px;
            border-radius: 16px;
            font-size: 0.85rem;
            line-height: 1.4;
            word-wrap: break-word;
            box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
            position: relative;
        }

        /* Alineaciones y Colores consistentes */
        .bubble.me, .bubble.fail-me {
            background: var(--bubble-me);
            color: white;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .bubble.her, .bubble.fail-her {
            background: var(--bubble-her);
            color: white;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }

        .msg-time {
            font-size: 0.65rem;
            color: rgba(255,255,255,0.4);
            margin-top: 5px;
            font-family: monospace;
        }
        .bubble.me .msg-time, .bubble.fail-me .msg-time {
            text-align: right;
        }
        .bubble.her .msg-time, .bubble.fail-her .msg-time {
            text-align: left;
        }

        /* Detalles extras de Fails */
        .breaking-point {
            background: rgba(239, 68, 68, 0.06);
            border-left: 4px solid #ef4444;
            border-radius: 0 10px 10px 0;
            padding: 14px;
            margin-top: 15px;
            font-size: 0.85rem;
            border: 1px solid rgba(239, 68, 68, 0.15);
            border-left-width: 0;
        }

        .breaking-point h4 {
            margin: 0 0 6px 0;
            color: #f87171;
            font-family: 'Outfit', sans-serif;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.05em;
        }

        .breaking-point p {
            margin: 4px 0;
            line-height: 1.35;
            color: #cbd5e1;
        }

        .breaking-point strong {
            color: #fca5a5;
        }

        .justification {
            padding: 15px 20px;
            background: rgba(59, 130, 246, 0.05);
            font-size: 0.85rem;
            border-top: 1px solid rgba(255,255,255,0.05);
            color: #cbd5e1;
        }

        /* --- CAROUSEL SCROLL HORIZONTAL NATIVO --- */
        .carousel-container-horizontal {
            display: flex;
            overflow-x: auto;
            scroll-snap-type: x mandatory;
            -webkit-overflow-scrolling: touch;
            width: 100%;
            max-height: 450px;
            background: #000;
            gap: 10px;
            padding: 10px;
        }
        
        .carousel-container-horizontal::-webkit-scrollbar {
            height: 6px;
        }
        
        .carousel-container-horizontal::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 3px;
        }
        
        .carousel-slide-horizontal {
            flex: 0 0 100%;
            scroll-snap-align: start;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .carousel-slide-horizontal img {
            max-width: 100%;
            max-height: 420px;
            object-fit: contain;
            border-radius: 8px;
            cursor: zoom-in;
        }

        /* --- LIGHTBOX MODAL --- */
        .lightbox-modal {
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.95);
            justify-content: center;
            align-items: center;
        }

        .lightbox-content {
            max-width: 90%;
            max-height: 90%;
            object-fit: contain;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(255,255,255,0.1);
            animation: zoom 0.2s ease;
        }

        @keyframes zoom {
            from { transform: scale(0.9); opacity: 0; }
            to { transform: scale(1); opacity: 1; }
        }

        .lightbox-close {
            position: absolute;
            top: 20px;
            right: 30px;
            color: #fff;
            font-size: 35px;
            font-weight: bold;
            cursor: pointer;
        }

        /* --- MANUAL TAB STYLING --- */
        .manual-section {
            margin-bottom: 30px;
        }
        
        .manual-section h2 {
            font-family: 'Outfit', sans-serif;
            color: #fff;
            border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            padding-bottom: 8px;
            margin-top: 30px;
        }

        .manual-section h3 {
            color: #60a5fa;
            font-size: 1.1rem;
            margin-top: 20px;
        }

        .manual-index {
            background: rgba(15, 23, 42, 0.6);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 12px;
            padding: 15px;
            margin-bottom: 25px;
        }

        .manual-index h3 {
            margin-top: 0;
            color: #fff;
            font-size: 1rem;
        }

        .manual-index ul {
            padding-left: 20px;
            margin: 0;
        }

        .manual-index li {
            margin-bottom: 6px;
        }

        .manual-index a {
            color: #60a5fa;
            text-decoration: none;
        }

        .manual-index a:hover {
            text-decoration: underline;
        }

        .formula-box {
            background: rgba(59, 130, 246, 0.1);
            border-left: 4px solid #3b82f6;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
            font-family: monospace;
            font-size: 1rem;
            margin: 15px 0;
            color: #93c5fd;
        }

        .grid-2 {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
        }

        @media (min-width: 768px) {
            .grid-2 {
                grid-template-columns: 1fr 1fr;
            }
        }

        /* Viewport limits for iPhone 15 & mobile */
        @media (max-width: 480px) {
            body {
                padding-top: 110px;
            }
            .action-bar {
                flex-direction: column;
                gap: 8px;
                align-items: stretch;
            }
            .action-bar-right {
                justify-content: flex-end;
            }
            .path-input {
                width: 100%;
            }
            .tab-content {
                padding: 12px 8px;
            }
            .case-card {
                margin-bottom: 16px;
                border-radius: 12px;
            }
            .case-header {
                padding: 12px 15px;
            }
            .case-header h2 {
                font-size: 1rem;
            }
            .bubble {
                max-width: 82%;
                font-size: 0.8rem;
                padding: 8px 12px;
            }
            .tab-btn {
                padding: 6px 10px;
                font-size: 0.8rem;
            }
        }
    </style>
</head>
<body>

    <div class="header">
        <h1>Text Game: Casos Reales</h1>
    </div>

    <div class="tabs">
        <button class="tab-btn" onclick="if(window.parent && typeof window.parent.showScreen === 'function') { window.parent.showScreen('game'); } else { alert('Simulador no disponible en modo independiente.'); }" style="background: linear-gradient(135deg, #ff3c6e 0%, #ff7854 100%); color: white; font-weight: 800; border: none; box-shadow: 0 4px 12px rgba(255, 60, 110, 0.3);">🎮 Ir al Simulador</button>
        <button class="tab-btn active" onclick="openTab(event, 'tab-exitos')">Éxitos (YouTube)</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-fails')">Fails (YouTube)</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-reddit')">Reddit (Top)</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-favoritos')">⭐ Mis Favoritos</button>
        <button class="tab-btn" onclick="openTab(event, 'tab-manual')">Guía de Natalia</button>
    </div>

    <!-- BUSCADOR GLOBAL -->
    <div class="search-wrapper">
        <input type="text" id="globalSearchBar" onkeyup="filterCasesGlobal()" placeholder="🔍 Buscar por título, palabra o concepto en esta pestaña...">
    </div>

    <!-- PESTAÑA ÉXITOS -->
    <div id="tab-exitos" class="tab-content active">
        <div id="exitos-list">
"""

    # Inyectar éxitos
    for idx, caso in enumerate(exitos, 1):
        score = caso.get('scoring', '?')
        titulo = caso.get('titulo') or f"Conversación {caso.get('video_id', '')}"
        analisis = caso.get('resumen_estrategico') or caso.get('justificacion_scoring', '')
        html_content += f"""
        <div class="case-card">
            <div class="case-header">
                <h2>#{idx} - {titulo} <span class="score">Score: {score}/10</span></h2>
            </div>
            <div class="justification" style="border-top: none; border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(16, 185, 129, 0.05);">
                <strong>Análisis Estratégico:</strong> {analisis}
            </div>
            <div class="chat-container">
"""
        mensajes = caso.get('mensajes', [])
        if not mensajes and 'fases' in caso:
            for fase in caso['fases']:
                mensajes.extend(fase.get('mensajes', []))
                
        for msg in mensajes:
            autor = msg.get('autor', 'Ella')
            raw_texto = msg.get('texto')
            tiempo = msg.get('tiempo', 'N/A')
            texto = (raw_texto if raw_texto else '').replace('"', '&quot;')
            clase = "me" if autor.lower() in ['el', 'él'] else "her"
            # Solo mostrar tiempo si hay dato real (no N/A)
            tiempo_html = f'<div class="msg-time">⏱️ {tiempo}</div>' if tiempo and tiempo.strip() not in ('N/A', '', 'n/a', 'na') else ''
            html_content += f'<div class="bubble {clase}">{texto}{tiempo_html}</div>\n'
        
        html_content += f"""
            </div>
        </div>
"""

    html_content += """
        </div>
    </div>

    <!-- PESTAÑA FAILS -->
    <div id="tab-fails" class="tab-content">
        <div style="background: rgba(239, 68, 68, 0.08); padding: 15px; border-radius: 12px; margin-bottom: 20px; border: 1px solid rgba(239, 68, 68, 0.15);">
            <h3 style="margin-top:0; color: #f87171; font-family: 'Outfit';">El Cementerio de Chats 🪦</h3>
            <p style="font-size: 0.85rem; margin-bottom:0; color:#cbd5e1;">Esta galería muestra anti-patrones y errores fatales de interacciones reales analizados por la IA. El Punto de Quiebre explica la solución recomendada.</p>
        </div>
        <div id="fails-list">
"""

    # Inyectar Fails
    for idx, caso in enumerate(fails, 1):
        analisis = caso.get('justificacion_error', '')
        html_content += f"""
        <div class="case-card">
            <div class="case-header">
                <h2>#{idx} - {caso.get('error_tipo', 'Error Desconocido')} <span class="score fail-score">FAIL</span></h2>
            </div>
            <div class="justification" style="border-top: none; border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(239, 68, 68, 0.05);">
                <strong>Análisis Crítico:</strong> {analisis}
            </div>
            <div class="chat-container">
"""
        punto = caso.get('punto_quiebre', {})
        for msg in caso.get('mensajes', []):
            autor = msg.get('autor', 'Ella')
            clase = "fail-me" if autor.lower() in ['el', 'él'] else "fail-her"
            texto = msg.get('texto', '')
            tiempo = msg.get('tiempo', 'N/A')
            tiempo_html = f'<div class="msg-time">⏱️ {tiempo}</div>' if tiempo and tiempo.strip() not in ('N/A', '', 'n/a', 'na') else ''
            html_content += f'<div class="bubble {clase}">{texto}{tiempo_html}</div>\n'
        
        html_content += f"""
                <div class="breaking-point">
                    <h4>Punto de Quiebre</h4>
                    <p><strong>Error:</strong> {punto.get('mensaje_error', '')}</p>
                    <p><strong>Solución:</strong> {punto.get('explicacion', '')}</p>
                </div>
            </div>
        </div>
"""

    html_content += """
        </div>
    </div>

    <!-- PESTAÑA REDDIT -->
    <div id="tab-reddit" class="tab-content">
        
        <h3 style="border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px; font-family: 'Outfit'; font-size:1.3rem;">Conversaciones con 1 Imagen</h3>
"""
    
    # Inyectar Reddit Single
    reddit_single_cases = [c for c in reddit_cases if c['type'] == 'single']
    for idx, caso in enumerate(reddit_single_cases, 1):
        img = caso['image_paths'][0]
        img_b64 = image_to_base64(img)
        reddit_json_path = os.path.join("reddit_cases", f"{caso['id']}.json")
        
        score = "?"
        resumen = ""
        mensajes_html = ""
        titulo_analizado = caso['title']
        
        if os.path.exists(reddit_json_path):
            try:
                with open(reddit_json_path, "r", encoding="utf-8") as f:
                    r_data = json.load(f)
                    score = r_data.get("scoring", "?")
                    resumen = r_data.get("resumen_estrategico", "")
                    if "titulo" in r_data and r_data["titulo"]:
                        titulo_analizado = r_data["titulo"]
                        
                    for msg in r_data.get("mensajes", []):
                        autor = msg.get('autor', 'Ella')
                        raw_texto = msg.get('texto')
                        tiempo = msg.get('tiempo', 'N/A')
                        texto = (raw_texto if raw_texto else '').replace('"', '&quot;')
                        clase = "me" if autor.lower() in ['el', 'él'] else "her"
                        # Solo mostrar tiempo si hay dato real
                        tiempo_html = f'<div class="msg-time">⏱️ {tiempo}</div>' if tiempo and tiempo.strip() not in ('N/A', '', 'n/a', 'na') else ''
                        mensajes_html += f'<div class="bubble {clase}">{texto}{tiempo_html}</div>\n'
            except:
                pass

        html_content += f"""
        <div class="case-card" data-post-id="{caso['id']}">
            <div class="case-header">
                <h2>#{idx} - {titulo_analizado} <span class="score">Score: {score}/10</span></h2>
                <a href="{caso['post_url']}" target="_blank" style="color: #60a5fa; font-size: 0.8rem; text-decoration: none;">🔗 Ver post</a>
            </div>
            <div class="justification" style="border-top: none; border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(59, 130, 246, 0.05);">
                <strong>Análisis Estratégico:</strong> {resumen}
            </div>
            <div class="split-container">
                <div class="screenshot-side">
                    <img class="reddit-img" src="{img_b64}" alt="Captura Original de Reddit" onclick="openLightbox('{img_b64}')">
                </div>
                <div class="chat-side">
                    {mensajes_html}
                </div>
            </div>
            <div class="fav-bar" style="display:flex; gap:8px; padding:10px 16px; border-top: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.15);">
                <button onclick="toggleFav('{caso['id']}', 'like', this)" class="fav-btn" id="fav-like-{caso['id']}" style="flex:1; padding:6px; border-radius:8px; border: 1px solid rgba(255,255,255,0.1); background:rgba(16,185,129,0.1); color:#10b981; font-size:1rem; cursor:pointer; transition: all 0.2s;">👍 Me Gustó</button>
                <button onclick="toggleFav('{caso['id']}', 'dislike', this)" class="fav-btn" id="fav-dislike-{caso['id']}" style="flex:1; padding:6px; border-radius:8px; border: 1px solid rgba(255,255,255,0.1); background:rgba(239,68,68,0.1); color:#ef4444; font-size:1rem; cursor:pointer; transition: all 0.2s;">👎 No Me Gustó</button>
            </div>
        </div>
"""


    html_content += """
        <h3 style="border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 8px; margin-top: 40px; font-family: 'Outfit'; font-size:1.3rem;">Conversaciones con Carrusel (Deslizar horizontalmente)</h3>
"""

    # Inyectar Reddit Multi (Carrusel)
    multi_cases = [c for c in reddit_cases if c['type'] == 'multi']
    if not multi_cases:
        html_content += "<p style='color: var(--text-secondary); text-align: center; margin: 20px 0;'>No se encontraron posts de múltiples imágenes en este momento.</p>"
    for idx, caso in enumerate(multi_cases, 1):
        reddit_json_path = os.path.join("reddit_cases", f"{caso['id']}.json")
        score = "?"
        resumen = ""
        mensajes_html = ""
        titulo_analizado = caso['title']
        
        if os.path.exists(reddit_json_path):
            try:
                with open(reddit_json_path, "r", encoding="utf-8") as f:
                    r_data = json.load(f)
                    score = r_data.get("scoring", "?")
                    resumen = r_data.get("resumen_estrategico", "")
                    if "titulo" in r_data and r_data["titulo"]:
                        titulo_analizado = r_data["titulo"]
                        
                    for msg in r_data.get("mensajes", []):
                        autor = msg.get('autor', 'Ella')
                        raw_texto = msg.get('texto')
                        tiempo = msg.get('tiempo', 'N/A')
                        texto = (raw_texto if raw_texto else '').replace('"', '&quot;')
                        clase = "me" if autor.lower() in ['el', 'él'] else "her"
                        mensajes_html += f'<div class="bubble {clase}">{texto}<div class="msg-time">⏱️ {tiempo}</div></div>\n'
            except Exception as e:
                logging.error(f"Error cargando JSON de Reddit multi: {e}")

        # Generar slides del carrusel scrollable
        carousel_slides_html = ""
        for img in caso['image_paths']:
            img_b64 = image_to_base64(img)
            carousel_slides_html += f"""
            <div class="carousel-slide-horizontal">
                <img class="reddit-img" src="{img_b64}" alt="Reddit Slide" onclick="openLightbox('{img_b64}')">
            </div>
            """

        html_content += f"""
        <div class="case-card" data-post-id="{caso['id']}">
            <div class="case-header">
                <h2>#{idx} - {titulo_analizado} <span class="score">Score: {score}/10</span></h2>
                <a href="{caso['post_url']}" target="_blank" style="color: #60a5fa; font-size: 0.8rem; text-decoration: none;">🔗 Ver post</a>
            </div>
            <div class="justification" style="border-top: none; border-bottom: 1px solid rgba(255,255,255,0.05); background: rgba(59, 130, 246, 0.05);">
                <strong>Análisis Estratégico:</strong> {resumen}
            </div>
            <div class="split-container">
                <div class="screenshot-side">
                    <div class="carousel-container-horizontal">
                        {carousel_slides_html}
                    </div>
                </div>
                <div class="chat-side">
                    {mensajes_html}
                </div>
            </div>
            <div class="fav-bar" style="display:flex; gap:8px; padding:10px 16px; border-top: 1px solid rgba(255,255,255,0.06); background: rgba(0,0,0,0.15);">
                <button onclick="toggleFav('{caso['id']}', 'like', this)" class="fav-btn" id="fav-like-{caso['id']}" style="flex:1; padding:6px; border-radius:8px; border: 1px solid rgba(255,255,255,0.1); background:rgba(16,185,129,0.1); color:#10b981; font-size:1rem; cursor:pointer; transition: all 0.2s;">👍 Me Gustó</button>
                <button onclick="toggleFav('{caso['id']}', 'dislike', this)" class="fav-btn" id="fav-dislike-{caso['id']}" style="flex:1; padding:6px; border-radius:8px; border: 1px solid rgba(255,255,255,0.1); background:rgba(239,68,68,0.1); color:#ef4444; font-size:1rem; cursor:pointer; transition: all 0.2s;">👎 No Me Gustó</button>
            </div>
        </div>
        """


    # PESTAÑA MANUAL / GUÍA DE NATALIA
    html_content += """
    </div>

    <!-- PESTAÑA MANUAL Y TEORÍA REEVALUADA -->
    <div id="tab-manual" class="tab-content">
        <div class="manual-index">
            <h3>Índice de Contenido Técnico</h3>
            <ul>
                <li><a href="#manual-1">1. La Epidemia de Soledad y el Invierno Demográfico</a></li>
                <li><a href="#manual-2">2. La Fórmula Universal del Text Game (O.T.C.) reevaluada</a></li>
                <li><a href="#manual-3">3. Algoritmo de Scoring y Calibración</a></li>
                <li><a href="#manual-4">4. Los 10 Mandamientos del Texting Clínico y Consejos de Élite</a></li>
                <li><a href="#manual-5">5. Bibliografía y Fuentes de Entrenamiento</a></li>
            </ul>
        </div>

        <div class="card manual-section" id="manual-1">
            <h2>📊 1. La Epidemia de Soledad y el Invierno Demográfico</h2>
            <p>La sociedad enfrenta una crisis silenciosa. Los datos recopilados por la OMS y el Pew Research Center demuestran un aislamiento clínico alarmante:</p>
            <div class="stats-grid">
                <div class="stat-box">
                    <div class="stat-number red">63%</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">De hombres jóvenes (18-30 años) se reportan completamente solos y sin pareja en USA.</div>
                </div>
                <div class="stat-box">
                    <div class="stat-number blue">34%</div>
                    <div style="font-size: 0.8rem; color: var(--text-secondary);">De mujeres en el mismo rango de edad se encuentran solteras.</div>
                </div>
            </div>
            <p style="margin-top: 15px;">Esta distorsión masiva de la oferta y la demanda, sumada a la hipergama de las redes sociales, empuja a los hombres al aislamiento, afectando drásticamente el matrimonio y provocando tasas de natalidad críticamente bajas a nivel global.</p>
        </div>

        <div class="card manual-section" id="manual-2">
            <h2>🧠 2. La Fórmula Universal del Text Game (Framework O.T.C.)</h2>
            <p>Natalia reevalúa la comunicación efectiva dividiéndola en tres etapas fundamentales:</p>
            <ul class="concept-list">
                <li>
                    <div class="concept-title">1. Opening (Apertura de Intriga/Descalificación)</div>
                    <p>No utilices saludos lógicos. Debes romper el patrón conversacional de descarte y captar la atención de inmediato con asunciones lúdicas o bromas de intriga.</p>
                </li>
                <li>
                    <div class="concept-title">2. Tension & Calibration (Tensión y Calibración)</div>
                    <p>Mide la inversión mediante el <strong>IIR (Índice de Inversión Relativa)</strong>. La longitud de tus mensajes debe ser un 20% menor que la de ella (IIR &lt; 1.0). Jamás caigas en el 'Modo Entrevista' ni te justifiques ante Shit Tests.</p>
                </li>
                <li>
                    <div class="concept-title">3. Closing (Cierre Logístico Asertivo)</div>
                    <p>Propón planes concretos basados en un liderazgo relajado. No pidas permiso ("¿te gustaría...?"), utiliza la asertividad tranquila: "Tomemos café el jueves a las 6. Pasa tu número".</p>
                </li>
            </ul>
        </div>

        <div class="card manual-section" id="manual-3">
            <h2>⚖️ 3. Algoritmo de Scoring y Calibración</h2>
            <p>Cada interacción analizada en este estudio se rige bajo la siguiente fórmula matemática de valor de estatus social:</p>
            <div class="formula-box">
                Score = (Reversión de Resistencia × 3) + (Eficiencia de Transición × 2) - (Inversión Excesiva)
            </div>
            <div class="grid-2">
                <div>
                    <h3 style="margin-top:0;">Criterios Aprobados</h3>
                    <ul>
                        <li>Respuestas humorísticas exagerando shit-tests.</li>
                        <li>Transiciones fluidas de plataforma hacia WhatsApp.</li>
                        <li>Establecimiento de límites claros (Frame Control).</li>
                    </ul>
                </div>
                <div>
                    <h3 style="margin-top:0;">Criterios Penalizados</h3>
                    <ul>
                        <li>Explicarse lógicamente ante desinterés o frialdad.</li>
                        <li>Doble texto ansioso buscando aprobación.</li>
                        <li>Inversión de caracteres desbalanceada.</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="card manual-section" id="manual-4">
            <h2>📜 4. Los 10 Mandamientos de Natalia & Consejos de Élite</h2>
            <div class="grid-2">
                <div>
                    <h3 style="color:#10b981; margin-top:0;">Los DO's (Prácticas Recomendadas)</h3>
                    <ul style="padding-left: 20px; line-height: 1.6;">
                        <li><strong>Asume Atracción:</strong> Actúa como si ya le gustaras.</li>
                        <li><strong>Statements > Preguntas:</strong> Usa opiniones en lugar de cuestionarios.</li>
                        <li><strong>Liderazgo Logístico:</strong> Propón día, hora y lugar de forma clara.</li>
                        <li><strong>Descalificación Lúdica:</strong> Moléstala amistosamente para equilibrar estatus.</li>
                    </ul>
                </div>
                <div>
                    <h3 style="color:#ef4444; margin-top:0;">Los DON'Ts (Prohibidos)</h3>
                    <ul style="padding-left: 20px; line-height: 1.6;">
                        <li><strong>Doble Texto Ansioso:</strong> Jamás persigas a quien no responde.</li>
                        <li><strong>Justificaciones Lógicas:</strong> No debatas emociones por texto.</li>
                        <li><strong>Disculpas sin motivo:</strong> No pidas perdón por existir o querer salir.</li>
                        <li><strong>Redes Excesivas:</strong> No pidas sus redes sociales secundarias, pide su WhatsApp.</li>
                    </ul>
                </div>
            </div>
        </div>

        <div class="card manual-section" id="manual-5">
            <h2>📚 5. Bibliografía y Fuentes de Entrenamiento</h2>
            <p>Este sistema unificado integra los conceptos y aprendizajes pragmáticos de los principales referentes empíricos:</p>
            <ul style="line-height: 1.7;">
                <li><strong>Playing With Fire:</strong> Tácticas de push/pull extremo y desconexión estratégica.</li>
                <li><strong>Todd V Dating:</strong> Teoría de valor y diseño estructurado de apertura.</li>
                <li><strong>Austen Summers:</strong> Cierres instantáneos e interacciones logísticas veloces.</li>
                <li><strong>Coach Kyle:</strong> Dinámicas naturales basadas en empatía y límites asertivos.</li>
            </ul>
        </div>
    </div>

    <!-- PESTAÑA MIS FAVORITOS -->
    <div id="tab-favoritos" class="tab-content">
        <div style="display:flex; gap:10px; margin-bottom:20px;">
            <button onclick="showFavSection('liked')" id="btn-fav-liked" style="flex:1; padding:10px; border-radius:10px; border:2px solid #10b981; background:rgba(16,185,129,0.15); color:#10b981; font-family:Outfit,sans-serif; font-weight:700; font-size:0.95rem; cursor:pointer;">👍 Me Gustó</button>
            <button onclick="showFavSection('disliked')" id="btn-fav-disliked" style="flex:1; padding:10px; border-radius:10px; border:2px solid #ef4444; background:rgba(239,68,68,0.1); color:#ef4444; font-family:Outfit,sans-serif; font-weight:700; font-size:0.95rem; cursor:pointer;">👎 No Me Gustó</button>
        </div>
        <div id="favs-liked-section">
            <h3 style="color:#10b981; font-family:Outfit; margin-bottom:12px;">👍 Conversaciones que me gustaron</h3>
            <div id="favs-liked-list"><p style="color:#94a3b8;">Aún no has marcado ninguna como favorita.</p></div>
        </div>
        <div id="favs-disliked-section" style="display:none;">
            <h3 style="color:#ef4444; font-family:Outfit; margin-bottom:12px;">👎 No me gustaron (para que Natalia aprenda qué evitar)</h3>
            <div id="favs-disliked-list"><p style="color:#94a3b8;">Aún no has marcado ninguna como no favorita.</p></div>
        </div>
    </div>

    <!-- Lightbox Modal -->
    <div id="lightboxModal" class="lightbox-modal" onclick="closeLightbox()">
        <span class="lightbox-close">&times;</span>
        <img class="lightbox-content" id="lightboxImg">
    </div>

    <script>
        function copyUrl() {
            const urlInput = document.getElementById('documentUrl');
            urlInput.select();
            urlInput.setSelectionRange(0, 99999); // Para móviles
            navigator.clipboard.writeText(urlInput.value).then(() => {
                alert("¡Enlace copiado con éxito al portapapeles!");
            }).catch(err => {
                alert("Error al copiar enlace automáticamente.");
            });
        }

        function openInBrowser() {
            window.open(document.getElementById('documentUrl').value, '_blank');
        }

        function openTab(evt, tabName) {
            var i, tabcontent, tablinks;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].style.display = "none";
                tabcontent[i].classList.remove("active");
            }
            tablinks = document.getElementsByClassName("tab-btn");
            for (i = 0; i < tablinks.length; i++) {
                tablinks[i].classList.remove("active");
            }
            document.getElementById(tabName).style.display = "block";
            document.getElementById(tabName).classList.add("active");
            if (evt) {
                evt.currentTarget.classList.add("active");
            }
            
            // Re-aplicar filtro de búsqueda al cambiar de pestaña
            filterCasesGlobal();
        }

        function filterCasesGlobal() {
            var input = document.getElementById("globalSearchBar");
            var filter = input.value.toUpperCase();
            var activeTab = document.querySelector(".tab-content.active");
            if (!activeTab) return;
            
            var cards = activeTab.getElementsByClassName("case-card");
            for (var i = 0; i < cards.length; i++) {
                var textContent = cards[i].textContent || cards[i].innerText;
                if (textContent.toUpperCase().indexOf(filter) > -1) {
                    cards[i].style.display = "";
                } else {
                    cards[i].style.display = "none";
                }
            }
        }

        // Sistema de Favoritos con localStorage
        const FAV_KEY = 'redditFavoritos';
        
        function loadFavs() {
            try { return JSON.parse(localStorage.getItem(FAV_KEY)) || {}; } catch(e) { return {}; }
        }
        
        function saveFavs(data) {
            localStorage.setItem(FAV_KEY, JSON.stringify(data));
        }
        
        function toggleFav(postId, type, btn) {
            var favs = loadFavs();
            if (favs[postId] === type) {
                // Deseleccionar si clickea el mismo
                delete favs[postId];
            } else {
                favs[postId] = type;
            }
            saveFavs(favs);
            updateFavButtons();
            renderFavLists();
        }
        
        function updateFavButtons() {
            var favs = loadFavs();
            document.querySelectorAll('[id^="fav-like-"]').forEach(function(btn) {
                var postId = btn.id.replace('fav-like-', '');
                btn.style.background = (favs[postId] === 'like') ? 'rgba(16,185,129,0.5)' : 'rgba(16,185,129,0.1)';
                btn.style.fontWeight = (favs[postId] === 'like') ? '800' : 'normal';
            });
            document.querySelectorAll('[id^="fav-dislike-"]').forEach(function(btn) {
                var postId = btn.id.replace('fav-dislike-', '');
                btn.style.background = (favs[postId] === 'dislike') ? 'rgba(239,68,68,0.5)' : 'rgba(239,68,68,0.1)';
                btn.style.fontWeight = (favs[postId] === 'dislike') ? '800' : 'normal';
            });
        }
        
        function renderFavLists() {
            var favs = loadFavs();
            var likedIds = Object.keys(favs).filter(function(k) { return favs[k] === 'like'; });
            var dislikedIds = Object.keys(favs).filter(function(k) { return favs[k] === 'dislike'; });
            
            // Renderizar favoritos
            var likedList = document.getElementById('favs-liked-list');
            if (likedIds.length === 0) {
                likedList.innerHTML = '<p style="color:#94a3b8;">Aún no has marcado ninguna como favorita.</p>';
            } else {
                likedList.innerHTML = '';
                likedIds.forEach(function(pid) {
                    var card = document.querySelector('[data-post-id="' + pid + '"]');
                    if (card) {
                        var clone = card.cloneNode(true);
                        clone.querySelectorAll('.fav-bar').forEach(function(el) { el.style.display = 'none'; });
                        likedList.appendChild(clone);
                    }
                });
            }
            
            // Renderizar no favoritos
            var dislikedList = document.getElementById('favs-disliked-list');
            if (dislikedIds.length === 0) {
                dislikedList.innerHTML = '<p style="color:#94a3b8;">Aún no has marcado ninguna como no favorita.</p>';
            } else {
                dislikedList.innerHTML = '';
                dislikedIds.forEach(function(pid) {
                    var card = document.querySelector('[data-post-id="' + pid + '"]');
                    if (card) {
                        var clone = card.cloneNode(true);
                        clone.querySelectorAll('.fav-bar').forEach(function(el) { el.style.display = 'none'; });
                        dislikedList.appendChild(clone);
                    }
                });
            }
        }
        
        function showFavSection(type) {
            document.getElementById('favs-liked-section').style.display = (type === 'liked') ? 'block' : 'none';
            document.getElementById('favs-disliked-section').style.display = (type === 'disliked') ? 'block' : 'none';
            document.getElementById('btn-fav-liked').style.borderWidth = (type === 'liked') ? '3px' : '2px';
            document.getElementById('btn-fav-disliked').style.borderWidth = (type === 'disliked') ? '3px' : '2px';
        }
        
        // Inicializar favoritos al cargar la página
        window.addEventListener('load', function() {
            updateFavButtons();
            renderFavLists();
        });

        // Funciones del Lightbox Modal
        function openLightbox(src) {
            document.getElementById('lightboxImg').src = src;
            document.getElementById('lightboxModal').style.display = 'flex';
        }

        function closeLightbox() {
            document.getElementById('lightboxModal').style.display = 'none';
        }
    </script>
</body>
</html>
"""

    with open("estudio_textgame_casos_reales.html", "w", encoding="utf-8") as f:
        f.write(html_content)    
    logging.info(f"📁 HTML Final Unificado Generado Exitosamente")

    print("\n--- ESTADISTICAS DE COMPRESION ---")
    total_orig = sum(s['original'] for s in compression_stats)
    total_comp = sum(s['compressed'] for s in compression_stats)
    for s in compression_stats:
        ratio = 100 - (s['compressed'] / s['original'] * 100) if s['original'] > 0 else 0
        print(f"{s['file']}: {s['original']/1024:.1f} KB -> {s['compressed']/1024:.1f} KB (Ahorro: {ratio:.1f}%)")
    
    if total_orig > 0:
        total_ratio = 100 - (total_comp / total_orig * 100)
        print(f"TOTAL: {total_orig/1024/1024:.2f} MB -> {total_comp/1024/1024:.2f} MB (Ahorro Global: {total_ratio:.1f}%)")
    print("----------------------------------\n")

if __name__ == "__main__":
    compile_html()
