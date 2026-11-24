
import sqlite3
import re
from pypdf import PdfReader

# 1. Leer el PDF
pdf = PdfReader("Banco_de_Preguntas_Tecnica_NOVICIO.pdf")

texto = ""

for pagina in pdf.pages:
    texto += (pagina.extract_text() or "") + "\n"

# 2. Separar preguntas y respuestas
if "RESPUESTAS DEL EXAMEN" not in texto:
    print("Error: no se encontró la sección de respuestas.")
    exit()

parte_preguntas, parte_respuestas = texto.split(
    "RESPUESTAS DEL EXAMEN", 1
)

# 3. Leer las respuestas correctas
respuestas = {}

for numero, letra in re.findall(
    r"(\d{1,3})\s*-\s*([A-D])",
    parte_respuestas,
    re.IGNORECASE
):
    respuestas[int(numero)] = letra.lower()

# 4. Separar las preguntas
bloques = re.split(
    r"(?m)^\s*(\d{1,3})\.\s+",
    parte_preguntas
)

preguntas = []

# 5. Procesar cada pregunta
for i in range(1, len(bloques), 2):

    numero = int(bloques[i])
    contenido = bloques[i + 1]

    opciones = {}

    encontradas = re.findall(
        r"(?m)^\s*([a-eA-E])\)\s*(.*)",
        contenido
    )

    for letra, texto_opcion in encontradas:
        opciones[letra.lower()] = texto_opcion.strip()

    # Corregir el error de tipeo de la pregunta 48
    if numero == 48 and "e" in opciones and "d" not in opciones:
        opciones["d"] = opciones.pop("e")

    pregunta = re.split(
        r"(?m)^\s*a\)",
        contenido
    )[0].strip()

    if (
        len(opciones) != 4
        or not all(letra in opciones for letra in ["a", "b", "c", "d"])
        or numero not in respuestas
    ):
        print("Revisar pregunta:", numero)
        continue

    preguntas.append((
        "Técnica y Electrónica",
        pregunta,
        opciones["a"],
        opciones["b"],
        opciones["c"],
        opciones["d"],
        respuestas[numero]
    ))

# 6. Verificar las 150 preguntas
if len(preguntas) != 150:
    print("Error: no se encontraron las 150 preguntas.")
    print("Preguntas encontradas:", len(preguntas))
    print("No se modificó la base de datos.")
    exit()

# 7. Conectar con SQLite
conexion = sqlite3.connect("database.db")

conexion.execute("""
CREATE TABLE IF NOT EXISTS preguntas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    opcion_a TEXT NOT NULL,
    opcion_b TEXT NOT NULL,
    opcion_c TEXT NOT NULL,
    opcion_d TEXT NOT NULL,
    correcta TEXT NOT NULL
)
""")

# 8. Comprobar que exista la columna opcion_d
columnas = [
    fila[1]
    for fila in conexion.execute("PRAGMA table_info(preguntas)")
]

if "opcion_d" not in columnas:
    conexion.execute(
        "ALTER TABLE preguntas ADD COLUMN opcion_d TEXT"
    )

# 9. Eliminar las preguntas anteriores de este banco
conexion.execute("DELETE FROM preguntas")

# 10. Insertar las 150 preguntas
conexion.executemany("""
INSERT INTO preguntas
(categoria, pregunta, opcion_a, opcion_b, opcion_c, opcion_d, correcta)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", preguntas)

conexion.commit()

# 11. Comprobar la cantidad guardada
cantidad = conexion.execute(
    "SELECT COUNT(*) FROM preguntas"
).fetchone()[0]

conexion.close()

print("¡Carga completada correctamente!")
print("Categoría: Técnica y Electrónica")
print("Preguntas cargadas:", cantidad)
