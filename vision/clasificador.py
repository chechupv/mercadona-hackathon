"""Distingue productos que YOLO ve iguales (p. ej. cuatro "bottle") comparando su color
con fotos de ejemplo.

Las fotos están en referencias/<codigo>/*.jpg, una carpeta por producto. Para crearlas
desde un vídeo: python crear_referencias.py --help
"""

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

EXTENSIONES = {".jpg", ".jpeg", ".png"}


def caracteristicas(recorte: np.ndarray) -> np.ndarray:
    """Histograma de color (HSV) de la parte central del producto.

    Se descartan los bordes porque ahí suele salir el fondo o la mano que lo sujeta.
    """
    alto, ancho = recorte.shape[:2]
    centro = recorte[int(alto * 0.10):int(alto * 0.90), int(ancho * 0.20):int(ancho * 0.80)]
    if centro.size == 0:
        centro = recorte
    hsv = cv2.cvtColor(centro, cv2.COLOR_BGR2HSV)
    histograma = cv2.calcHist([hsv], [0, 1, 2], None, [12, 6, 6], [0, 180, 0, 256, 0, 256])
    return cv2.normalize(histograma, histograma).flatten()


@dataclass
class Referencia:
    codigo: str
    histograma: np.ndarray


class ClasificadorVisual:

    def __init__(self, carpeta: str | Path, codigos: list[str], distancia_maxima: float) -> None:
        self.distancia_maxima = distancia_maxima
        self.referencias: list[Referencia] = []
        carpeta = Path(carpeta)
        for codigo in codigos:
            fotos = [f for f in sorted((carpeta / codigo).glob("*")) if f.suffix.lower() in EXTENSIONES]
            if not fotos:
                raise FileNotFoundError(f"No hay fotos de ejemplo de '{codigo}' en {carpeta / codigo}. "
                                        f"Créalas con crear_referencias.py")
            for foto in fotos:
                imagen = cv2.imread(str(foto))
                if imagen is not None:
                    self.referencias.append(Referencia(codigo, caracteristicas(imagen)))

    def clasificar(self, recorte: np.ndarray) -> tuple[str | None, float]:
        """Devuelve el producto más parecido y su distancia (0 = idéntico, 1 = nada que ver).
        Si ninguno se parece lo suficiente, devuelve None."""
        histograma = caracteristicas(recorte)
        mejor, mejor_distancia = None, 1.0
        for referencia in self.referencias:
            distancia = cv2.compareHist(histograma, referencia.histograma, cv2.HISTCMP_BHATTACHARYYA)
            if distancia < mejor_distancia:
                mejor, mejor_distancia = referencia.codigo, distancia
        return (mejor if mejor_distancia <= self.distancia_maxima else None), mejor_distancia
