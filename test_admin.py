
from playwright.sync_api import sync_playwright
from getpass import getpass

URL = "http://127.0.0.1:5000"

print("\nPRUEBAS DE ADMINISTRACIÓN - RADIO EXAM\n")

usuario = input("Usuario administrador: ")
contrasena = getpass("Contraseña: ")

texto_original = "PREGUNTA TEMPORAL PLAYWRIGHT"
texto_editado = "PREGUNTA EDITADA PLAYWRIGHT"


def probar_proteccion(page):
    page.goto(URL + "/admin")

    assert page.url.endswith("/admin/login"), (
        "ERROR: Se pudo entrar al panel sin iniciar sesión"
    )

    print("OK: Panel protegido")


def iniciar_sesion(page):
    page.goto(URL + "/admin/login")

    page.locator("#usuario").fill(usuario)
    page.locator("#contrasena").fill(contrasena)

    page.get_by_role("button", name="INGRESAR").click()

    assert page.get_by_role(
        "heading", name="Panel principal"
    ).count() == 1

    print("OK: Inicio de sesión")


def probar_panel(page):
    assert page.locator(".admin-stat-number").count() == 1
    assert page.get_by_text(
        "Gestionar preguntas"
    ).count() == 1

    print("OK: Panel principal")


def probar_creacion(page):
    page.get_by_role(
        "link", name="+ Agregar pregunta"
    ).click()

    page.locator("#categoria").fill("Prueba automatizada")
    page.locator("#pregunta").fill(texto_original)

    page.get_by_role(
        "button", name="+ Agregar opción"
    ).click()

    opciones = page.locator('input[name="opciones[]"]')

    assert opciones.count() == 3

    opciones.nth(0).fill("Respuesta incorrecta uno")
    opciones.nth(1).fill("Respuesta correcta")
    opciones.nth(2).fill("Respuesta incorrecta dos")

    page.locator('input[name="correcta"]').nth(1).check()

    page.get_by_role(
        "button", name="Guardar pregunta"
    ).click()

    assert page.get_by_text(texto_original).count() == 1

    print("OK: Creación de pregunta con 3 opciones")


def probar_edicion(page):
    tarjeta = page.locator(
        ".question-admin-card"
    ).filter(has_text=texto_original)

    assert tarjeta.count() == 1

    tarjeta.get_by_role("link", name="Editar").click()

    page.locator("#pregunta").fill(texto_editado)

    page.get_by_role(
        "button", name="Guardar pregunta"
    ).click()

    assert page.get_by_text(texto_editado).count() == 1
    assert page.get_by_text(texto_original).count() == 0

    print("OK: Edición de pregunta")


def probar_eliminacion(page):
    tarjeta = page.locator(
        ".question-admin-card"
    ).filter(has_text=texto_editado)

    assert tarjeta.count() == 1

    page.once("dialog", lambda dialog: dialog.accept())

    tarjeta.get_by_role(
        "button", name="Eliminar"
    ).click()

    assert page.get_by_text(texto_editado).count() == 0

    print("OK: Eliminación de pregunta")


def probar_cierre_sesion(page):
    page.goto(URL + "/admin")

    page.get_by_role(
        "button", name="Cerrar sesión"
    ).click()

    assert page.url.endswith("/admin/login")

    page.goto(URL + "/admin")

    assert page.url.endswith("/admin/login")

    print("OK: Cierre de sesión y protección posterior")


with sync_playwright() as p:
    navegador = p.chromium.launch(headless=True)
    contexto = navegador.new_context()
    pagina = contexto.new_page()

    try:
        probar_proteccion(pagina)
        iniciar_sesion(pagina)
        probar_panel(pagina)
        probar_creacion(pagina)
        probar_edicion(pagina)
        probar_eliminacion(pagina)
        probar_cierre_sesion(pagina)

        print("\nTODAS LAS PRUEBAS DE ADMINISTRACIÓN FINALIZARON CORRECTAMENTE")

    except Exception as error:
        print("\nERROR EN LAS PRUEBAS:")
        print(error)
        raise

    finally:
        navegador.close()
