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
    items |= {acomp: (unidad, seccion) for acomp, (_, unidad, seccion) in config.ACOMPANAMIENTOS.items()}
    items["pan"] = ("g", "Almacén")
    return items


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
            cortes = [corte for categoria in config.CARNES for corte in elecciones.get(categoria, [])]
            for corte in cortes:
                total[corte] += config.GRAMOS_CARNE_POR_ADULTO * f / len(cortes)
            for achura in elecciones.get("achuras", []):
                total[achura] += config.ACHURAS[achura][0] * f
        f_acomp = f * config.FACTOR_VEGETARIANO_ACOMPANAMIENTOS if p["es_vegetariano"] else f
        for acomp in elecciones.get("acompanamientos", []):
            total[acomp] += config.ACOMPANAMIENTOS[acomp][0] * f_acomp
        total["pan"] += config.GRAMOS_PAN_POR_PERSONA * f
    return total


def calcular_lista(respuestas):
    """Devuelve {sección: {ítem: (cantidad, unidad)}} con unidad "kg", "u" o "bolsa"."""
    total = _sumar_pedidos(respuestas)
    lista = {seccion: {} for seccion in SECCIONES}
    kg_carne_y_achuras = 0  # con extra y antes de redondear: base del carbón

    for item, (unidad, seccion) in _items().items():
        if not total.get(item):
            continue  # nadie lo eligió
        con_extra = total[item] * (1 + config.EXTRA)
        if unidad == "g":
            gramos = _hacia_arriba(con_extra / config.REDONDEO_GRAMOS) * config.REDONDEO_GRAMOS
            lista[seccion][item] = (gramos / 1000, "kg")
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
    """(1.25, "kg") -> "1,25 kg"; (1, "u") -> "1 unidad"; (2, "bolsa") -> "2 bolsas de 4 kg"."""
    if unidad == "kg":
        return f"{cantidad:g} kg".replace(".", ",")
    if unidad == "bolsa":
        return f"{cantidad} {'bolsa' if cantidad == 1 else 'bolsas'} de {config.KG_BOLSA_CARBON} kg"
    return f"{cantidad} {'unidad' if cantidad == 1 else 'unidades'}"


def texto_whatsapp(nombre_asado, lista):
    """Lista de compras como texto para pegar en WhatsApp (*negrita*)."""
    lineas = [f"*Compras para {nombre_asado}*"]
    for seccion, items in lista.items():
        if items:
            lineas += ["", f"*{seccion}*"]
            lineas += [f"- {item}: {formatear(*cantidad)}" for item, cantidad in items.items()]
    return "\n".join(lineas)
