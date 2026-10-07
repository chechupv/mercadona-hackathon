"""Tests de las partes de detector.py que no necesitan YOLO.

Uso:  python -m unittest test_detector
"""

import unittest

from detector import Producto, quitar_duplicados


class QuitarDuplicadosTests(unittest.TestCase):

    def test_un_recuadro_dentro_de_otro_es_el_mismo_objeto(self) -> None:
        grande = Producto("cocacola", (100, 100, 140, 200), 0.8)
        dentro = Producto("cocacola", (105, 110, 138, 190), 0.6)
        self.assertEqual(quitar_duplicados([dentro, grande]), [grande])

    def test_dos_productos_separados_se_quedan_los_dos(self) -> None:
        a = Producto("cocacola", (100, 100, 140, 200), 0.8)
        b = Producto("cocacola", (300, 100, 340, 200), 0.7)
        self.assertEqual(quitar_duplicados([a, b]), [a, b])

    def test_productos_distintos_juntos_se_quedan_los_dos(self) -> None:
        agua = Producto("agua", (100, 100, 140, 200), 0.8)
        cocacola = Producto("cocacola", (110, 110, 150, 210), 0.7)
        self.assertEqual(quitar_duplicados([agua, cocacola]), [agua, cocacola])


if __name__ == "__main__":
    unittest.main()
