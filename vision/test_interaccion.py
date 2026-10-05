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


PERSONA_3 = Persona(3, (1000, 100, 1200, 500), [(1100, 300)])

EN_MANO_1 = botella(310, 310)
EN_MANO_2 = botella(710, 310)
EN_MANO_3 = botella(1110, 310)
EN_LA_MESA = botella(500, 450)
OTRA_EN_LA_MESA = botella(550, 450)

COGER = Evento(1, "bottle", "COGER")
DEVOLVER = Evento(1, "bottle", "DEVOLVER")


def regalo(de: int, a: int) -> Evento:
    return Evento(de, "bottle", "REGALAR", receptor_id=a)


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

    def test_un_producto_que_sigue_en_su_sitio_no_esta_en_la_mano(self) -> None:
        # La botella está en la mesa; llega alguien y deja la muñeca justo al lado
        # (p. ej. al alargar el brazo para coger la de al lado)
        al_lado = botella(320, 320)
        self.fotogramas(10, [], [al_lado])
        self.assertEqual(self.fotogramas(40, [PERSONA_1], [al_lado]), [])

    def test_levantarlo_poco_a_poco_si_cuenta(self) -> None:
        # Está en la mesa, llega alguien, pone la mano al lado y la levanta despacio (3 px por fotograma)
        self.fotogramas(10, [], [botella(320, 330)])
        self.assertEqual(self.fotogramas(10, [PERSONA_1], [botella(320, 330)]), [])
        eventos = []
        for paso in range(1, 40):
            mano = Persona(1, (200, 100, 400, 500), [(310, 320 - 3 * paso)])
            eventos += self.fotogramas(1, [mano], [botella(320, 330 - 3 * paso)])
        self.assertEqual(eventos, [COGER])

    def test_si_yolo_la_pierde_al_cogerla_cuenta_igual_y_al_dejarla_resta(self) -> None:
        en_su_sitio = botella(400, 330)
        mano_al_lado = Persona(1, (200, 100, 400, 500), [(380, 320)])
        self.fotogramas(10, [], [en_su_sitio])
        self.fotogramas(10, [mano_al_lado], [en_su_sitio])
        # Empieza a levantarla (se mueve 4 px por fotograma, aún cerca de su sitio)...
        for paso in range(1, 7):
            self.fotogramas(1, [mano_al_lado], [botella(400 - 4 * paso, 330 - 2 * paso)])
        # ...y YOLO deja de verla porque la gira para mirarla
        eventos = self.fotogramas(40, [mano_al_lado], [])
        self.assertEqual(eventos, [COGER])

        # La vuelve a dejar en su sitio y aparta la mano
        mano_lejos = Persona(1, (200, 100, 400, 500), [(250, 250)])
        self.assertEqual(self.fotogramas(30, [mano_lejos], [en_su_sitio]), [DEVOLVER])

    def test_si_yolo_la_pierde_al_cogerla_y_luego_la_regala_no_vuelve_a_sumar(self) -> None:
        # Como en botellaIntercambioDevolucion2.mp4: la 1 la coge (YOLO la pierde un momento),
        # se la da a la 2 y la 2 la deja en la mesa. Solo debe haber COGER, REGALAR y DEVOLVER.
        en_su_sitio = botella(400, 330)
        mano_1 = Persona(1, (200, 100, 400, 500), [(380, 320)])
        dos = [mano_1, PERSONA_2]
        eventos = self.fotogramas(10, [PERSONA_2], [en_su_sitio])
        eventos += self.fotogramas(10, dos, [en_su_sitio])
        for paso in range(1, 7):
            eventos += self.fotogramas(1, dos, [botella(400 - 4 * paso, 330 - 2 * paso)])
        eventos += self.fotogramas(20, dos, [])               # la 1 la tiene, pero YOLO no la ve
        eventos += self.fotogramas(30, dos, [EN_MANO_2])      # se la da a la 2
        eventos += self.fotogramas(30, dos, [en_su_sitio])    # la 2 la deja en la mesa
        eventos += self.fotogramas(80, [PERSONA_2], [en_su_sitio])  # la 1 se va
        self.assertEqual(eventos, [COGER, regalo(1, 2), DEVOLVER])

    def test_levantarla_muy_despacio_y_que_yolo_la_pierda_tambien_cuenta(self) -> None:
        # Como en botellaIntercambioDevolucion.mp4: la sube menos de 1 px por fotograma y luego deja de verse
        en_su_sitio = botella(400, 330)
        mano_al_lado = Persona(1, (200, 100, 400, 500), [(380, 320)])
        self.fotogramas(10, [], [en_su_sitio])
        eventos = self.fotogramas(10, [mano_al_lado], [en_su_sitio])
        for paso in range(1, 41):
            eventos += self.fotogramas(1, [mano_al_lado], [botella(400, 330 - 0.8 * paso)])
        eventos += self.fotogramas(40, [mano_al_lado], [])
        self.assertEqual(eventos, [COGER])

    def test_si_se_mueve_la_camara_y_la_tapan_no_cuenta(self) -> None:
        # Como la cantimplora de dosPersonasDiferentesObjetos.mp4: la cámara se desplaza poco a poco
        # (todas las botellas de la mesa se mueven igual en la imagen) y alguien tapa una un momento
        mano_al_lado = Persona(1, (200, 100, 400, 500), [(380, 320)])
        eventos = self.fotogramas(10, [], [botella(400, 330), botella(550, 330)])
        for paso in range(1, 61):  # 0.8 px por fotograma: en 40 fotogramas, 32 px
            eventos += self.fotogramas(1, [mano_al_lado], [botella(400 - 0.8 * paso, 330), botella(550 - 0.8 * paso, 330)])
        eventos += self.fotogramas(40, [mano_al_lado], [botella(502, 330)])  # la de la izquierda queda tapada
        self.assertEqual(eventos, [])

    def test_si_la_tapan_a_medias_al_pasar_por_delante_no_cuenta(self) -> None:
        en_su_sitio = botella(400, 330)  # 80 px de alto
        mano_al_lado = Persona(1, (200, 100, 400, 500), [(380, 320)])
        self.fotogramas(10, [], [en_su_sitio])
        self.fotogramas(10, [mano_al_lado], [en_su_sitio])
        # El cuerpo tapa la mitad de abajo: el recuadro encoge y su centro sube (parece que se mueve)
        for _ in range(6):
            self.fotogramas(1, [mano_al_lado], [Producto("bottle", (385, 290, 415, 320), 0.5)])
        eventos = self.fotogramas(40, [mano_al_lado], [])
        eventos += self.fotogramas(20, [mano_al_lado], [en_su_sitio])
        self.assertEqual(eventos, [])

    def test_si_solo_la_tapan_sin_moverla_no_cuenta(self) -> None:
        en_su_sitio = botella(400, 330)
        mano_al_lado = Persona(1, (200, 100, 400, 500), [(380, 320)])
        self.fotogramas(10, [], [en_su_sitio])
        self.fotogramas(10, [mano_al_lado], [en_su_sitio])
        eventos = self.fotogramas(40, [mano_al_lado], [])  # el cuerpo la tapa
        eventos += self.fotogramas(20, [mano_al_lado], [en_su_sitio])
        self.assertEqual(eventos, [])

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

    # --- Regalos (paga quien lo coge de la estantería, como en Amazon Go) ---

    def coger_de_la_mesa_y_darselo_a_la_2(self) -> list[Evento]:
        dos = [PERSONA_1, PERSONA_2]
        eventos = self.fotogramas(10, dos, [EN_LA_MESA])
        eventos += self.fotogramas(8, dos, [EN_MANO_1])   # la 1 la coge de la mesa
        eventos += self.fotogramas(8, dos, [EN_MANO_2])   # se la da a la 2
        return eventos

    def test_darle_el_producto_a_otra_persona_es_un_regalo(self) -> None:
        # La 1 paga (COGER); la 2 lo recibe sin pagar (REGALAR, sin COGER para la 2)
        self.assertEqual(self.coger_de_la_mesa_y_darselo_a_la_2(), [COGER, regalo(1, 2)])

    def test_si_quien_lo_recibe_se_lo_lleva_lo_sigue_pagando_quien_lo_cogio(self) -> None:
        self.coger_de_la_mesa_y_darselo_a_la_2()
        eventos = self.fotogramas(20, [PERSONA_1, PERSONA_2], [EN_MANO_2])
        eventos += self.fotogramas(80, [PERSONA_1], [])  # la 2 sale del plano con el regalo
        self.assertEqual(eventos, [])  # ningún DEVOLVER: la 1 lo sigue pagando

    def test_si_quien_lo_recibe_lo_deja_en_la_mesa_se_resta_a_quien_lo_pagaba(self) -> None:
        self.coger_de_la_mesa_y_darselo_a_la_2()
        eventos = self.fotogramas(30, [PERSONA_1, PERSONA_2], [EN_LA_MESA])
        self.assertEqual(eventos, [DEVOLVER])  # se resta a la persona 1, no a la 2

    def test_si_se_lo_devuelve_ya_no_es_un_regalo(self) -> None:
        dos = [PERSONA_1, PERSONA_2]
        self.coger_de_la_mesa_y_darselo_a_la_2()
        self.assertEqual(self.fotogramas(8, dos, [EN_MANO_1]), [regalo(2, 1)])
        # Ahora la tiene quien la paga: si la deja en la mesa, se le resta a ella
        self.assertEqual(self.fotogramas(30, dos, [EN_LA_MESA]), [DEVOLVER])

    def test_un_regalo_de_un_regalo_lo_sigue_pagando_el_primero(self) -> None:
        tres = [PERSONA_1, PERSONA_2, PERSONA_3]
        eventos = self.fotogramas(10, tres, [EN_LA_MESA])
        eventos += self.fotogramas(8, tres, [EN_MANO_1])
        eventos += self.fotogramas(8, tres, [EN_MANO_2])
        eventos += self.fotogramas(8, tres, [EN_MANO_3])
        eventos += self.fotogramas(30, tres, [EN_LA_MESA])  # la 3 la deja en la mesa
        self.assertEqual(eventos, [COGER, regalo(1, 2), regalo(2, 3), DEVOLVER])

    def test_cada_uno_paga_lo_que_coge_de_la_mesa(self) -> None:
        dos = [PERSONA_1, PERSONA_2]
        eventos = self.fotogramas(10, dos, [EN_LA_MESA, OTRA_EN_LA_MESA])
        eventos += self.fotogramas(10, dos, [EN_MANO_1, EN_MANO_2])  # cada una coge una
        self.assertEqual(sorted(eventos, key=lambda e: e.persona_id), [COGER, Evento(2, "bottle", "COGER")])

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
