"""Opciones del formulario y constantes de cálculo (ver reglas de negocio en SPEC.md)."""

# --- Formulario ---

APETITOS = ["poco", "normal", "mucho"]

CARNES = {
    "vaca": ["asado de tira", "vacío", "matambre", "entraña", "colita de cuadril", "bife de chorizo"],
    "cerdo": ["bondiola", "matambre de cerdo", "costillitas"],
    "pollo": ["pata muslo", "alitas"],
}

# Achura: (cantidad por persona, unidad). "u" = unidades, "g" = gramos.
ACHURAS = {
    "chorizo": (1, "u"),
    "morcilla": (0.5, "u"),
    "chinchulines": (100, "g"),
    "mollejas": (100, "g"),
    "riñón": (80, "g"),
}

# Acompañamiento: (cantidad por persona, unidad, sección de compra).
ACOMPANAMIENTOS = {
    "provoleta": (0.5, "u", "Almacén"),
    "verduras a la parrilla": (300, "g", "Verdulería"),
    "choclo": (1, "u", "Verdulería"),
    "ensalada": (200, "g", "Verdulería"),
}

# Categorías tal como se guardan en `elecciones` y cómo se muestran.
CATEGORIAS = {**CARNES, "achuras": list(ACHURAS), "acompanamientos": list(ACOMPANAMIENTOS)}
TITULOS = {
    "vaca": "🐄 Vaca",
    "cerdo": "🐖 Cerdo",
    "pollo": "🐔 Pollo",
    "achuras": "🌭 Achuras",
    "acompanamientos": "🥗 Acompañamientos",
}

# --- Cálculo ---

FACTOR_APETITO = {"poco": 0.75, "normal": 1.0, "mucho": 1.3}
FACTOR_CHICO = 0.5
FACTOR_VEGETARIANO_ACOMPANAMIENTOS = 2

GRAMOS_CARNE_POR_ADULTO = 400
GRAMOS_PAN_POR_PERSONA = 120

# Peso por unidad, solo para calcular el carbón.
PESO_CHORIZO = 100
PESO_MORCILLA = 100

KG_CARBON_POR_KG_CARNE = 1
KG_BOLSA_CARBON = 4

EXTRA = 0.15
REDONDEO_GRAMOS = 250
