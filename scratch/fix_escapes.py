import re

file_path = "build_simulator.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Buscar y reemplazar cualquier escape de dollar en strings
# Queremos cambiar \${{ por ${{
# Y también \${ por ${ (en caso de que no hayan usado llaves dobles)
new_content = content.replace("\\${{", "${{").replace("\\${", "${")

# También busquemos si hay alguna barra inclinada en los template literals
# Por ejemplo: \${
# Vamos a usar una expresión regular para estar seguros de quitar la barra antes de $
cleaned_content = re.sub(r'\\\$', '$', content)

# Pero espera! En Python, si la cadena es un f-string, las llaves dobles {{ y }} se compilan a { y }.
# Si cambiamos \\${{ a ${{\n# Se compilará a ${ en el HTML final, que es la sintaxis correcta de Javascript!
# Vamos a verificar todos los reemplazos de de-escala de barras antes de $
# Busquemos cuántas ocurrencias de \$ hay en el archivo:
occurrences = len(re.findall(r'\\\$', content))
print(f"Ocurrencias de \\$ encontradas: {occurrences}")

# Reemplazar y guardar
with open(file_path, "w", encoding="utf-8") as f:
    f.write(cleaned_content)
    
print("¡Archivo build_simulator.py corregido y guardado!")
