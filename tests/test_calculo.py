"""Tests de calculo.py. Cada caso trae la cuenta hecha a mano en el comentario."""

import pytest

import calculo


def persona(apetito="normal", chico=False, vegetariano=False, **elecciones):
    return {"nombre": "x", "es_chico": chico, "es_vegetariano": vegetariano, "apetito": apetito, "elecciones": elecciones}


def test_adulto_normal_un_corte():
    lista = calculo.calcular_lista([persona(vaca=["vacío"])])
    # vacío: 400 g × 1,15 = 460 g
    assert lista["Carnicería"] == {"vacío": (460, "g")}
    # pan: 120 g × 1,15 = 138 g -> 140 g; carbón: 0,46 kg -> 1 bolsa
    assert lista["Almacén"] == {"pan": (140, "g"), "carbón": (1, "bolsa")}


def test_reparto_entre_cortes():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], cerdo=["bondiola"])] * 5)
    # cada corte: 5 × 200 g = 1000 g × 1,15 = 1150 g
    assert lista["Carnicería"] == {"vacío": (1150, "g"), "bondiola": (1150, "g")}


def test_chico():
    lista = calculo.calcular_lista([persona(chico=True, vaca=["vacío"])] * 4)
    # 4 × 400 g × 0,5 = 800 g × 1,15 = 920 g
    assert lista["Carnicería"]["vacío"] == (920, "g")


@pytest.mark.parametrize(
    "apetito, gramos",
    [
        ("poco", 1380),  # 4 × 300 g = 1200 g × 1,15 = 1380 g
        ("normal", 1840),  # 4 × 400 g = 1600 g × 1,15 = 1840 g
        ("mucho", 2400),  # 4 × 520 g = 2080 g × 1,15 = 2392 g -> 2400 g
    ],
)
def test_apetito(apetito, gramos):
    lista = calculo.calcular_lista([persona(apetito=apetito, vaca=["vacío"])] * 4)
    assert lista["Carnicería"]["vacío"] == (gramos, "g")


def test_vegetariano_sin_carne_y_acompanamientos_por_dos():
    veg = persona(vegetariano=True, vaca=["vacío"], achuras=["chorizo"], verduras=["choclo"])
    lista = calculo.calcular_lista([veg])
    assert lista["Carnicería"] == {}
    # choclo: 1 × 2 × 1,15 = 2,3 -> 3 (un no vegetariano: 1,15 -> 2)
    assert lista["Verdulería"] == {"choclo": (3, "u")}
    # sin carne no hay carbón, pero el pan sí va
    assert lista["Almacén"] == {"pan": (140, "g")}

    no_veg = calculo.calcular_lista([persona(vaca=["vacío"], verduras=["choclo"])])
    assert no_veg["Verdulería"] == {"choclo": (2, "u")}


def test_extra_del_15_por_ciento():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], achuras=["chorizo"])] * 10)
    # chorizo: 10 × 1,15 = 11,5 -> 12 (sin extra serían 10)
    assert lista["Carnicería"]["chorizo"] == (12, "u")
    # vacío: 4000 g × 1,15 = 4600 g
    assert lista["Carnicería"]["vacío"] == (4600, "g")


def test_se_redondea_el_total_y_no_cada_aporte():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], cerdo=["bondiola"], pollo=["pata muslo"])] * 3)
    # cada corte: 3 × 133,3 g = 400 g × 1,15 = 460 g
    # (redondeando cada aporte: 133,3 × 1,15 = 153,3 -> 160 g × 3 = 480 g)
    assert lista["Carnicería"] == {"vacío": (460, "g"), "bondiola": (460, "g"), "pata muslo": (460, "g")}


def test_redondeo_de_unidades_y_gramos():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], achuras=["morcilla", "mollejas", "riñón"])])
    assert lista["Carnicería"]["morcilla"] == (1, "u")  # 0,5 × 1,15 = 0,575 -> 1
    assert lista["Carnicería"]["mollejas"] == (70, "g")  # 60 g × 1,15 = 69 g -> 70 g
    assert lista["Carnicería"]["riñón"] == (60, "g")  # 50 g × 1,15 = 57,5 g -> 60 g


def test_provoleta_sin_extra():
    def provoletas(respuestas):
        return calculo.calcular_lista(respuestas)["Almacén"]["provoleta"]

    adulto = persona(vaca=["vacío"], acompanamientos=["provoleta"])
    assert provoletas([adulto]) == (1, "u")  # 0,5 -> 1
    assert provoletas([adulto] * 2) == (1, "u")  # 1 (con el 15 % serían 1,15 -> 2)
    assert provoletas([adulto] * 3) == (2, "u")  # 1,5 -> 2
    veg = persona(vegetariano=True, acompanamientos=["provoleta"])
    assert provoletas([veg, adulto, adulto]) == (2, "u")  # 0,5 × 2 + 0,5 + 0,5 = 2


def test_verduras_100_g_cada_una_con_tope_de_300_g():
    una = calculo.calcular_lista([persona(vaca=["vacío"], verduras=["morrón"])])
    assert una["Verdulería"] == {"morrón": (120, "g")}  # 100 g × 1,15 = 115 g -> 120 g (no 300 g)

    todas = ["morrón", "cebolla", "berenjena", "zapallito", "papa", "batata"]
    seis = calculo.calcular_lista([persona(vaca=["vacío"], verduras=todas)])
    # 300 g / 6 = 50 g c/u × 1,15 = 57,5 g -> 60 g
    assert seis["Verdulería"] == {verdura: (60, "g") for verdura in todas}


def test_choclo_no_cuenta_para_el_tope_de_verduras():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], verduras=["morrón", "cebolla", "berenjena", "choclo"])])
    # 3 verduras × 100 g = 300 g (justo el tope) × 1,15 = 115 g -> 120 g c/u; choclo: 1,15 -> 2
    assert lista["Verdulería"] == {
        "morrón": (120, "g"), "cebolla": (120, "g"), "berenjena": (120, "g"), "choclo": (2, "u")
    }


def test_ensalada_criolla_y_sacar_ingredientes():
    completa = calculo.calcular_lista([persona(vaca=["vacío"], acompanamientos=["ensalada"])])
    # 200 g / 3 = 66,7 g × 1,15 = 76,7 g -> 80 g de cada uno
    assert completa["Verdulería"] == {"cebolla": (80, "g"), "lechuga": (80, "g"), "tomate": (80, "g")}

    sin_cebolla = calculo.calcular_lista(
        [persona(vaca=["vacío"], acompanamientos=["ensalada"], sin_ensalada=["cebolla"])]
    )
    # 200 g / 2 = 100 g × 1,15 = 115 g -> 120 g de lechuga y de tomate
    assert sin_cebolla["Verdulería"] == {"lechuga": (120, "g"), "tomate": (120, "g")}


def test_cebolla_de_ensalada_y_parrilla_en_un_renglon():
    lista = calculo.calcular_lista([persona(vaca=["vacío"], verduras=["cebolla"], acompanamientos=["ensalada"])])
    # parrilla 100 g + ensalada 66,7 g = 166,7 g × 1,15 = 191,7 g -> 200 g
    assert lista["Verdulería"]["cebolla"] == (200, "g")


def test_medallones_para_vegetarianos():
    lista = calculo.calcular_lista([persona(vegetariano=True, acompanamientos=["medallones"])])
    # 1 × 2 (vegetariano) = 2, sin el 15 % extra porque se compran enteros
    assert lista["Almacén"]["medallones"] == (2, "u")


def test_opciones_que_ya_no_existen_se_ignoran():
    vieja = persona(vaca=["vacío", "corte inventado"], acompanamientos=["verduras a la parrilla", "choclo"])
    lista = calculo.calcular_lista([vieja])
    # el vacío se lleva los 400 g completos: el corte inventado no cuenta para el reparto
    assert lista["Carnicería"] == {"vacío": (460, "g")}
    assert lista["Verdulería"] == {}


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
    assert calculo.formatear(460, "g") == "460 g"
    assert calculo.formatear(1380, "g") == "1,38 kg"
    assert calculo.formatear(2000, "g") == "2,00 kg"
    assert calculo.formatear(1, "u") == "1 unidad"
    assert calculo.formatear(2, "bolsa") == "2 bolsas de 4 kg"
    texto = calculo.texto_whatsapp("Cumple", calculo.calcular_lista([persona(vaca=["vacío"])]))
    assert texto == "*Compras para Cumple*\n\n*Carnicería*\n- Vacío: 460 g\n\n*Almacén*\n- Pan: 140 g\n- Carbón: 1 bolsa de 4 kg"
