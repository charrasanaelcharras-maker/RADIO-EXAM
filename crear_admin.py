
import os
import sqlite3
from getpass import getpass
from werkzeug.security import generate_password_hash


DB_PATH = os.environ.get("RADIO_EXAM_DB", "database.db")


def crear_admin():
    usuario = input("Nombre de usuario administrador: ").strip()

    if not usuario:
        print("El usuario no puede estar vacío.")
        return

    contrasena = getpass("Contraseña (mínimo 12 caracteres): ")
    confirmacion = getpass("Repetí la contraseña: ")

    if len(contrasena) < 12:
        print("La contraseña debe tener al menos 12 caracteres.")
        return

    if contrasena != confirmacion:
        print("Las contraseñas no coinciden.")
        return

    conexion = sqlite3.connect(DB_PATH)

    try:
        conexion.execute("""
            CREATE TABLE IF NOT EXISTS administradores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        """)

        existente = conexion.execute(
            "SELECT id FROM administradores WHERE usuario = ?",
            (usuario,)
        ).fetchone()

        if existente:
            print("Ese usuario ya existe.")
            return

        password_hash = generate_password_hash(contrasena)

        conexion.execute("""
            INSERT INTO administradores (usuario, password_hash)
            VALUES (?, ?)
        """, (usuario, password_hash))

        conexion.commit()
        print("\nAdministrador creado correctamente.")

    finally:
        conexion.close()


if __name__ == "__main__":
    crear_admin()
