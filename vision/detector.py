"""YOLO: detecta personas (con ID y muñecas) y productos en cada fotograma."""

from dataclasses import dataclass

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


class Detector:

    def __init__(self) -> None:
        # Se importa aquí para que interaccion.py y sus tests no necesiten ultralytics
        from ultralytics import YOLO

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
        resultado = self.modelo_objetos.predict(frame, classes=self.clases_productos,
                                                conf=config.CONFIANZA_PRODUCTO, verbose=False)[0]
        return [
            Producto(resultado.names[int(clase)], tuple(caja), float(confianza))
            for caja, clase, confianza in zip(resultado.boxes.xyxy.tolist(),
                                              resultado.boxes.cls.tolist(),
                                              resultado.boxes.conf.tolist())
        ]
