"""Acceso a datos en Postgres (Neon) vía st.connection("sql").

La cadena de conexión se lee de .streamlit/secrets.toml ([connections.sql]).
"""

import json

import streamlit as st
from sqlalchemy import text

CREAR_ASADOS = """
CREATE TABLE IF NOT EXISTS asados (
    slug        TEXT PRIMARY KEY,
    nombre      TEXT NOT NULL,
    fecha       DATE,
    clave_admin TEXT NOT NULL,
    creado_en   TIMESTAMPTZ DEFAULT now()
)"""

CREAR_RESPUESTAS = """
CREATE TABLE IF NOT EXISTS respuestas (
    id              SERIAL PRIMARY KEY,
    asado_slug      TEXT NOT NULL REFERENCES asados(slug) ON DELETE CASCADE,
    nombre          TEXT NOT NULL,
    nombre_clave    TEXT NOT NULL,
    es_chico        BOOLEAN NOT NULL DEFAULT false,
    es_vegetariano  BOOLEAN NOT NULL DEFAULT false,
    apetito         TEXT NOT NULL CHECK (apetito IN ('poco','normal','mucho')),
    elecciones      JSONB NOT NULL,
    actualizado_en  TIMESTAMPTZ DEFAULT now(),
    UNIQUE (asado_slug, nombre_clave)
)"""

GUARDAR_RESPUESTA = """
INSERT INTO respuestas (asado_slug, nombre, nombre_clave, es_chico, es_vegetariano, apetito, elecciones)
VALUES (:asado_slug, :nombre, :nombre_clave, :es_chico, :es_vegetariano, :apetito, CAST(:elecciones AS JSONB))
ON CONFLICT (asado_slug, nombre_clave) DO UPDATE SET
    nombre = EXCLUDED.nombre,
    es_chico = EXCLUDED.es_chico,
    es_vegetariano = EXCLUDED.es_vegetariano,
    apetito = EXCLUDED.apetito,
    elecciones = EXCLUDED.elecciones,
    actualizado_en = now()"""


@st.cache_resource
def _conexion():
    """Conecta una sola vez por proceso y crea las tablas si no existen."""
    # pool_pre_ping: Neon cierra las conexiones cuando suspende la base.
    conn = st.connection("sql", pool_pre_ping=True)
    with conn.session as s:
        s.execute(text(CREAR_ASADOS))
        s.execute(text(CREAR_RESPUESTAS))
        s.commit()
    return conn


def crear_asado(slug, nombre, fecha, clave_admin):
    with _conexion().session as s:
        s.execute(
            text("INSERT INTO asados (slug, nombre, fecha, clave_admin) VALUES (:slug, :nombre, :fecha, :clave)"),
            {"slug": slug, "nombre": nombre, "fecha": fecha, "clave": clave_admin},
        )
        s.commit()


def obtener_asado(slug):
    """Devuelve el asado como diccionario, o None si no existe."""
    with _conexion().session as s:
        fila = s.execute(
            text("SELECT slug, nombre, fecha, clave_admin FROM asados WHERE slug = :slug"),
            {"slug": slug},
        ).mappings().first()
    return dict(fila) if fila else None


def listar_respuestas(asado_slug):
    """Devuelve las respuestas del asado como lista de diccionarios, ordenadas por nombre."""
    with _conexion().session as s:
        filas = s.execute(
            text(
                "SELECT nombre, es_chico, es_vegetariano, apetito, elecciones FROM respuestas "
                "WHERE asado_slug = :slug ORDER BY nombre_clave"
            ),
            {"slug": asado_slug},
        ).mappings().all()
    return [dict(fila) for fila in filas]


def guardar_respuesta(asado_slug, nombre, es_chico, es_vegetariano, apetito, elecciones):
    """Crea o actualiza la respuesta de un invitado. Devuelve True si es nueva.

    La persona se identifica por su nombre sin espacios al borde y en minúsculas.
    """
    nombre = nombre.strip()
    params = {
        "asado_slug": asado_slug,
        "nombre": nombre,
        "nombre_clave": nombre.lower(),
        "es_chico": es_chico,
        "es_vegetariano": es_vegetariano,
        "apetito": apetito,
        "elecciones": json.dumps(elecciones, ensure_ascii=False),
    }
    with _conexion().session as s:
        existe = s.execute(
            text("SELECT 1 FROM respuestas WHERE asado_slug = :asado_slug AND nombre_clave = :nombre_clave"),
            params,
        ).first()
        s.execute(text(GUARDAR_RESPUESTA), params)
        s.commit()
    return existe is None
