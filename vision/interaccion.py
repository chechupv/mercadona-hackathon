"""Decide cuándo una persona coge o suelta un producto (+1 / -1).

Regla clave para distinguir "lo deja en la mesa" de "se lo lleva":
  - Solo se resta si, además de no estar en la mano, aparece un producto SUELTO
    más que antes en la escena (lo ha dejado en algún sitio visible).
  - Si simplemente deja de verse (la mano lo tapa, se gira, sale del plano con él),
    sigue en el carrito y se cobra al salir.

No usa YOLO ni la cámara: recibe lo detectado en cada fotograma, así se puede
probar con datos inventados (test_interaccion.py).
"""

from collections import deque
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
    confirmado: int = 0         # unidades que ya hemos enviado al backend
    candidato: int = 0          # unidades que estamos viendo y aún no hemos confirmado
    fotogramas: int = 0         # cuántos fotogramas llevamos viendo el candidato
    libres_referencia: int = 0  # productos sueltos en la escena la última vez que todo cuadraba


@dataclass
class Interacciones:
    productos: list[str] = field(default_factory=lambda: list(config.PRODUCTOS))
    distancia_muneca: float = config.DISTANCIA_MUNECA
    fotogramas_coger: int = config.FOTOGRAMAS_COGER
    fotogramas_soltar: int = config.FOTOGRAMAS_SOLTAR
    segundos_salida: float = config.SEGUNDOS_SALIDA
    ventana_libres: int = config.VENTANA_LIBRES

    def __post_init__(self) -> None:
        self._estados: dict[tuple[int, str], _Estado] = {}
        self._ultima_vez: dict[int, float] = {}
        self._historial_libres = {clase: deque(maxlen=self.ventana_libres) for clase in self.productos}

    def actualizar(self, personas: list[Persona], productos: list[Producto], ahora: float) -> ResultadoFotograma:
        duenos = self._asignar_duenos(personas, productos)

        en_mano: dict[tuple[int, str], int] = {}
        libres = {clase: 0 for clase in self.productos}
        for indice, producto in enumerate(productos):
            if indice in duenos:
                clave = (duenos[indice], producto.clase)
                en_mano[clave] = en_mano.get(clave, 0) + 1
            elif producto.clase in libres:
                libres[producto.clase] += 1
        for clase, cantidad in libres.items():
            self._historial_libres[clase].append(cantidad)

        eventos = []
        for persona in personas:
            self._ultima_vez[persona.id] = ahora
            for clase in self.productos:
                eventos += self._actualizar_estado(persona.id, clase, en_mano.get((persona.id, clase), 0))

        salidas, eventos_salida = self._personas_que_salen(ahora)
        return ResultadoFotograma(eventos + eventos_salida, salidas, duenos)

    def personas_en_plano(self) -> list[int]:
        """Personas vistas hace poco que aún no han salido."""
        return list(self._ultima_vez)

    def _libres(self, clase: str) -> int:
        """Productos sueltos de esta clase, suavizado con la mediana de los últimos fotogramas
        para que un fotograma en que YOLO ve una botella de más o de menos no cuente."""
        historial = sorted(self._historial_libres[clase])
        return historial[len(historial) // 2] if historial else 0

    def _soltados(self, estado: _Estado, clase: str) -> int:
        """Cuántos productos han aparecido sueltos desde la última vez que todo cuadraba."""
        return max(0, self._libres(clase) - estado.libres_referencia)

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
        clave = (persona_id, clase)
        if clave not in self._estados:
            self._estados[clave] = _Estado(libres_referencia=self._libres(clase))
        estado = self._estados[clave]

        if cantidad < estado.confirmado:
            # Ya no lo vemos en la mano. Solo cuenta como soltado si ha aparecido suelto en la
            # escena; si no, sigue con la persona (tapado por la mano o saliendo del plano con él)
            cantidad = max(cantidad, estado.confirmado - self._soltados(estado, clase))

        if cantidad == estado.confirmado:
            # Todo cuadra: se actualiza la referencia de productos sueltos. El contador va
            # bajando poco a poco en vez de reiniciarse, para que un fallo suelto de YOLO
            # no eche a perder lo acumulado
            estado.libres_referencia = self._libres(clase)
            estado.fotogramas = max(0, estado.fotogramas - 1)
            return []

        if cantidad != estado.candidato:
            estado.candidato = cantidad
            estado.fotogramas = 0
        estado.fotogramas += 1

        necesarios = self.fotogramas_coger if cantidad > estado.confirmado else self.fotogramas_soltar
        if estado.fotogramas < necesarios:
            return []

        return self._confirmar(persona_id, clase, estado, cantidad)

    def _confirmar(self, persona_id: int, clase: str, estado: _Estado, cantidad: int) -> list[Evento]:
        diferencia = cantidad - estado.confirmado
        estado.confirmado = cantidad
        estado.fotogramas = 0
        estado.libres_referencia = self._libres(clase)
        accion = "COGER" if diferencia > 0 else "DEVOLVER"
        return [Evento(persona_id, clase, accion)] * abs(diferencia)

    def _personas_que_salen(self, ahora: float) -> tuple[list[int], list[Evento]]:
        salidas = [pid for pid, vista in self._ultima_vez.items() if ahora - vista > self.segundos_salida]
        eventos = []
        for persona_id in salidas:
            del self._ultima_vez[persona_id]
            for clave in [c for c in self._estados if c[0] == persona_id]:
                estado = self._estados.pop(clave)
                # Si dejó algo en la mesa justo antes de irse y no dio tiempo a confirmarlo,
                # se resta ahora: lo que sigue suelto en la escena no se lo ha llevado
                soltados = min(self._soltados(estado, clave[1]), estado.confirmado)
                if soltados > 0:
                    eventos += self._confirmar(persona_id, clave[1], estado, estado.confirmado - soltados)
        return salidas, eventos
