
from pypdf import PdfReader

PDF_PATH = "Banco_de_Preguntas_Tecnica_NOVICIO.pdf"

pdf = PdfReader(PDF_PATH)

print("PAGINAS:", len(pdf.pages))

texto = "\n".join(
    pagina.extract_text() or ""
    for pagina in pdf.pages
)

print("\n--- INICIO DEL TEXTO EXTRAIDO ---")
print(texto[:5000])

print("\n--- SECCION DE RESPUESTAS ---")

if "RESPUESTAS DEL EXAMEN" in texto:
    respuestas = texto.split("RESPUESTAS DEL EXAMEN", 1)[1]
    print(respuestas[:2000])
else:
    print("No se encontró el título exacto de la sección.")
