"""Decide cuándo una persona coge o suelta un producto (+1 / -1).

No usa YOLO ni la cámara: recibe lo detectado en cada fotograma, así se puede
probar con datos inventados (test_interaccion.py).
"""

from dataclasses import dataclass, field
from math import dist, inf

import config
from detector import Persona, Producto


@dataclass(frozen=True)
class Evento:
    persona_id: int
    producto: str
    accion: str  # "COGER" o "DEVOLVER"


@dataclass
class ResultadoFotograma:
    eventos: list[Evento]
    salidas: list[int]       # personas que han salido del plano
    duenos: dict[int, int]   # índice del producto en la lista -> persona que lo tiene en la mano


@dataclass
class _Estado:
    """Lo que sabemos de una persona y un tipo de producto."""
    confirmado: int = 0  # unidades que ya hemos enviado al backend
    candidato: int = 0   # unidades que estamos viendo y aún no hemos confirmado
    fotogramas: int = 0  # cuántos fotogramas llevamos viendo el candidato


@dataclass
class Interacciones:
    productos: list[str] = field(default_factory=lambda: list(config.PRODUCTOS))
    distancia_muneca: float = config.DISTANCIA_MUNECA
    fotogramas_coger: int = config.FOTOGRAMAS_COGER
    fotogramas_soltar: int = config.FOTOGRAMAS_SOLTAR
    segundos_salida: float = config.SEGUNDOS_SALIDA

    def __post_init__(self) -> None:
        self._estados: dict[tuple[int, str], _Estado] = {}
        self._ultima_vez: dict[int, float] = {}

    def actualizar(self, personas: list[Persona], productos: list[Producto], ahora: float) -> ResultadoFotograma:
        duenos = self._asignar_duenos(personas, productos)

        en_mano: dict[tuple[int, str], int] = {}
        for indice, persona_id in duenos.items():
            clave = (persona_id, productos[indice].clase)
            en_mano[clave] = en_mano.get(clave, 0) + 1

        eventos = []
        for persona in personas:
            self._ultima_vez[persona.id] = ahora
            for clase in self.productos:
                eventos += self._actualizar_estado(persona.id, clase, en_mano.get((persona.id, clase), 0))

        return ResultadoFotograma(eventos, self._personas_que_salen(ahora), duenos)

    def _asignar_duenos(self, personas: list[Persona], productos: list[Producto]) -> dict[int, int]:
        """Asigna cada producto a la muñeca más cercana, si está lo bastante cerca."""
        duenos: dict[int, int] = {}
        for indice, producto in enumerate(productos):
            dueno, mejor_distancia = None, inf
            for persona in personas:
                limite = self.distancia_muneca * persona.altura
                for muneca in persona.munecas:
                    distancia = dist(producto.centro, muneca)
                    if distancia <= limite and distancia < mejor_distancia:
                        dueno, mejor_distancia = persona.id, distancia
            if dueno is not None:
                duenos[indice] = dueno
        return duenos

    def _actualizar_estado(self, persona_id: int, clase: str, cantidad: int) -> list[Evento]:
        estado = self._estados.setdefault((persona_id, clase), _Estado())

        if cantidad == estado.confirmado:
            # Va bajando poco a poco en vez de reiniciarse: un fotograma suelto en que
            # YOLO pierde la botella no echa a perder todo lo acumulado
            estado.fotogramas = max(0, estado.fotogramas - 1)
            return []

        if cantidad != estado.candidato:
            estado.candidato = cantidad
            estado.fotogramas = 0
        estado.fotogramas += 1

        necesarios = self.fotogramas_coger if cantidad > estado.confirmado else self.fotogramas_soltar
        if estado.fotogramas < necesarios:
            return []

        diferencia = cantidad - estado.confirmado
        estado.confirmado = cantidad
        estado.fotogramas = 0
        accion = "COGER" if diferencia > 0 else "DEVOLVER"
        return [Evento(persona_id, clase, accion)] * abs(diferencia)

    def _personas_que_salen(self, ahora: float) -> list[int]:
        salidas = [pid for pid, vista in self._ultima_vez.items() if ahora - vista > self.segundos_salida]
        for persona_id in salidas:
            del self._ultima_vez[persona_id]
            for clave in [c for c in self._estados if c[0] == persona_id]:
                del self._estados[clave]
        return salidas
