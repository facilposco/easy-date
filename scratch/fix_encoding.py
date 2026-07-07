import sys
import codecs
sys.stdout.reconfigure(encoding='utf-8')

HTML_PATH = "estudio_textgame_casos_reales.html"

with open(HTML_PATH, "rb") as f:
    raw_bytes = f.read()

# It seems the file might have been written as cp1252 but containing utf-8 bytes
# Let's decode as utf-8, replace any weird characters, and save
try:
    content = raw_bytes.decode('utf-8')
    print("El archivo ya es UTF-8 válido.")
    # Pero puede contener "Ã³" que es la representación ANSI de "ó"
    replacements = {
        'Ã¡': 'á',
        'Ã©': 'é',
        'Ã³': 'ó',
        'Ãº': 'ú',
        'Ã±': 'ñ',
        'Ã­': 'í', # í
        'Â¿': '¿',
        'Â¡': '¡',
        'Ã ': 'Á',
        'Ã‰': 'É',
        'Ã“': 'Ó',
        'Ãš': 'Ú',
        'Ã‘': 'Ñ'
    }
    
    modified = False
    for bad, good in replacements.items():
        if bad in content:
            content = content.replace(bad, good)
            modified = True
            
    if modified:
        with open(HTML_PATH, "w", encoding="utf-8") as f:
            f.write(content)
        print("Se encontraron caracteres corruptos y fueron reemplazados por UTF-8 correcto.")
    else:
        print("No se encontraron caracteres corruptos en el HTML.")

except Exception as e:
    print(f"Error decodificando: {e}")
