
import sqlite3

def crear_base_datos(db_path="database.db"):
    conexion = sqlite3.connect(db_path)
    conexion.execute("PRAGMA foreign_keys = ON")

    try:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS preguntas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                pregunta TEXT NOT NULL,
                opcion_a TEXT NOT NULL,
                opcion_b TEXT NOT NULL,
                opcion_c TEXT NOT NULL,
                correcta TEXT NOT NULL,
                opcion_d TEXT
            )
        """)

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

        conexion.execute("""
            CREATE TABLE IF NOT EXISTS administradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        conexion.commit()
        print("Base de datos creada correctamente.")

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()


if __name__ == "__main__":
    crear_base_datos()
