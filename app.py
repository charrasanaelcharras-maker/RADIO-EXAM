
import os
import sqlite3
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort
)
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import check_password_hash


app = Flask(__name__)

app.secret_key = os.environ.get("SECRET_KEY")

if not app.secret_key:
    raise RuntimeError("Falta configurar SECRET_KEY.")

csrf = CSRFProtect(app)


# =====================================
# BASE DE DATOS
# =====================================

DB_PATH = os.environ.get("RADIO_EXAM_DB", "database.db")


def conectar_db():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def obtener_opciones(conexion, pregunta_id):
    return conexion.execute("""
        SELECT id, texto, orden, es_correcta
        FROM opciones
        WHERE pregunta_id = ?
        ORDER BY orden
    """, (pregunta_id,)).fetchall()


def preparar_formulario(pregunta=None, opciones=None):

    if opciones is None:
        opciones = [
            {"texto": "", "es_correcta": False},
            {"texto": "", "es_correcta": False}
        ]

    return render_template(
        "pregunta_form.html",
        titulo="Editar pregunta" if pregunta else "Agregar pregunta",
        pregunta=pregunta,
        opciones=opciones
    )


def guardar_opciones(conexion, pregunta_id, textos, correcta_index):
    for indice, texto in enumerate(textos):
        conexion.execute("""
            INSERT INTO opciones (
                pregunta_id, texto, orden, es_correcta
            )
            VALUES (?, ?, ?, ?)
        """, (
            pregunta_id,
            texto,
            indice + 1,
            int(indice == correcta_index)
        ))


def obtener_datos_formulario():
    categoria = request.form.get("categoria", "").strip()
    texto = request.form.get("pregunta", "").strip()

    opciones = [
        opcion.strip()
        for opcion in request.form.getlist("opciones[]")
    ]

    correcta = request.form.get("correcta", "").strip()

    if not categoria or not texto:
        return None, "Completá la categoría y el enunciado."

    if len(opciones) < 2:
        return None, "La pregunta debe tener al menos dos opciones."

    if any(not opcion for opcion in opciones):
        return None, "No puede haber opciones vacías."

    try:
        correcta_index = int(correcta)
    except (ValueError, TypeError):
        return None, "Seleccioná una respuesta correcta."

    if correcta_index < 0 or correcta_index >= len(opciones):
        return None, "La respuesta correcta seleccionada no es válida."

    return {
        "categoria": categoria,
        "pregunta": texto,
        "opciones": opciones,
        "correcta_index": correcta_index
    }, None


def preparar_opciones_formulario(textos, correcta_index):
    return [
        {
            "texto": texto,
            "es_correcta": indice == correcta_index
        }
        for indice, texto in enumerate(textos)
    ]


def guardar_columnas_compatibilidad(conexion, pregunta_id, datos):
    textos = datos["opciones"]

    opcion_a = textos[0]
    opcion_b = textos[1]
    opcion_c = textos[2] if len(textos) > 2 else ""
    opcion_d = textos[3] if len(textos) > 3 else ""

    letras = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    indice = datos["correcta_index"]
    correcta_antigua = letras[indice] if indice < len(letras) else "A"

    conexion.execute("""
        UPDATE preguntas
        SET opcion_a = ?,
            opcion_b = ?,
            opcion_c = ?,
            opcion_d = ?,
            correcta = ?
        WHERE id = ?
    """, (
        opcion_a,
        opcion_b,
        opcion_c,
        opcion_d,
        correcta_antigua,
        pregunta_id
    ))


# =====================================
# PROTECCIÓN DE ADMINISTRACIÓN
# =====================================

def requiere_admin(funcion):
    @wraps(funcion)
    def decorada(*args, **kwargs):
        if not session.get("admin_id"):
            return redirect(url_for("admin_login"))
        return funcion(*args, **kwargs)
    return decorada


# =====================================
# INICIO
# =====================================

@app.route("/")
def inicio():
    return render_template("index.html")


# =====================================
# EXAMEN
# =====================================

@app.route("/examen")
def examen():
    conexion = conectar_db()

    preguntas_db = conexion.execute("""
        SELECT *
        FROM preguntas
        ORDER BY RANDOM()
        LIMIT 15
    """).fetchall()

    preguntas = []
    respuestas_correctas = []

    for pregunta_db in preguntas_db:
        opciones_db = obtener_opciones(
            conexion, pregunta_db["id"]
        )

        if len(opciones_db) < 2:
            continue

        opciones = [dict(opcion) for opcion in opciones_db]

        pregunta = dict(pregunta_db)
        pregunta["opciones"] = opciones

        preguntas.append(pregunta)

        correcta = next(
            (o["id"] for o in opciones if o["es_correcta"]),
            None
        )

        respuestas_correctas.append({
            "id": pregunta["id"],
            "correcta": correcta
        })

    conexion.close()

    if not preguntas:
        return "No hay preguntas con opciones disponibles.", 500

    session["preguntas"] = respuestas_correctas

    return render_template(
        "examen.html",
        preguntas=preguntas
    )


# =====================================
# CORREGIR EXAMEN
# =====================================

@app.route("/corregir", methods=["POST"])
def corregir():
    preguntas = session.get("preguntas", [])

    if not preguntas:
        return redirect(url_for("inicio"))

    correctas = 0

    for pregunta in preguntas:
        respuesta = request.form.get(str(pregunta["id"]))

        if respuesta == str(pregunta["correcta"]):
            correctas += 1

    total = len(preguntas)
    incorrectas = total - correctas
    porcentaje = round((correctas / total) * 100)
    aprobado = correctas >= 11

    session.pop("preguntas", None)

    return render_template(
        "resultado.html",
        correctas=correctas,
        incorrectas=incorrectas,
        total=total,
        porcentaje=porcentaje,
        aprobado=aprobado
    )


# =====================================
# LOGIN ADMIN
# =====================================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if session.get("admin_id"):
        return redirect(url_for("admin_inicio"))

    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        contrasena = request.form.get("contrasena", "")

        conexion = conectar_db()

        administrador = conexion.execute("""
            SELECT *
            FROM administradores
            WHERE usuario = ?
        """, (usuario,)).fetchone()

        conexion.close()

        if administrador and check_password_hash(
            administrador["password_hash"], contrasena
        ):
            session.clear()
            session["admin_id"] = administrador["id"]
            session["admin_usuario"] = administrador["usuario"]

            return redirect(url_for("admin_inicio"))

        flash("Usuario o contraseña incorrectos.")

    return render_template("login.html")


# =====================================
# PANEL ADMIN
# =====================================

@app.route("/admin")
@requiere_admin
def admin_inicio():
    conexion = conectar_db()

    total_preguntas = conexion.execute(
        "SELECT COUNT(*) FROM preguntas"
    ).fetchone()[0]

    categorias = conexion.execute("""
        SELECT categoria, COUNT(*) AS cantidad
        FROM preguntas
        GROUP BY categoria
        ORDER BY categoria
    """).fetchall()

    conexion.close()

    return render_template(
        "admin.html",
        total_preguntas=total_preguntas,
        categorias=categorias
    )


@app.route("/admin/logout", methods=["POST"])
@requiere_admin
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))


# =====================================
# LISTAR PREGUNTAS
# =====================================

@app.route("/admin/preguntas")
@requiere_admin
def listar_preguntas():
    conexion = conectar_db()

    preguntas_db = conexion.execute("""
        SELECT *
        FROM preguntas
        ORDER BY categoria, id
    """).fetchall()

    preguntas = []

    for pregunta_db in preguntas_db:
        pregunta = dict(pregunta_db)
        pregunta["opciones"] = [
            dict(o) for o in obtener_opciones(
                conexion, pregunta["id"]
            )
        ]
        preguntas.append(pregunta)

    conexion.close()

    return render_template(
        "preguntas_admin.html",
        preguntas=preguntas
    )


# =====================================
# AGREGAR PREGUNTA
# =====================================

@app.route("/admin/preguntas/nueva", methods=["GET", "POST"])
@requiere_admin
def nueva_pregunta():

    if request.method == "POST":
        datos, error = obtener_datos_formulario()

        if error:
            flash(error)

            textos = request.form.getlist("opciones[]")
            correcta = request.form.get("correcta", "-1")

            try:
                indice = int(correcta)
            except ValueError:
                indice = -1

            pregunta_temporal = {
                "categoria": request.form.get("categoria", ""),
                "pregunta": request.form.get("pregunta", "")
            }

            return preparar_formulario(
                pregunta_temporal,
                preparar_opciones_formulario(textos, indice)
            )

        conexion = conectar_db()

        try:
            cursor = conexion.execute("""
                INSERT INTO preguntas (
                    categoria, pregunta,
                    opcion_a, opcion_b, opcion_c,
                    opcion_d, correcta
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                datos["categoria"],
                datos["pregunta"],
                datos["opciones"][0],
                datos["opciones"][1],
                datos["opciones"][2] if len(datos["opciones"]) > 2 else "",
                datos["opciones"][3] if len(datos["opciones"]) > 3 else "",
                "A"
            ))

            pregunta_id = cursor.lastrowid

            guardar_opciones(
                conexion,
                pregunta_id,
                datos["opciones"],
                datos["correcta_index"]
            )

            guardar_columnas_compatibilidad(
                conexion, pregunta_id, datos
            )

            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

        finally:
            conexion.close()

        flash("Pregunta agregada correctamente.")
        return redirect(url_for("listar_preguntas"))

    return preparar_formulario()


# =====================================
# EDITAR PREGUNTA
# =====================================

@app.route("/admin/preguntas/<int:id>/editar", methods=["GET", "POST"])
@requiere_admin
def editar_pregunta(id):
    conexion = conectar_db()

    pregunta_db = conexion.execute("""
        SELECT *
        FROM preguntas
        WHERE id = ?
    """, (id,)).fetchone()

    if not pregunta_db:
        conexion.close()
        abort(404)

    if request.method == "POST":
        datos, error = obtener_datos_formulario()

        if error:
            flash(error)

            textos = request.form.getlist("opciones[]")
            correcta = request.form.get("correcta", "-1")

            try:
                indice = int(correcta)
            except ValueError:
                indice = -1

            pregunta_temporal = {
                "id": id,
                "categoria": request.form.get("categoria", ""),
                "pregunta": request.form.get("pregunta", "")
            }

            conexion.close()

            return preparar_formulario(
                pregunta_temporal,
                preparar_opciones_formulario(textos, indice)
            )

        try:
            conexion.execute("""
                UPDATE preguntas
                SET categoria = ?, pregunta = ?
                WHERE id = ?
            """, (
                datos["categoria"],
                datos["pregunta"],
                id
            ))

            conexion.execute("""
                DELETE FROM opciones
                WHERE pregunta_id = ?
            """, (id,))

            guardar_opciones(
                conexion,
                id,
                datos["opciones"],
                datos["correcta_index"]
            )

            guardar_columnas_compatibilidad(
                conexion, id, datos
            )

            conexion.commit()

        except Exception:
            conexion.rollback()
            raise

        finally:
            conexion.close()

        flash("Pregunta actualizada correctamente.")
        return redirect(url_for("listar_preguntas"))

    pregunta = dict(pregunta_db)

    opciones = [
        dict(o) for o in obtener_opciones(conexion, id)
    ]

    conexion.close()

    return preparar_formulario(pregunta, opciones)


# =====================================
# ELIMINAR PREGUNTA
# =====================================

@app.route("/admin/preguntas/<int:id>/eliminar", methods=["POST"])
@requiere_admin
def eliminar_pregunta(id):
    conexion = conectar_db()

    try:
        conexion.execute("""
            DELETE FROM opciones
            WHERE pregunta_id = ?
        """, (id,))

        conexion.execute("""
            DELETE FROM preguntas
            WHERE id = ?
        """, (id,))

        conexion.commit()

    except Exception:
        conexion.rollback()
        raise

    finally:
        conexion.close()

    flash("Pregunta eliminada correctamente.")
    return redirect(url_for("listar_preguntas"))


# =====================================
# INICIAR APLICACIÓN
# =====================================

if __name__ == "__main__":
    app.run(debug=False)
