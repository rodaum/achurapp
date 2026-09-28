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
    "chinchulines": (60, "g"),
    "mollejas": (60, "g"),
    "riñón": (50, "g"),
}

# Verduras a la parrilla (Verdulería): cada una aporta GRAMOS_POR_VERDURA por persona,
# con un tope de TOPE_GRAMOS_VERDURAS por persona (si elige más, se reparten).
VERDURAS = ["morrón", "cebolla", "berenjena", "zapallito", "papa", "batata"]
GRAMOS_POR_VERDURA = 100
TOPE_GRAMOS_VERDURAS = 300
CHOCLOS_POR_PERSONA = 1  # en la misma sección del formulario, pero en unidades y fuera del tope

# Ensalada criolla: GRAMOS_ENSALADA por persona, repartidos entre los ingredientes que quiere.
ENSALADA = ["lechuga", "tomate", "cebolla"]
GRAMOS_ENSALADA = 200

# Acompañamiento con cantidad fija: (cantidad por persona, unidad, sección de compra).
ACOMPANAMIENTOS = {
    "provoleta": (0.5, "u", "Almacén"),
    "medallones": (1, "u", "Almacén"),  # solo se ofrece a vegetarianos
}
SOLO_VEGETARIANOS = ["medallones"]

# Categorías tal como se guardan en `elecciones` y cómo se muestran.
# Además, `elecciones["sin_ensalada"]` guarda los ingredientes que se sacan de la ensalada.
CATEGORIAS = {
    **CARNES,
    "achuras": list(ACHURAS),
    "verduras": VERDURAS + ["choclo"],
    "acompanamientos": ["provoleta", "ensalada", "medallones"],
}
TITULOS = {
    "vaca": "🐄 Vaca",
    "cerdo": "🐖 Cerdo",
    "pollo": "🐔 Pollo",
    "achuras": "🌭 Achuras",
    "verduras": "🫑 Verduras a la parrilla",
    "acompanamientos": "🥗 Acompañamientos",
}
TITULO_ACOMPANAMIENTOS_VEGETARIANO = "🌱 Tu menú"
ETIQUETAS = {"medallones": "medallones (soja, lentejas, garbanzos)", "ensalada": "ensalada criolla"}

# --- Cálculo ---

FACTOR_APETITO = {"poco": 0.75, "normal": 1.0, "mucho": 1.3}
FACTOR_CHICO = 0.5
FACTOR_VEGETARIANO_ACOMPANAMIENTOS = 2  # también verduras y ensalada

GRAMOS_CARNE_POR_ADULTO = 400
GRAMOS_PAN_POR_PERSONA = 120

# Peso por unidad, solo para calcular el carbón.
PESO_CHORIZO = 100
PESO_MORCILLA = 100

KG_CARBON_POR_KG_CARNE = 1
KG_BOLSA_CARBON = 4

EXTRA = 0.15
SIN_EXTRA = ["provoleta", "medallones"]  # se compran enteros: el extra los inflaba
REDONDEO_GRAMOS = 10
