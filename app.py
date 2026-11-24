
from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = "radio-exam-clave"


def conectar_db():
    conexion = sqlite3.connect("database.db")
    conexion.row_factory = sqlite3.Row
    return conexion


@app.route("/")
def inicio():
    return render_template("index.html")


@app.route("/examen")
def examen():
    conexion = conectar_db()

    preguntas = conexion.execute("""
        SELECT * FROM preguntas
        ORDER BY RANDOM()
        LIMIT 15
    """).fetchall()

    conexion.close()

    session["preguntas"] = [dict(p) for p in preguntas]

    return render_template("examen.html", preguntas=preguntas)


@app.route("/corregir", methods=["POST"])
def corregir():

    preguntas = session.get("preguntas", [])

    if not preguntas:
        return redirect(url_for("inicio"))

    correctas = 0

    for pregunta in preguntas:

        respuesta = request.form.get(str(pregunta["id"]))

        if respuesta == pregunta["correcta"]:
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


if __name__ == "__main__":
    app.run(debug=True)
