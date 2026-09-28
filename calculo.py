"""Cálculo de la lista de compras (reglas en SPEC.md). Funciones puras: sin Streamlit ni base."""

import math
from collections import defaultdict

import config

SECCIONES = ["Carnicería", "Verdulería", "Almacén"]
PESO_POR_UNIDAD = {"chorizo": config.PESO_CHORIZO, "morcilla": config.PESO_MORCILLA}


def _items():
    """Cada ítem que se compra -> (unidad, sección), en el orden en que se lista.

    Unidad: "g" (se compra en kg) o "u" (unidades).
    """
    items = {corte: ("g", "Carnicería") for cortes in config.CARNES.values() for corte in cortes}
    items |= {achura: (unidad, "Carnicería") for achura, (_, unidad) in config.ACHURAS.items()}
    # La cebolla está en verduras y en ensalada: queda un solo renglón con la suma.
    items |= {verdura: ("g", "Verdulería") for verdura in config.VERDURAS + config.ENSALADA}
    items["choclo"] = ("u", "Verdulería")
    items |= {acomp: (unidad, seccion) for acomp, (_, unidad, seccion) in config.ACOMPANAMIENTOS.items()}
    items["pan"] = ("g", "Almacén")
    return items


def _elegidas(elecciones, categoria, validas):
    """Opciones elegidas en la categoría, ignorando las que ya no existen (respuestas viejas)."""
    return [op for op in elecciones.get(categoria, []) if op in validas]


def _hacia_arriba(valor):
    # round() evita que un error de coma flotante (ej. 2.0000000001) sume uno de más.
    return math.ceil(round(valor, 6))


def factor(persona):
    f = config.FACTOR_APETITO[persona["apetito"]]
    return f * config.FACTOR_CHICO if persona["es_chico"] else f


def _sumar_pedidos(respuestas):
    """Total por ítem, sin extra ni redondeo, en gramos o unidades."""
    total = defaultdict(float)
    for p in respuestas:
        f = factor(p)
        elecciones = p["elecciones"]
        if not p["es_vegetariano"]:
            cortes = [corte for cat, validos in config.CARNES.items() for corte in _elegidas(elecciones, cat, validos)]
            for corte in cortes:
                total[corte] += config.GRAMOS_CARNE_POR_ADULTO * f / len(cortes)
            for achura in _elegidas(elecciones, "achuras", config.ACHURAS):
                total[achura] += config.ACHURAS[achura][0] * f

        # Verduras, ensalada y acompañamientos: los vegetarianos cuentan doble.
        f_acomp = f * config.FACTOR_VEGETARIANO_ACOMPANAMIENTOS if p["es_vegetariano"] else f

        verduras = _elegidas(elecciones, "verduras", config.VERDURAS)
        for verdura in verduras:
            total[verdura] += min(config.GRAMOS_POR_VERDURA, config.TOPE_GRAMOS_VERDURAS / len(verduras)) * f_acomp
        if "choclo" in elecciones.get("verduras", []):
            total["choclo"] += config.CHOCLOS_POR_PERSONA * f_acomp

        acompanamientos = elecciones.get("acompanamientos", [])
        if "ensalada" in acompanamientos:
            ingredientes = [i for i in config.ENSALADA if i not in elecciones.get("sin_ensalada", [])]
            for ingrediente in ingredientes:
                total[ingrediente] += config.GRAMOS_ENSALADA / len(ingredientes) * f_acomp
        for acomp in _elegidas(elecciones, "acompanamientos", config.ACOMPANAMIENTOS):
            total[acomp] += config.ACOMPANAMIENTOS[acomp][0] * f_acomp

        total["pan"] += config.GRAMOS_PAN_POR_PERSONA * f
    return total


def calcular_lista(respuestas):
    """Devuelve {sección: {ítem: (cantidad, unidad)}} con unidad "g", "u" o "bolsa"."""
    total = _sumar_pedidos(respuestas)
    lista = {seccion: {} for seccion in SECCIONES}
    kg_carne_y_achuras = 0  # con extra y antes de redondear: base del carbón

    for item, (unidad, seccion) in _items().items():
        if not total.get(item):
            continue  # nadie lo eligió
        extra = 0 if item in config.SIN_EXTRA else config.EXTRA
        con_extra = total[item] * (1 + extra)
        if unidad == "g":
            gramos = _hacia_arriba(con_extra / config.REDONDEO_GRAMOS) * config.REDONDEO_GRAMOS
            lista[seccion][item] = (gramos, "g")
            kg = con_extra / 1000
        else:
            lista[seccion][item] = (_hacia_arriba(con_extra), "u")
            kg = con_extra * PESO_POR_UNIDAD.get(item, 0) / 1000
        if seccion == "Carnicería":
            kg_carne_y_achuras += kg

    if kg_carne_y_achuras:
        kg_carbon = kg_carne_y_achuras * config.KG_CARBON_POR_KG_CARNE
        lista["Almacén"]["carbón"] = (_hacia_arriba(kg_carbon / config.KG_BOLSA_CARBON), "bolsa")
    return lista


def formatear(cantidad, unidad):
    """(460, "g") -> "460 g"; (1380, "g") -> "1,38 kg"; (1, "u") -> "1 unidad"; (2, "bolsa") -> "2 bolsas de 4 kg"."""
    if unidad == "g":
        return f"{cantidad} g" if cantidad < 1000 else f"{cantidad / 1000:.2f} kg".replace(".", ",")
    if unidad == "bolsa":
        return f"{cantidad} {'bolsa' if cantidad == 1 else 'bolsas'} de {config.KG_BOLSA_CARBON} kg"
    return f"{cantidad} {'unidad' if cantidad == 1 else 'unidades'}"


def texto_whatsapp(nombre_asado, lista):
    """Lista de compras como texto para pegar en WhatsApp (*negrita*)."""
    lineas = [f"*Compras para {nombre_asado}*"]
    for seccion, items in lista.items():
        if items:
            lineas += ["", f"*{seccion}*"]
            lineas += [f"- {item.capitalize()}: {formatear(*cantidad)}" for item, cantidad in items.items()]
    return "\n".join(lineas)
