
import sqlite3

# Conectar con la base de datos
conexion = sqlite3.connect("database.db")

# Crear la tabla de preguntas
conexion.execute("""
CREATE TABLE IF NOT EXISTS preguntas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL,
    pregunta TEXT NOT NULL,
    opcion_a TEXT NOT NULL,
    opcion_b TEXT NOT NULL,
    opcion_c TEXT NOT NULL,
    correcta TEXT NOT NULL
)
""")

# Guardar los cambios
conexion.commit()

# Cerrar la conexión
conexion.close()

print("Base de datos creada correctamente")
