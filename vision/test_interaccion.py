"""Tests de la lógica de coger/soltar con detecciones inventadas (no necesita cámara ni YOLO).

Uso:  python -m unittest test_interaccion
"""

import unittest

from detector import Persona, Producto
from interaccion import Evento, Interacciones

# Persona de 400 px de alto con la muñeca derecha en (300, 300).
# Con DISTANCIA_MUNECA = 0.15, "en la mano" es estar a menos de 60 px de la muñeca.
PERSONA_1 = Persona(1, (200, 100, 400, 500), [(300, 300)])
PERSONA_2 = Persona(2, (600, 100, 800, 500), [(700, 300)])


def botella(x: float, y: float) -> Producto:
    return Producto("bottle", (x - 15, y - 40, x + 15, y + 40), 0.8)


EN_MANO_1 = botella(310, 310)
EN_LA_MESA = botella(500, 450)
OTRA_EN_LA_MESA = botella(550, 450)

COGER = Evento(1, "bottle", "COGER")
DEVOLVER = Evento(1, "bottle", "DEVOLVER")


class InteraccionesTests(unittest.TestCase):

    def setUp(self) -> None:
        self.interacciones = Interacciones(productos=["bottle"], distancia_muneca=0.15, fotogramas_coger=8,
                                           fotogramas_soltar=15, segundos_salida=3, ventana_libres=9)
        self.t = 0.0

    def fotogramas(self, n: int, personas: list[Persona], productos: list[Producto]) -> list[Evento]:
        eventos = []
        for _ in range(n):
            self.t += 0.05
            eventos += self.interacciones.actualizar(personas, productos, self.t).eventos
        return eventos

    def sale_del_plano(self, productos_que_quedan: list[Producto]):
        """Avanza 4 s sin ver a nadie (más que segundos_salida)."""
        self.t += 4
        return self.interacciones.actualizar([], productos_que_quedan, self.t)

    # --- Coger ---

    def test_coger_necesita_varios_fotogramas_seguidos(self) -> None:
        self.assertEqual(self.fotogramas(7, [PERSONA_1], [EN_MANO_1]), [])
        self.assertEqual(self.fotogramas(1, [PERSONA_1], [EN_MANO_1]), [COGER])
        # Seguir con la botella en la mano no vuelve a sumar
        self.assertEqual(self.fotogramas(30, [PERSONA_1], [EN_MANO_1]), [])

    def test_un_fallo_suelto_de_yolo_no_reinicia_la_cuenta(self) -> None:
        eventos = self.fotogramas(5, [PERSONA_1], [EN_MANO_1])
        eventos += self.fotogramas(1, [PERSONA_1], [])  # YOLO pierde la botella un fotograma
        eventos += self.fotogramas(5, [PERSONA_1], [EN_MANO_1])
        self.assertEqual(eventos, [COGER])

    def test_una_botella_cerca_pero_no_en_la_mano_no_cuenta(self) -> None:
        cerca = botella(300, 380)  # a 80 px de la muñeca: más del 15 % de 400 px
        self.assertEqual(self.fotogramas(30, [PERSONA_1], [cerca]), [])

    def test_dos_botellas_en_las_manos_suman_dos(self) -> None:
        dos_manos = Persona(1, (200, 100, 400, 500), [(250, 300), (350, 300)])
        eventos = self.fotogramas(8, [dos_manos], [botella(250, 310), botella(350, 310)])
        self.assertEqual(eventos, [COGER] * 2)

    def test_la_botella_es_de_la_persona_con_la_muneca_mas_cerca(self) -> None:
        eventos = self.fotogramas(8, [PERSONA_1, PERSONA_2], [botella(690, 310)])
        self.assertEqual(eventos, [Evento(2, "bottle", "COGER")])

    # --- Dejarla en la mesa: resta ---

    def test_dejarla_en_la_mesa_resta(self) -> None:
        self.fotogramas(8, [PERSONA_1], [EN_MANO_1])
        self.assertEqual(self.fotogramas(14, [PERSONA_1], [EN_LA_MESA]), [])
        self.assertEqual(self.fotogramas(11, [PERSONA_1], [EN_LA_MESA]), [DEVOLVER])

    def test_dejarla_en_la_mesa_y_salir_enseguida_tambien_resta(self) -> None:
        self.fotogramas(8, [PERSONA_1], [EN_MANO_1])
        # La deja y se va antes de que dé tiempo a confirmar el DEVOLVER
        self.assertEqual(self.fotogramas(6, [PERSONA_1], [EN_LA_MESA]), [])

        resultado = self.sale_del_plano([EN_LA_MESA])
        self.assertEqual(resultado.eventos, [DEVOLVER])
        self.assertEqual(resultado.salidas, [1])

    def test_con_otras_botellas_en_la_mesa_solo_resta_si_vuelve_a_dejarla(self) -> None:
        self.fotogramas(10, [PERSONA_1], [EN_LA_MESA, OTRA_EN_LA_MESA])
        self.assertEqual(self.fotogramas(8, [PERSONA_1], [EN_MANO_1, OTRA_EN_LA_MESA]), [COGER])

        # La mano la tapa un buen rato: la otra botella sigue en la mesa, pero no es la suya
        self.assertEqual(self.fotogramas(30, [PERSONA_1], [OTRA_EN_LA_MESA]), [])

        # La vuelve a dejar: ahora hay dos sueltas otra vez
        self.assertEqual(self.fotogramas(30, [PERSONA_1], [EN_LA_MESA, OTRA_EN_LA_MESA]), [DEVOLVER])

    # --- Llevársela: no resta ---

    def test_si_la_mano_tapa_la_botella_un_rato_no_resta(self) -> None:
        self.fotogramas(8, [PERSONA_1], [EN_MANO_1])
        eventos = self.fotogramas(40, [PERSONA_1], [])  # 2 segundos sin ver la botella
        eventos += self.fotogramas(20, [PERSONA_1], [EN_MANO_1])
        self.assertEqual(eventos, [])

    def test_salir_del_plano_con_la_botella_no_resta(self) -> None:
        self.fotogramas(8, [PERSONA_1], [EN_MANO_1])
        # Se gira para irse: se le sigue viendo pero la botella ya no
        self.assertEqual(self.fotogramas(30, [PERSONA_1], []), [])

        resultado = self.sale_del_plano([])
        self.assertEqual(resultado.eventos, [])  # se la lleva: se cobra
        self.assertEqual(resultado.salidas, [1])

    def test_salir_con_una_de_dos_botellas_solo_resta_la_que_deja(self) -> None:
        dos_manos = Persona(1, (200, 100, 400, 500), [(250, 300), (350, 300)])
        self.assertEqual(self.fotogramas(8, [dos_manos], [botella(250, 310), botella(350, 310)]), [COGER] * 2)

        # Deja una en la mesa y se va con la otra
        self.fotogramas(6, [dos_manos], [EN_LA_MESA])
        resultado = self.sale_del_plano([EN_LA_MESA])
        self.assertEqual(resultado.eventos, [DEVOLVER])

    # --- Salida ---

    def test_la_salida_se_avisa_una_vez_y_olvida_a_la_persona(self) -> None:
        self.fotogramas(8, [PERSONA_1], [EN_MANO_1])

        resultado = self.interacciones.actualizar([], [], self.t + 2)
        self.assertEqual(resultado.salidas, [])
        resultado = self.interacciones.actualizar([], [], self.t + 4)
        self.assertEqual(resultado.salidas, [1])
        resultado = self.interacciones.actualizar([], [], self.t + 5)
        self.assertEqual(resultado.salidas, [])

        # Si vuelve con el mismo ID, empieza de cero y vuelve a contar el COGER
        self.t += 6
        self.assertEqual(self.fotogramas(8, [PERSONA_1], [EN_MANO_1]), [COGER])

    def test_duenos_dice_que_producto_tiene_cada_persona(self) -> None:
        resultado = self.interacciones.actualizar([PERSONA_1], [EN_LA_MESA, EN_MANO_1], 0)
        self.assertEqual(resultado.duenos, {1: 1})


if __name__ == "__main__":
    unittest.main()
