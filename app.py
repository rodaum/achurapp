"""App de Streamlit: ruteo por parámetros de URL y pantallas."""

import re
import secrets
import string
import unicodedata
from urllib.parse import quote, urlencode

import streamlit as st

import calculo
import config
import db

st.set_page_config(page_title="Achurapp", page_icon="🔥")

APETITOS = {"poco": "🐣 Poco", "normal": "🙂 Normal", "mucho": "🦁 Mucho"}
ICONOS_SECCION = {"Carnicería": "🥩", "Verdulería": "🥬", "Almacén": "🏪"}


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


def link_whatsapp(texto):
    """Abre WhatsApp con el texto ya escrito; la persona elige a quién mandarlo."""
    return "https://wa.me/?text=" + quote(texto)


def encabezado(asado):
    st.title(f"🔥 {asado['nombre']}")
    if asado["fecha"]:
        st.badge(f"{asado['fecha']:%d/%m/%Y}", icon="📅", color="orange")


def tarjeta_invitados(asado):
    link = armar_link(asado=asado["slug"])
    with st.container(border=True):
        st.markdown("**👥 Link para invitados**")
        st.code(link, language=None)
        invitacion = f"🔥 ¡Asado: {asado['nombre']}! Contanos qué querés comer: {link}"
        st.link_button("💬 Compartir por WhatsApp", link_whatsapp(invitacion), type="primary", width="stretch")


def pantalla_crear():
    st.title("🔥 Achurapp")
    st.write("Armá la lista de compras de tu asado para que **sobre y no falte**.")
    with st.form("crear"):
        nombre = st.text_input("¿Cómo se llama el asado?", placeholder="Cumple de Juan")
        fecha = st.date_input("Fecha (opcional)", value=None, format="DD/MM/YYYY")
        creado = st.form_submit_button("Crear asado", type="primary", width="stretch")

    if not creado:
        return
    if not nombre.strip():
        st.error("Poné un nombre para el asado.")
        return

    slug = generar_slug(nombre)
    clave = secrets.token_urlsafe(8)
    db.crear_asado(slug, nombre.strip(), fecha, clave)

    st.success("¡Asado creado! 🎉")
    tarjeta_invitados({"slug": slug, "nombre": nombre.strip()})
    with st.container(border=True):
        st.markdown("**🔑 Tu link de organizador**")
        st.code(armar_link(asado=slug, admin=clave), language=None)
        st.warning("Guardalo: es la única forma de ver las respuestas y la lista de compras.")


def pantalla_invitado(asado):
    encabezado(asado)
    st.write("Contanos qué querés comer así compramos lo justo (y un poco más).")

    # Fuera del form para que al activarlo se oculten las carnes al instante.
    vegetariano = st.toggle("🥦 Vegetariano/a")

    with st.form("respuesta", border=False):
        nombre = st.text_input("Nombre")
        st.caption("Si alguien más tiene tu nombre, agregá tu apellido.")
        chico = st.toggle("🧒 Chico/a")
        apetito = st.segmented_control(
            "Apetito", list(APETITOS), default="normal", required=True, format_func=APETITOS.get
        )

        elecciones = {categoria: [] for categoria in config.CATEGORIAS}  # si es vegetariano/a, carnes y achuras quedan vacías
        for categoria, opciones in config.CATEGORIAS.items():
            if vegetariano and categoria != "acompanamientos":
                continue
            with st.container(border=True):
                elecciones[categoria] = st.pills(
                    config.TITULOS[categoria], opciones, selection_mode="multi", format_func=str.capitalize, key=categoria
                )

        enviado = st.form_submit_button("Enviar", type="primary", width="stretch")

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
        st.balloons()


def pantalla_organizador(asado):
    encabezado(asado)
    # Cualquier botón vuelve a correr el script, y eso ya relee la base.
    st.button("🔄 Actualizar")

    respuestas = db.listar_respuestas(asado["slug"])
    if not respuestas:
        st.info("Todavía no respondió nadie. ¡Compartí el link!")
        tarjeta_invitados(asado)
        return

    lista = calculo.calcular_lista(respuestas)
    kg_carne = sum(cantidad for cantidad, unidad in lista["Carnicería"].values() if unidad == "kg")
    columnas = st.columns(4)
    columnas[0].metric("👥 Respuestas", len(respuestas), border=True)
    columnas[1].metric("🥦 Vegetarianos", sum(r["es_vegetariano"] for r in respuestas), border=True)
    columnas[2].metric("🧒 Chicos/as", sum(r["es_chico"] for r in respuestas), border=True)
    columnas[3].metric("🥩 Carne", calculo.formatear(kg_carne, "kg"), border=True)

    compras, gente, invitar = st.tabs(["🛒 Lista de compras", "👥 Respuestas", "📨 Invitar"])

    with compras:
        for seccion, items in lista.items():
            if items:
                with st.container(border=True):
                    renglones = [f"- {item.capitalize()}: {calculo.formatear(*cantidad)}" for item, cantidad in items.items()]
                    st.markdown(f"**{ICONOS_SECCION[seccion]} {seccion}**\n" + "\n".join(renglones))

        texto = calculo.texto_whatsapp(asado["nombre"], lista)
        izquierda, derecha = st.columns(2)
        izquierda.link_button("💬 Enviar por WhatsApp", link_whatsapp(texto), type="primary", width="stretch")
        derecha.download_button("⬇️ Descargar .txt", texto, file_name=f"compras-{asado['slug']}.txt", width="stretch")
        with st.expander("📋 Ver texto para copiar"):
            st.code(texto, language=None)

    with gente:
        tabla = [
            {
                "Nombre": r["nombre"],
                "Chico/a": r["es_chico"],
                "Vegetariano/a": r["es_vegetariano"],
                "Apetito": APETITOS[r["apetito"]],
                "Elecciones": ", ".join(op.capitalize() for opciones in r["elecciones"].values() for op in opciones),
            }
            for r in respuestas
        ]
        st.dataframe(tabla, hide_index=True)

    with invitar:
        tarjeta_invitados(asado)


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
