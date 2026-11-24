
import sqlite3

conexion = sqlite3.connect("database.db")
conexion.execute("PRAGMA foreign_keys = ON")

try:
    conexion.execute("""
        CREATE TABLE IF NOT EXISTS opciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pregunta_id INTEGER NOT NULL,
            texto TEXT NOT NULL,
            orden INTEGER NOT NULL,
            es_correcta INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (pregunta_id)
                REFERENCES preguntas(id)
                ON DELETE CASCADE
        )
    """)

    preguntas = conexion.execute("""
        SELECT id, opcion_a, opcion_b, opcion_c, opcion_d, correcta
        FROM preguntas
    """).fetchall()

    migradas = 0

    for pregunta in preguntas:

        pregunta_id = pregunta[0]

        existentes = conexion.execute("""
            SELECT COUNT(*)
            FROM opciones
            WHERE pregunta_id = ?
        """, (pregunta_id,)).fetchone()[0]

        if existentes > 0:
            continue

        correcta = str(pregunta[5]).strip().upper()

        respuestas = [
            ("A", pregunta[1]),
            ("B", pregunta[2]),
            ("C", pregunta[3]),
            ("D", pregunta[4])
        ]

        for orden, (letra, texto) in enumerate(respuestas, start=1):

            if texto is None or not str(texto).strip():
                continue

            conexion.execute("""
                INSERT INTO opciones (
                    pregunta_id, texto, orden, es_correcta
                )
                VALUES (?, ?, ?, ?)
            """, (
                pregunta_id,
                str(texto).strip(),
                orden,
                int(letra == correcta)
            ))

        migradas += 1

    conexion.commit()

    total = conexion.execute(
        "SELECT COUNT(*) FROM opciones"
    ).fetchone()[0]

    print("Migración completada correctamente.")
    print("Preguntas procesadas:", migradas)
    print("Opciones registradas:", total)

except Exception:
    conexion.rollback()
    raise

finally:
    conexion.close()
