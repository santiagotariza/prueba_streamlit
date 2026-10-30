import time
import pandas as pd
import streamlit as st
import fitz   # PyMuPDF
from google import genai

MODELO = "gemini-3.5-flash-lite"
MAX_ARCHIVOS = 5      # límite para no agotar el cupo gratuito
PAUSA = 4             # segundos entre llamadas (~15 pedidos por minuto)

def procesar(texto_pdf, api_key):
    # Esta función debe ser AUTOCONTENIDA: define adentro todo lo que usa.
    client = genai.Client(api_key=api_key)
    prompt = ("Resumí en español, con ortografía correcta, en como máximo 150 palabras, "
              "el siguiente paper. Incluí objetivo, método y resultado principal. "
              "Si algo no aparece, no lo inventes. Paper: " + texto_pdf)
    return client.models.generate_content(model=MODELO, contents=prompt).text


st.set_page_config(page_title="Asistente de papers", page_icon="📄")
st.title("📄 Asistente de papers")
st.write("Subí uno o varios PDFs y obtené el resultado en una tabla que podés descargar.")

# --- API key: de los secretos de Streamlit, o la ingresa quien usa la app ---
def obtener_api_key():
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return ""

api_key = obtener_api_key()
if not api_key:
    api_key = st.text_input("Tu API key de Gemini", type="password")

# accept_multiple_files=True permite subir varios PDFs: devuelve una LISTA de archivos
archivos = st.file_uploader("Subí tus PDFs", type="pdf", accept_multiple_files=True)

if archivos and len(archivos) > MAX_ARCHIVOS:
    st.warning(f"Se van a procesar solo los primeros {MAX_ARCHIVOS} archivos.")
    archivos = archivos[:MAX_ARCHIVOS]

if archivos and api_key and st.button("Procesar"):
    filas = []
    barra = st.progress(0.0)                      # barra de progreso
    for i, archivo in enumerate(archivos):
        try:
            doc = fitz.open(stream=archivo.read(), filetype="pdf")
            texto = " ".join(pagina.get_text() for pagina in doc)
            resultado = procesar(texto, api_key)
        except Exception as e:
            resultado = f"ERROR: {e}"
        filas.append({"archivo": archivo.name, "resultado": resultado})
        barra.progress((i + 1) / len(archivos))
        time.sleep(PAUSA)
    # session_state guarda la tabla para que NO desaparezca cuando la página se vuelve a ejecutar
    st.session_state["tabla"] = pd.DataFrame(filas)

if "tabla" in st.session_state:
    st.subheader("Resultados")
    st.dataframe(st.session_state["tabla"])
    st.download_button("Descargar CSV",
                       st.session_state["tabla"].to_csv(index=False).encode("utf-8"),
                       file_name="resultados.csv", mime="text/csv")
elif archivos and not api_key:
    st.info("Falta la API key.")
