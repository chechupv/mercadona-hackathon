"""Decide cuándo una persona coge, suelta o regala un producto.

Reglas (como en Amazon Go, paga quien coge el producto de la estantería):
  - COGER: aparece en su mano y desaparece un producto SUELTO de la escena.
  - REGALAR: aparece en su mano sin que desaparezca ninguno suelto, y a otra persona
    se le acaba de quedar la mano vacía. Quien lo recibe no paga: lo sigue pagando
    quien lo cogió de la estantería.
  - DEVOLVER: deja de estar en su mano y aparece un producto suelto más en la escena
    (lo ha dejado en la mesa). Se resta a quien lo estaba pagando.
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
    persona_id: int                 # quien paga (COGER/DEVOLVER) o quien da el producto (REGALAR)
    producto: str
    accion: str                     # "COGER", "DEVOLVER" o "REGALAR"
    receptor_id: int | None = None  # solo en REGALAR: quien lo recibe


@dataclass
class ResultadoFotograma:
    eventos: list[Evento]
    salidas: list[int]       # personas que han salido del plano
    duenos: dict[int, int]   # índice del producto en la lista -> persona que lo tiene en la mano


@dataclass
class _Estado:
    """Lo que sabemos de una persona y un tipo de producto."""
    en_mano: int = 0            # unidades que tiene en la mano (ya confirmadas)
    candidato: int = 0          # unidades que estamos viendo y aún no hemos confirmado
    fotogramas: int = 0         # cuántos fotogramas llevamos viendo el candidato
    libres_referencia: int = 0  # productos sueltos en la escena la última vez que todo cuadraba
    regalos: list[int] = field(default_factory=list)  # quién paga cada unidad que le han regalado


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

        visibles = {persona.id for persona in personas}
        eventos = []
        for persona in personas:
            self._ultima_vez[persona.id] = ahora
            for clase in self.productos:
                eventos += self._actualizar_estado(persona.id, clase, en_mano, visibles)

        salidas, eventos_salida = self._personas_que_salen(ahora)
        return ResultadoFotograma(eventos + eventos_salida, salidas, duenos)

    def personas_en_plano(self) -> list[int]:
        """Personas vistas hace poco que aún no han salido."""
        return list(self._ultima_vez)

    # --- Productos sueltos en la escena ---

    def _libres(self, clase: str) -> int:
        """Productos sueltos de esta clase, suavizado con la mediana de los últimos fotogramas
        para que un fotograma en que YOLO ve un producto de más o de menos no cuente."""
        historial = sorted(self._historial_libres[clase])
        return historial[len(historial) // 2] if historial else 0

    def _soltados(self, estado: _Estado, clase: str) -> int:
        """Cuántos productos han aparecido sueltos desde la última vez que todo cuadraba."""
        return max(0, self._libres(clase) - estado.libres_referencia)

    def _cogidos_de_la_mesa(self, estado: _Estado, clase: str) -> int:
        """Cuántos productos sueltos han desaparecido desde la última vez que todo cuadraba."""
        return max(0, estado.libres_referencia - self._libres(clase))

    # --- Quién tiene qué en la mano ---

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

    def _estado(self, persona_id: int, clase: str) -> _Estado:
        clave = (persona_id, clase)
        if clave not in self._estados:
            self._estados[clave] = _Estado(libres_referencia=self._libres(clase))
        return self._estados[clave]

    def _actualizar_estado(self, persona_id: int, clase: str, en_mano: dict[tuple[int, str], int],
                           visibles: set[int]) -> list[Evento]:
        estado = self._estado(persona_id, clase)
        cantidad = en_mano.get((persona_id, clase), 0)

        if cantidad < estado.en_mano:
            # Ya no lo vemos en la mano. Solo cuenta como soltado si ha aparecido suelto en la
            # escena; si no, sigue con la persona (tapado, saliendo del plano o dándoselo a otro)
            cantidad = max(cantidad, estado.en_mano - self._soltados(estado, clase))

        if cantidad == estado.en_mano:
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

        necesarios = self.fotogramas_coger if cantidad > estado.en_mano else self.fotogramas_soltar
        if estado.fotogramas < necesarios:
            return []

        diferencia = cantidad - estado.en_mano
        eventos = []
        if diferencia > 0:
            de_la_mesa = min(diferencia, self._cogidos_de_la_mesa(estado, clase))
            eventos += [Evento(persona_id, clase, "COGER")] * de_la_mesa
            for _ in range(diferencia - de_la_mesa):
                eventos += self._recibir(persona_id, clase, estado, en_mano, visibles)
        else:
            for _ in range(-diferencia):
                eventos += self._soltar(persona_id, clase, estado)

        estado.en_mano = cantidad
        estado.fotogramas = 0
        estado.libres_referencia = self._libres(clase)
        return eventos

    def _recibir(self, persona_id: int, clase: str, estado: _Estado,
                 en_mano: dict[tuple[int, str], int], visibles: set[int]) -> list[Evento]:
        """Le aparece un producto en la mano sin que falte ninguno en la mesa: se lo han dado."""
        donante = self._buscar_donante(persona_id, clase, en_mano, visibles)
        if donante is None:
            # No sabemos de dónde viene (p. ej. de una estantería fuera de plano): lo paga quien lo tiene
            return [Evento(persona_id, clase, "COGER")]

        estado_donante = self._estados[(donante, clase)]
        estado_donante.en_mano -= 1
        estado_donante.candidato = estado_donante.en_mano
        estado_donante.fotogramas = 0
        # Si el donante también lo había recibido de regalo, el que paga sigue siendo el original
        pagador = estado_donante.regalos.pop() if estado_donante.regalos else donante
        if pagador != persona_id:  # si vuelve a quien lo paga, deja de ser un regalo
            estado.regalos.append(pagador)
        return [Evento(donante, clase, "REGALAR", receptor_id=persona_id)]

    def _buscar_donante(self, persona_id: int, clase: str, en_mano: dict[tuple[int, str], int],
                        visibles: set[int]) -> int | None:
        """Otra persona visible a la que le falta en la mano un producto que tenía."""
        for (otra, otra_clase), estado in self._estados.items():
            if (otra != persona_id and otra_clase == clase and otra in visibles
                    and estado.en_mano > en_mano.get((otra, clase), 0)):
                return otra
        return None

    def _soltar(self, persona_id: int, clase: str, estado: _Estado) -> list[Evento]:
        """Ha dejado un producto en la mesa: se resta a quien lo estaba pagando."""
        pagador = estado.regalos.pop() if estado.regalos else persona_id
        return [Evento(pagador, clase, "DEVOLVER")]

    # --- Salida ---

    def _personas_que_salen(self, ahora: float) -> tuple[list[int], list[Evento]]:
        salidas = [pid for pid, vista in self._ultima_vez.items() if ahora - vista > self.segundos_salida]
        eventos = []
        for persona_id in salidas:
            del self._ultima_vez[persona_id]
            for clave in [c for c in self._estados if c[0] == persona_id]:
                estado = self._estados.pop(clave)
                # Si dejó algo en la mesa justo antes de irse y no dio tiempo a confirmarlo,
                # se resta ahora: lo que sigue suelto en la escena no se lo ha llevado.
                # Los regalos que se lleva los sigue pagando quien los cogió.
                for _ in range(min(self._soltados(estado, clave[1]), estado.en_mano)):
                    eventos += self._soltar(persona_id, clave[1], estado)
        return salidas, eventos
