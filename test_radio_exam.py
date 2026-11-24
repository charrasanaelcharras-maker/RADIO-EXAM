
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:5000"


def probar_inicio(page):
    page.goto(URL)

    assert page.get_by_role("heading", name="RADIO EXAM").count() >= 1
    assert page.get_by_text("Técnica y Electrónica").count() >= 1

    print("OK: Página principal")


def probar_examen(page):
    page.goto(URL)

    page.get_by_role("button", name="Comenzar examen").click()

    preguntas = page.locator(".question-card")
    assert preguntas.count() == 15

    for pregunta in preguntas.all():
        assert pregunta.locator('input[type="radio"]').count() == 4

    print("OK: 15 preguntas y 4 opciones")


def probar_progreso(page):
    page.goto(URL + "/examen")

    primera = page.locator(".question-card").first
    primera.locator('input[type="radio"]').first.check()

    assert page.locator("#progress-text").inner_text() == "1 de 15"

    assert page.locator("#progress-fill").evaluate(
        "(element) => element.style.width"
    ) != "0%"

    print("OK: Barra de progreso")


def probar_validacion(page):
    page.goto(URL + "/examen")

    valido = page.locator("#exam-form").evaluate(
        "(form) => form.checkValidity()"
    )

    assert valido is False

    print("OK: Validación de respuestas")


def probar_resultado(page):
    page.goto(URL + "/examen")

    preguntas = page.locator(".question-card")

    for pregunta in preguntas.all():
        pregunta.locator('input[type="radio"]').first.check()

    page.get_by_role("button", name="Finalizar examen").click()

    assert page.locator(".puntaje").count() == 1

    correctas = int(
        page.locator(".estadistica h3.aprobado").inner_text()
    )

    incorrectas = int(
        page.locator(".estadistica h3.desaprobado").inner_text()
    )

    assert correctas + incorrectas == 15

    print("OK: Resultado del examen")


with sync_playwright() as p:
    navegador = p.chromium.launch(headless=True)
    pagina = navegador.new_page()

    print("\nINICIANDO PRUEBAS DE RADIO EXAM\n")

    probar_inicio(pagina)
    probar_examen(pagina)
    probar_progreso(pagina)
    probar_validacion(pagina)
    probar_resultado(pagina)

    navegador.close()

    print("\nTODAS LAS PRUEBAS FINALIZARON CORRECTAMENTE")
