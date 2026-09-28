"""Tests de calculo.py. Cada caso trae la cuenta hecha a mano en el comentario."""

import pytest

import calculo


def persona(apetito="normal", chico=False, vegetariano=False, **elecciones):
    return {"nombre": "x", "es_chico": chico, "es_vegetariano": vegetariano, "apetito": apetito, "elecciones": elecciones}


def test_adulto_normal_un_corte():
    lista = calculo.calcular_lista([persona(vaca=["vacío"])])
    # vacío: 400 g × 1,15 = 460 g -> 500 g
    assert lista["Carnicería"] == {"vacío": (0.5, "kg")}
    # pan: 120 g × 1,15 = 138 g -> 250 g; carbón: 0,46 kg -> 1 bolsa
    assert lista["Almacén"] == {"pan": (0.25, "kg"), "carbón": (1, "bolsa")}


def test_reparto_entre_cortes():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], cerdo=["bondiola"])] * 5)
    # cada corte: 5 × 200 g = 1000 g × 1,15 = 1150 g -> 1250 g
    assert lista["Carnicería"] == {"vacío": (1.25, "kg"), "bondiola": (1.25, "kg")}


def test_chico():
    lista = calculo.calcular_lista([persona(chico=True, vaca=["vacío"])] * 4)
    # 4 × 400 g × 0,5 = 800 g × 1,15 = 920 g -> 1000 g
    assert lista["Carnicería"]["vacío"] == (1.0, "kg")


@pytest.mark.parametrize(
    "apetito, kg",
    [
        ("poco", 1.5),  # 4 × 300 g = 1200 g × 1,15 = 1380 g -> 1500 g
        ("normal", 2.0),  # 4 × 400 g = 1600 g × 1,15 = 1840 g -> 2000 g
        ("mucho", 2.5),  # 4 × 520 g = 2080 g × 1,15 = 2392 g -> 2500 g
    ],
)
def test_apetito(apetito, kg):
    lista = calculo.calcular_lista([persona(apetito=apetito, vaca=["vacío"])] * 4)
    assert lista["Carnicería"]["vacío"] == (kg, "kg")


def test_vegetariano_sin_carne_y_acompanamientos_por_dos():
    veg = persona(vegetariano=True, vaca=["vacío"], achuras=["chorizo"], acompanamientos=["choclo"])
    lista = calculo.calcular_lista([veg])
    assert lista["Carnicería"] == {}
    # choclo: 1 × 2 × 1,15 = 2,3 -> 3 (un no vegetariano: 1,15 -> 2)
    assert lista["Verdulería"] == {"choclo": (3, "u")}
    # sin carne no hay carbón, pero el pan sí va
    assert lista["Almacén"] == {"pan": (0.25, "kg")}

    no_veg = calculo.calcular_lista([persona(vaca=["vacío"], acompanamientos=["choclo"])])
    assert no_veg["Verdulería"] == {"choclo": (2, "u")}


def test_extra_del_15_por_ciento():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], achuras=["chorizo"])] * 10)
    # chorizo: 10 × 1,15 = 11,5 -> 12 (sin extra serían 10)
    assert lista["Carnicería"]["chorizo"] == (12, "u")
    # vacío: 4000 g × 1,15 = 4600 g -> 4750 g
    assert lista["Carnicería"]["vacío"] == (4.75, "kg")


def test_se_redondea_el_total_y_no_cada_aporte():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], cerdo=["bondiola"], pollo=["pata muslo"])] * 3)
    # cada corte: 3 × 133,3 g = 400 g × 1,15 = 460 g -> 500 g (redondeando cada aporte serían 750 g)
    assert lista["Carnicería"] == {"vacío": (0.5, "kg"), "bondiola": (0.5, "kg"), "pata muslo": (0.5, "kg")}


def test_redondeo_de_unidades_y_gramos():
    lista = calculo.calcular_lista(
        [persona(vaca=["vacío"], achuras=["morcilla", "mollejas"], acompanamientos=["provoleta", "ensalada"])]
    )
    assert lista["Carnicería"]["morcilla"] == (1, "u")  # 0,5 × 1,15 = 0,575 -> 1
    assert lista["Carnicería"]["mollejas"] == (0.25, "kg")  # 100 g × 1,15 = 115 g -> 250 g
    assert lista["Almacén"]["provoleta"] == (1, "u")  # 0,5 × 1,15 = 0,575 -> 1
    assert lista["Verdulería"]["ensalada"] == (0.25, "kg")  # 200 g × 1,15 = 230 g -> 250 g


def test_carbon_en_bolsas_incluye_chorizos():
    solo_carne = calculo.calcular_lista([persona(vaca=["vacío"])] * 8)
    # 8 × 400 g × 1,15 = 3,68 kg -> 1 bolsa de 4 kg
    assert solo_carne["Almacén"]["carbón"] == (1, "bolsa")

    con_chorizo = calculo.calcular_lista([persona(vaca=["vacío"], achuras=["chorizo"])] * 8)
    # 3,68 kg + 8 × 1,15 chorizos × 100 g = 3,68 + 0,92 = 4,6 kg -> 2 bolsas
    assert con_chorizo["Almacén"]["carbón"] == (2, "bolsa")


def test_items_no_elegidos_no_aparecen():
    lista = calculo.calcular_lista([persona(vaca=["vacío"])])
    assert list(lista["Carnicería"]) == ["vacío"]
    assert lista["Verdulería"] == {}
    assert "provoleta" not in lista["Almacén"]


def test_formato_para_whatsapp():
    assert calculo.formatear(1.25, "kg") == "1,25 kg"
    assert calculo.formatear(1, "u") == "1 unidad"
    assert calculo.formatear(2, "bolsa") == "2 bolsas de 4 kg"
    texto = calculo.texto_whatsapp("Cumple", calculo.calcular_lista([persona(vaca=["vacío"])]))
    assert texto == "*Compras para Cumple*\n\n*Carnicería*\n- Vacío: 0,5 kg\n\n*Almacén*\n- Pan: 0,25 kg\n- Carbón: 1 bolsa de 4 kg"
