"""Acceso a datos en Postgres (Neon) vía st.connection("sql").

La cadena de conexión se lee de .streamlit/secrets.toml ([connections.sql]).
"""

import json
import secrets

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

# Columnas agregadas en la etapa 10: así también se suman a las tablas que ya existen en Neon.
AGREGAR_COLUMNAS = [
    "ALTER TABLE asados ADD COLUMN IF NOT EXISTS cerrado BOOLEAN NOT NULL DEFAULT false",
    "ALTER TABLE respuestas ADD COLUMN IF NOT EXISTS token TEXT",
]

# Si el nombre ya respondió no hace nada y no devuelve filas: no se pisa la respuesta de otro.
CREAR_RESPUESTA = """
INSERT INTO respuestas (asado_slug, nombre, nombre_clave, token, es_chico, es_vegetariano, apetito, elecciones)
VALUES (:asado_slug, :nombre, :nombre_clave, :token, :es_chico, :es_vegetariano, :apetito, CAST(:elecciones AS JSONB))
ON CONFLICT (asado_slug, nombre_clave) DO NOTHING
RETURNING token"""

ACTUALIZAR_RESPUESTA = """
UPDATE respuestas SET
    es_chico = :es_chico,
    es_vegetariano = :es_vegetariano,
    apetito = :apetito,
    elecciones = CAST(:elecciones AS JSONB),
    actualizado_en = now()
WHERE asado_slug = :asado_slug AND token = :token"""


@st.cache_resource
def _conexion():
    """Conecta una sola vez por proceso y crea las tablas y columnas si no existen."""
    # pool_pre_ping: Neon cierra las conexiones cuando suspende la base.
    conn = st.connection("sql", pool_pre_ping=True)
    with conn.session as s:
        for sql in [CREAR_ASADOS, CREAR_RESPUESTAS, *AGREGAR_COLUMNAS]:
            s.execute(text(sql))
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
            text("SELECT slug, nombre, fecha, clave_admin, cerrado FROM asados WHERE slug = :slug"),
            {"slug": slug},
        ).mappings().first()
    return dict(fila) if fila else None


def cambiar_cerrado(slug, cerrado):
    """Abre o cierra el formulario del asado."""
    with _conexion().session as s:
        s.execute(text("UPDATE asados SET cerrado = :cerrado WHERE slug = :slug"), {"slug": slug, "cerrado": cerrado})
        s.commit()


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


def obtener_respuesta(asado_slug, token):
    """La respuesta del link personal, o None si el token no corresponde a este asado."""
    with _conexion().session as s:
        fila = s.execute(
            text(
                "SELECT nombre, es_chico, es_vegetariano, apetito, elecciones FROM respuestas "
                "WHERE asado_slug = :slug AND token = :token"
            ),
            {"slug": asado_slug, "token": token},
        ).mappings().first()
    return dict(fila) if fila else None


def crear_respuesta(asado_slug, nombre, es_chico, es_vegetariano, apetito, elecciones):
    """Guarda una respuesta nueva y devuelve su token personal, o None si ese nombre ya respondió.

    El nombre se compara sin espacios al borde y en minúsculas.
    """
    nombre = nombre.strip()
    params = {
        "asado_slug": asado_slug,
        "nombre": nombre,
        "nombre_clave": nombre.lower(),
        "token": secrets.token_urlsafe(8),
        "es_chico": es_chico,
        "es_vegetariano": es_vegetariano,
        "apetito": apetito,
        "elecciones": json.dumps(elecciones, ensure_ascii=False),
    }
    with _conexion().session as s:
        fila = s.execute(text(CREAR_RESPUESTA), params).first()
        s.commit()
    return fila[0] if fila else None


def actualizar_respuesta(asado_slug, token, es_chico, es_vegetariano, apetito, elecciones):
    """Edita la respuesta del link personal (el nombre no cambia)."""
    params = {
        "asado_slug": asado_slug,
        "token": token,
        "es_chico": es_chico,
        "es_vegetariano": es_vegetariano,
        "apetito": apetito,
        "elecciones": json.dumps(elecciones, ensure_ascii=False),
    }
    with _conexion().session as s:
        s.execute(text(ACTUALIZAR_RESPUESTA), params)
        s.commit()
