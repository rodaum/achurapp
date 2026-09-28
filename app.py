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


def etiqueta(opcion):
    """Texto de cada opción en el formulario: 'medallones' -> 'Medallones (soja, lentejas, garbanzos)'."""
    return config.ETIQUETAS.get(opcion, opcion).capitalize()


def resumen(elecciones):
    """Elecciones en una línea para la tabla del organizador."""
    texto = ", ".join(op.capitalize() for categoria in config.CATEGORIAS for op in elecciones.get(categoria, []))
    if elecciones.get("sin_ensalada"):
        texto += f" (ensalada sin {', '.join(elecciones['sin_ensalada'])})"
    return texto


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


def tarjeta_link_personal(asado, token):
    link = armar_link(asado=asado["slug"], invitado=token)
    with st.container(border=True):
        st.markdown("**🔗 Tu link personal**")
        st.code(link, language=None)
        st.caption("Guardalo: es la única forma de ver y cambiar tu respuesta.")
        mensaje = f"Mi link para cambiar mi respuesta del asado {asado['nombre']}: {link}"
        st.link_button("💬 Mandármelo por WhatsApp", link_whatsapp(mensaje), width="stretch")


def pantalla_invitado(asado, token=None, respuesta=None):
    """Sin token: respuesta nueva (link del grupo). Con token: edición de la propia (link personal)."""
    encabezado(asado)
    if asado["cerrado"]:
        st.info("El formulario está cerrado: ya se hicieron las compras 🛒")
        return

    previa = respuesta or {}
    elecciones_previas = previa.get("elecciones", {})
    if respuesta:
        with st.expander("🔗 Tu link personal"):
            tarjeta_link_personal(asado, token)
        st.write("Podés cambiar tu respuesta cuando quieras, hasta que se cierre el formulario.")
        nombre = st.text_input("Nombre", value=respuesta["nombre"], disabled=True)
    else:
        st.write("Contanos qué querés comer así compramos lo justo (y un poco más).")
        nombre = st.text_input("Nombre")
        st.caption("Si alguien más tiene tu nombre, agregá tu apellido.")

    # Sin st.form: cada cambio se refleja al instante (ocultar carnes, preguntar por la ensalada).
    chico = st.toggle("🧒 Chico/a", value=previa.get("es_chico", False))
    vegetariano = st.toggle("🥦 Vegetariano/a", value=previa.get("es_vegetariano", False))
    apetito = st.segmented_control(
        "Apetito", list(APETITOS), default=previa.get("apetito", "normal"), required=True, format_func=APETITOS.get
    )

    # Lo que no se muestra queda vacío: si es vegetariano/a, carnes y achuras.
    elecciones = {categoria: [] for categoria in config.CATEGORIAS} | {"sin_ensalada": []}
    for categoria, opciones in config.CATEGORIAS.items():
        titulo = config.TITULOS[categoria]
        if vegetariano and categoria in [*config.CARNES, "achuras"]:
            continue
        if categoria == "acompanamientos":
            if vegetariano:
                titulo = config.TITULO_ACOMPANAMIENTOS_VEGETARIANO
            else:
                opciones = [op for op in opciones if op not in config.SOLO_VEGETARIANOS]
        with st.container(border=True):
            # La clave cambia con las opciones para que Streamlit no conserve una opción que ya no está.
            # Se precargan las elecciones previas que sigan existiendo entre las opciones.
            previas = [op for op in elecciones_previas.get(categoria, []) if op in opciones]
            elecciones[categoria] = st.pills(
                titulo, opciones, selection_mode="multi", default=previas, format_func=etiqueta,
                key=f"{categoria}-{len(opciones)}",
            )
            if "ensalada" in elecciones[categoria]:
                elecciones["sin_ensalada"] = st.pills(
                    "Ensalada criolla: lechuga, tomate y cebolla. ¿Le sacamos algo?",
                    config.ENSALADA, selection_mode="multi", default=elecciones_previas.get("sin_ensalada", []),
                    format_func=str.capitalize, key="sin_ensalada",
                )

    if not st.button("Enviar", type="primary", width="stretch"):
        return

    cortes = sum(len(elecciones[c]) for c in config.CARNES)
    if not nombre.strip():
        st.error("Escribí tu nombre.")
    elif not vegetariano and cortes == 0:
        st.error("Elegí al menos un corte de carne (vaca, cerdo o pollo).")
    elif vegetariano and not (elecciones["verduras"] or elecciones["acompanamientos"]):
        st.error("Elegí al menos una verdura o algo de tu menú.")
    elif len(elecciones["sin_ensalada"]) == len(config.ENSALADA):
        st.error("A la ensalada le tiene que quedar al menos un ingrediente.")
    elif respuesta:
        db.actualizar_respuesta(asado["slug"], token, chico, vegetariano, apetito, elecciones)
        st.success(f"Listo, {nombre}: actualizamos tu respuesta.")
        st.balloons()
    else:
        token = db.crear_respuesta(asado["slug"], nombre, chico, vegetariano, apetito, elecciones)
        if token is None:
            st.error("Ya hay una respuesta con ese nombre. Si sos vos, entrá con tu link personal; si no, agregá tu apellido.")
            return
        # La URL pasa a ser el link personal: si toca algo más, sigue editando su propia respuesta.
        st.query_params["invitado"] = token
        st.success(f"¡Gracias, {nombre.strip()}! Guardamos tu respuesta.")
        tarjeta_link_personal(asado, token)
        st.balloons()


def cambiar_formulario(slug):
    """Se ejecuta al tocar el toggle, antes de volver a correr la pantalla."""
    db.cambiar_cerrado(slug, not st.session_state["abierto"])


def pantalla_organizador(asado):
    encabezado(asado)
    # Cualquier botón vuelve a correr el script, y eso ya relee la base.
    st.button("🔄 Actualizar")

    # El estado real está en la base. Con una key fija y on_change, cada toque se guarda
    # antes de redibujar (si el valor cambiaba la identidad del toggle, había que tocarlo dos veces).
    st.session_state["abierto"] = not asado["cerrado"]
    st.toggle("📝 Formulario abierto", key="abierto", on_change=cambiar_formulario, args=(asado["slug"],))
    if asado["cerrado"]:
        st.warning("Formulario cerrado: nadie puede responder ni cambiar su respuesta.")

    respuestas = db.listar_respuestas(asado["slug"])
    if not respuestas:
        st.info("Todavía no respondió nadie. ¡Compartí el link!")
        tarjeta_invitados(asado)
        return

    lista = calculo.calcular_lista(respuestas)
    gramos_carne = sum(cantidad for cantidad, unidad in lista["Carnicería"].values() if unidad == "g")
    columnas = st.columns(4)
    columnas[0].metric("👥 Respuestas", len(respuestas), border=True)
    columnas[1].metric("🥦 Vegetarianos", sum(r["es_vegetariano"] for r in respuestas), border=True)
    columnas[2].metric("🧒 Chicos/as", sum(r["es_chico"] for r in respuestas), border=True)
    columnas[3].metric("🥩 Carne", calculo.formatear(gramos_carne, "g"), border=True)

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
                "Elecciones": resumen(r["elecciones"]),
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
    elif "invitado" in st.query_params:
        token = st.query_params["invitado"]
        respuesta = db.obtener_respuesta(slug, token)
        if respuesta is None:
            st.error("Ese link personal no es válido. Revisá que esté completo.")
        else:
            pantalla_invitado(asado, token, respuesta)
    else:
        pantalla_invitado(asado)
