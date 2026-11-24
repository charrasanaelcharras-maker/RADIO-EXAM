
import os
import re
import sqlite3
from pypdf import PdfReader
from crear_db import crear_base_datos

PDF_PATH = "Banco_de_Preguntas_Tecnica_NOVICIO.pdf"
DB_PATH = os.environ.get("RADIO_EXAM_DB", "database.db")


def limpiar(texto):
    return re.sub(r"\s+", " ", texto).strip()


def extraer_preguntas(texto):
    preguntas = {}
    actual = None
    opcion_actual = None

    for linea in texto.splitlines():
        linea = linea.strip()

        if not linea:
            continue

        # Detectar el comienzo de una pregunta: 1. texto
        coincidencia = re.match(r"^(\d{1,3})\s*[.)]\s*(.*)$", linea)

        if coincidencia:
            numero = int(coincidencia.group(1))

            if 1 <= numero <= 150:
                actual = {
                    "numero": numero,
                    "pregunta": coincidencia.group(2),
                    "opciones": {}
                }

                preguntas[numero] = actual
                opcion_actual = None
                continue

        if actual is None:
            continue

        # Detectar opciones: a), b), c), d)
        coincidencia = re.match(
            r"^([a-eA-E])\s*\)\s*(.*)$",
            linea
        )

        if coincidencia:
            letra = coincidencia.group(1).lower()
            contenido = coincidencia.group(2)

            # En la pregunta 48, el PDF identifica D como E.
            if actual["numero"] == 48 and letra == "e":
                letra = "d"

            if letra in ["a", "b", "c", "d"]:
                actual["opciones"][letra] = contenido
                opcion_actual = letra
                continue

        # Continuación de una pregunta o de una opción
        if opcion_actual:
            actual["opciones"][opcion_actual] += " " + linea
        else:
            actual["pregunta"] += " " + linea

    return preguntas


def cargar_preguntas():
    if not os.path.exists(PDF_PATH):
        print(f"ERROR: No se encontró {PDF_PATH}")
        return

    print("Leyendo el PDF...")

    pdf = PdfReader(PDF_PATH)

    texto = "\n".join(
        pagina.extract_text() or ""
        for pagina in pdf.pages
    )

    if "RESPUESTAS DEL EXAMEN" not in texto:
        print("ERROR: No se encontró la sección de respuestas.")
        return

    texto_preguntas, texto_respuestas = texto.split(
        "RESPUESTAS DEL EXAMEN", 1
    )

    preguntas = extraer_preguntas(texto_preguntas)

    # Extraer las respuestas del formato 1-C, 26-B, etc.
    respuestas = {}

    for numero, letra in re.findall(
        r"(\d{1,3})\s*-\s*([A-D])\b",
        texto_respuestas,
        re.IGNORECASE
    ):
        numero = int(numero)

        if 1 <= numero <= 150:
            respuestas[numero] = letra.upper()

    # Verificar que estén las 150 preguntas
    if len(preguntas) != 150:
        print(
            f"ERROR: Se encontraron {len(preguntas)} preguntas "
            "en lugar de 150."
        )
        print("No se modificó ninguna base de datos.")
        return

    # Verificar que estén todas las respuestas
    if len(respuestas) != 150:
        print(
            f"ERROR: Se encontraron {len(respuestas)} respuestas "
            "en lugar de 150."
        )
        print("No se modificó ninguna base de datos.")
        return

    # Preparar los datos y validar las cuatro opciones
    datos = []

    for numero in range(1, 151):
        if numero not in preguntas or numero not in respuestas:
            print(f"ERROR: Falta la pregunta o respuesta {numero}.")
            return

        item = preguntas[numero]
        opciones = item["opciones"]

        if not all(letra in opciones for letra in ["a", "b", "c", "d"]):
            print(f"ERROR: Faltan opciones en la pregunta {numero}.")
            print(f"Opciones encontradas: {list(opciones.keys())}")
            return

        pregunta = limpiar(item["pregunta"])
        opciones_limpias = [
            limpiar(opciones[letra])
            for letra in ["a", "b", "c", "d"]
        ]

        if not pregunta or not all(opciones_limpias):
            print(f"ERROR: Hay contenido vacío en la pregunta {numero}.")
            return

        datos.append({
            "categoria": "Técnica y Electrónica",
            "pregunta": pregunta,
            "opciones": opciones_limpias,
            "correcta": respuestas[numero]
        })

    # Crear las tablas en la base seleccionada
    crear_base_datos(DB_PATH)

    conexion = sqlite3.connect(DB_PATH)
    conexion.execute("PRAGMA foreign_keys = ON")

    try:
        existentes = conexion.execute(
            "SELECT COUNT(*) FROM preguntas"
        ).fetchone()[0]

        if existentes > 0:
            print("ERROR: La base de datos ya contiene preguntas.")
            print("No se modificó ningún dato.")
            print("Usá una base de datos nueva.")
            return

        for item in datos:
            cursor = conexion.execute("""
                INSERT INTO preguntas (
                    categoria,
                    pregunta,
                    opcion_a,
                    opcion_b,
                    opcion_c,
                    correcta,
                    opcion_d
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                item["categoria"],
                item["pregunta"],
                item["opciones"][0],
                item["opciones"][1],
                item["opciones"][2],
                item["correcta"],
                item["opciones"][3]
            ))

            pregunta_id = cursor.lastrowid

            for indice, opcion in enumerate(item["opciones"]):
                letra = chr(65 + indice)

                conexion.execute("""
                    INSERT INTO opciones (
                        pregunta_id,
                        texto,
                        orden,
                        es_correcta
                    )
                    VALUES (?, ?, ?, ?)
                """, (
                    pregunta_id,
                    opcion,
                    indice + 1,
                    1 if letra == item["correcta"] else 0
                ))

        conexion.commit()

        total_preguntas = conexion.execute(
            "SELECT COUNT(*) FROM preguntas"
        ).fetchone()[0]

        total_opciones = conexion.execute(
            "SELECT COUNT(*) FROM opciones"
        ).fetchone()[0]

        print("\n¡Carga completada correctamente!")
        print(f"Preguntas cargadas: {total_preguntas}")
        print(f"Opciones cargadas: {total_opciones}")
        print(f"Base utilizada: {DB_PATH}")

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


if __name__ == "__main__":
    cargar_preguntas()
