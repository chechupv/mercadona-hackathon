"""YOLO: detecta personas (con ID y muñecas) y productos en cada fotograma."""

from dataclasses import dataclass
from pathlib import Path

import config

# Índices de los puntos del cuerpo en YOLO-pose (formato COCO)
MUNECA_IZQUIERDA = 9
MUNECA_DERECHA = 10

Caja = tuple[float, float, float, float]  # x1, y1, x2, y2 en píxeles
Punto = tuple[float, float]


@dataclass
class Persona:
    id: int
    caja: Caja
    munecas: list[Punto]  # solo las que se ven bien (0, 1 o 2)

    @property
    def altura(self) -> float:
        return self.caja[3] - self.caja[1]


@dataclass
class Producto:
    clase: str
    caja: Caja
    confianza: float

    @property
    def centro(self) -> Punto:
        x1, y1, x2, y2 = self.caja
        return (x1 + x2) / 2, (y1 + y2) / 2


def quitar_duplicados(productos: list[Producto], solape_maximo: float = 0.5) -> list[Producto]:
    """YOLO a veces detecta el mismo objeto dos veces (un recuadro dentro de otro).
    Si dos productos de la misma clase se solapan más de solape_maximo (respecto al más
    pequeño), se queda el de más confianza."""
    def solape(a: Caja, b: Caja) -> float:
        ancho = min(a[2], b[2]) - max(a[0], b[0])
        alto = min(a[3], b[3]) - max(a[1], b[1])
        if ancho <= 0 or alto <= 0:
            return 0.0
        area_menor = min((a[2] - a[0]) * (a[3] - a[1]), (b[2] - b[0]) * (b[3] - b[1]))
        return ancho * alto / area_menor if area_menor > 0 else 0.0

    elegidos: list[Producto] = []
    for producto in sorted(productos, key=lambda p: p.confianza, reverse=True):
        if all(p.clase != producto.clase or solape(p.caja, producto.caja) <= solape_maximo for p in elegidos):
            elegidos.append(producto)
    return elegidos


class Detector:

    def __init__(self) -> None:
        # Se importan aquí para que interaccion.py y sus tests no necesiten ultralytics ni OpenCV
        from ultralytics import YOLO

        from clasificador import ClasificadorVisual

        self.modelo_pose = YOLO(config.MODELO_POSE)
        self.modelo_objetos = YOLO(config.MODELO_OBJETOS)

        # YOLO-World no tiene clases fijas: detecta los textos que le pasemos
        if "world" in config.MODELO_OBJETOS.lower():
            self.modelo_objetos.set_classes(config.PRODUCTOS)

        nombres = self.modelo_objetos.names  # {id: "bottle", ...}
        desconocidos = set(config.PRODUCTOS) - set(nombres.values())
        if desconocidos:
            raise ValueError(f"{config.MODELO_OBJETOS} no conoce estas clases: {sorted(desconocidos)}")
        self.clases_productos = [i for i, nombre in nombres.items() if nombre in config.PRODUCTOS]

        # Un clasificador por cada clase con variantes (p. ej. "bottle" -> agua, cantimplora...)
        self.clasificadores = {
            clase: ClasificadorVisual(Path(__file__).parent / config.CARPETA_REFERENCIAS, codigos,
                                      config.DISTANCIA_MAXIMA_VARIANTE)
            for clase, codigos in config.VARIANTES.items() if clase in config.PRODUCTOS
        }

    def detectar(self, frame) -> tuple[list[Persona], list[Producto]]:
        return self._personas(frame), self._productos(frame)

    def _personas(self, frame) -> list[Persona]:
        # persist=True: el tracker recuerda los fotogramas anteriores y mantiene los IDs
        resultado = self.modelo_pose.track(frame, persist=True, tracker=config.TRACKER,
                                           conf=config.CONFIANZA_PERSONA, verbose=False)[0]
        if resultado.boxes is None or resultado.boxes.id is None or resultado.keypoints is None:
            return []

        ids = resultado.boxes.id.int().tolist()
        cajas = resultado.boxes.xyxy.tolist()
        puntos = resultado.keypoints.xy.tolist()
        confianzas = resultado.keypoints.conf.tolist() if resultado.keypoints.conf is not None else None

        personas = []
        for i, (persona_id, caja) in enumerate(zip(ids, cajas)):
            munecas = []
            for indice in (MUNECA_IZQUIERDA, MUNECA_DERECHA):
                x, y = puntos[i][indice]
                visible = confianzas is None or confianzas[i][indice] >= config.CONFIANZA_MUNECA
                if visible and (x > 0 or y > 0):  # YOLO pone (0, 0) cuando no ve el punto
                    munecas.append((x, y))
            personas.append(Persona(persona_id, tuple(caja), munecas))
        return personas

    def _productos(self, frame) -> list[Producto]:
        resultado = self.modelo_objetos.predict(frame, classes=self.clases_productos, conf=config.CONFIANZA_PRODUCTO,
                                                imgsz=config.TAMANO_IMAGEN, verbose=False)[0]
        productos = []
        for caja, clase, confianza in zip(resultado.boxes.xyxy.tolist(), resultado.boxes.cls.tolist(),
                                          resultado.boxes.conf.tolist()):
            nombre = resultado.names[int(clase)]
            clasificador = self.clasificadores.get(nombre)
            if clasificador is not None:
                x1, y1, x2, y2 = map(int, caja)
                recorte = frame[max(0, y1):y2, max(0, x1):x2]
                if recorte.size == 0:
                    continue
                nombre, _ = clasificador.clasificar(recorte)
                if nombre is None:
                    continue  # no se parece a ningún producto conocido: se ignora
            productos.append(Producto(nombre, tuple(caja), float(confianza)))
        return quitar_duplicados(productos)
