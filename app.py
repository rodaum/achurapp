"""App de Streamlit: ruteo por parámetros de URL y pantallas."""

import re
import secrets
import string
import unicodedata
from urllib.parse import urlencode

import streamlit as st

import config
import db

st.set_page_config(page_title="Asado", page_icon="🔥")


def generar_slug(nombre):
    """'Cumpleaños de Juan' -> 'cumpleanos-de-juan-x7k2'."""
    texto = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    base = re.sub(r"[^a-z0-9]+", "-", texto).strip("-")[:40] or "asado"
    sufijo = "".join(secrets.choice(string.ascii_lowercase + string.digits) for _ in range(4))
    return f"{base}-{sufijo}"


def armar_link(**params):
    """Link absoluto si Streamlit conoce su URL; si no, solo los parámetros."""
    base = getattr(st.context, "url", "") or ""
    return base.split("?")[0] + "?" + urlencode(params)


def pantalla_crear():
    st.title("🔥 Organizá tu asado")
    with st.form("crear"):
        nombre = st.text_input("Nombre del asado", placeholder="Cumple de Juan")
        fecha = st.date_input("Fecha (opcional)", value=None, format="DD/MM/YYYY")
        creado = st.form_submit_button("Crear asado")

    if not creado:
        return
    if not nombre.strip():
        st.error("Poné un nombre para el asado.")
        return

    slug = generar_slug(nombre)
    clave = secrets.token_urlsafe(8)
    db.crear_asado(slug, nombre.strip(), fecha, clave)

    st.success("¡Asado creado!")
    st.write("**Link para invitados** (compartilo por WhatsApp):")
    st.code(armar_link(asado=slug), language=None)
    st.write("**Tu link de organizador:**")
    st.code(armar_link(asado=slug, admin=clave), language=None)
    st.warning("Guardá el link de organizador: es la única forma de ver las respuestas y la lista de compras.")


def pantalla_invitado(asado):
    st.title(f"🔥 {asado['nombre']}")
    if asado["fecha"]:
        st.caption(f"Fecha: {asado['fecha']:%d/%m/%Y}")
    st.write("Contanos qué querés comer así compramos lo justo (y un poco más).")

    # Fuera del form para que al tildarla se oculten las carnes al instante.
    vegetariano = st.checkbox("¿Es vegetariano/a?")

    with st.form("respuesta"):
        nombre = st.text_input("Nombre")
        st.caption("Si alguien más tiene tu nombre, agregá tu apellido.")
        chico = st.checkbox("¿Es chico/a?")
        apetito = st.radio("Apetito", config.APETITOS, index=1, horizontal=True)

        elecciones = {}
        for categoria, opciones in config.CATEGORIAS.items():
            if vegetariano and categoria != "acompanamientos":
                elecciones[categoria] = []  # se descartan carnes y achuras
                continue
            st.subheader(config.TITULOS[categoria])
            elecciones[categoria] = [op for op in opciones if st.checkbox(op, key=f"{categoria}-{op}")]

        enviado = st.form_submit_button("Enviar")

    if not enviado:
        return

    cortes = sum(len(elecciones[c]) for c in config.CARNES)
    if not nombre.strip():
        st.error("Escribí tu nombre.")
    elif vegetariano and not elecciones["acompanamientos"]:
        st.error("Elegí al menos un acompañamiento.")
    elif not vegetariano and cortes == 0:
        st.error("Elegí al menos un corte de carne (vaca, cerdo o pollo).")
    else:
        nueva = db.guardar_respuesta(asado["slug"], nombre, chico, vegetariano, apetito, elecciones)
        if nueva:
            st.success(f"¡Gracias, {nombre.strip()}! Guardamos tu respuesta.")
        else:
            st.success(f"Listo, {nombre.strip()}: actualizamos tu respuesta anterior.")


def pantalla_organizador(asado):
    st.title(f"🔥 {asado['nombre']}")
    if asado["fecha"]:
        st.caption(f"Fecha: {asado['fecha']:%d/%m/%Y}")
    st.write("**Link para invitados:**")
    st.code(armar_link(asado=asado["slug"]), language=None)

    # Cualquier botón vuelve a correr el script, y eso ya relee la base.
    st.button("🔄 Actualizar")

    respuestas = db.listar_respuestas(asado["slug"])
    st.subheader(f"Respuestas: {len(respuestas)}")
    if not respuestas:
        st.info("Todavía no respondió nadie. Compartí el link para invitados.")
        return

    tabla = [
        {
            "Nombre": r["nombre"],
            "Chico/a": r["es_chico"],
            "Vegetariano/a": r["es_vegetariano"],
            "Apetito": r["apetito"],
            "Elecciones": ", ".join(op for opciones in r["elecciones"].values() for op in opciones),
        }
        for r in respuestas
    ]
    st.dataframe(tabla, hide_index=True)


# --- Ruteo ---

slug = st.query_params.get("asado")
if not slug:
    pantalla_crear()
else:
    asado = db.obtener_asado(slug)
    if asado is None:
        st.error("No encontramos ese asado. Revisá que el link esté completo.")
    elif "admin" in st.query_params:
        if st.query_params["admin"] == asado["clave_admin"]:
            pantalla_organizador(asado)
        else:
            st.error("La clave de organizador no es correcta. Revisá que el link esté completo.")
    else:
        pantalla_invitado(asado)
