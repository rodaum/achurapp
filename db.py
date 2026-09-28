"""Acceso a datos.

Etapa 2: guarda todo en memoria, compartido entre sesiones. En la etapa 3
se reemplaza la implementación por Postgres sin cambiar estas funciones.
"""

import streamlit as st


@st.cache_resource
def _memoria():
    return {"asados": {}, "respuestas": {}}


def crear_asado(slug, nombre, fecha, clave_admin):
    _memoria()["asados"][slug] = {
        "slug": slug,
        "nombre": nombre,
        "fecha": fecha,
        "clave_admin": clave_admin,
    }


def obtener_asado(slug):
    """Devuelve el asado como diccionario, o None si no existe."""
    return _memoria()["asados"].get(slug)


def guardar_respuesta(asado_slug, nombre, es_chico, es_vegetariano, apetito, elecciones):
    """Crea o actualiza la respuesta de un invitado. Devuelve True si es nueva.

    La persona se identifica por su nombre sin espacios al borde y en minúsculas.
    """
    nombre = nombre.strip()
    clave = (asado_slug, nombre.lower())
    respuestas = _memoria()["respuestas"]
    nueva = clave not in respuestas
    respuestas[clave] = {
        "nombre": nombre,
        "es_chico": es_chico,
        "es_vegetariano": es_vegetariano,
        "apetito": apetito,
        "elecciones": elecciones,
    }
    return nueva
