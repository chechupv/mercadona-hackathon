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
from statistics import median

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
    ocultos: int = 0            # unidades que tiene en la mano aunque YOLO no las vea (ver _detectar_desapariciones)


@dataclass
class _Sitio:
    """Un sitio donde ha estado un producto suelto (p. ej. su hueco en la mesa)."""
    punto: tuple[float, float]          # posición suavizada del sitio
    ultimo_fotograma: int
    llevado_por: int | None = None      # persona a la que se le ha atribuido al desaparecer
    # Últimas veces que se vio suelto aquí: (fotograma, centro, altura)
    vistas: deque = field(default_factory=lambda: deque(maxlen=60))

    def ver(self, fotograma: int, centro: tuple[float, float], alto: float) -> None:
        self.ultimo_fotograma = fotograma
        self.vistas.append((fotograma, centro, alto))

    def vista_cerca(self, fotograma: int, margen: int) -> tuple[int, tuple[float, float]] | None:
        """La vez que se vio más cerca de ese fotograma (a como mucho `margen` fotogramas)."""
        cercanas = [(abs(f - fotograma), f, c) for f, c, _ in self.vistas if abs(f - fotograma) <= margen]
        if not cercanas:
            return None
        _, f, c = min(cercanas)
        return f, c


@dataclass
class Interacciones:
    productos: list[str] = field(default_factory=config.codigos_de_producto)
    distancia_muneca: float = config.DISTANCIA_MUNECA
    fotogramas_coger: int = config.FOTOGRAMAS_COGER
    fotogramas_soltar: int = config.FOTOGRAMAS_SOLTAR
    segundos_salida: float = config.SEGUNDOS_SALIDA
    ventana_libres: int = config.VENTANA_LIBRES
    desplazamiento_coger: float = config.DESPLAZAMIENTO_COGER
    fotogramas_reposo: int = config.FOTOGRAMAS_REPOSO
    suavizado_sitio: float = config.SUAVIZADO_SITIO
    fotogramas_desaparecer: int = config.FOTOGRAMAS_DESAPARECER
    movimiento_inicio: float = config.MOVIMIENTO_INICIO
    alto_minimo_relativo: float = config.ALTO_MINIMO_RELATIVO
    distancia_desaparecer: float = config.DISTANCIA_DESAPARECER

    def __post_init__(self) -> None:
        self._estados: dict[tuple[int, str], _Estado] = {}
        self._ultima_vez: dict[int, float] = {}
        self._historial_libres = {clase: deque(maxlen=self.ventana_libres) for clase in self.productos}
        # Sitios donde han estado los productos sueltos (sus huecos en la mesa)
        self._sitios: dict[str, list[_Sitio]] = {clase: [] for clase in self.productos}
        self._fotograma = 0

    def actualizar(self, personas: list[Persona], productos: list[Producto], ahora: float) -> ResultadoFotograma:
        duenos = self._asignar_duenos(personas, productos)
        self._recordar_reposo(productos, duenos)
        self._detectar_desapariciones(personas)

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

    def _sitio_cercano(self, producto: Producto) -> _Sitio | None:
        alto = producto.caja[3] - producto.caja[1]
        sitios = [s for s in self._sitios.get(producto.clase, [])
                  if dist(producto.centro, s.punto) < self.desplazamiento_coger * alto]
        return min(sitios, key=lambda s: dist(producto.centro, s.punto), default=None)

    def _en_reposo(self, producto: Producto) -> bool:
        """Sigue en el sitio donde estaba suelto: no se ha movido, así que no está en ninguna
        mano aunque haya una muñeca cerca (p. ej. al alargar el brazo para coger el de al lado)."""
        return self._sitio_cercano(producto) is not None

    def _recordar_reposo(self, productos: list[Producto], duenos: dict[int, int]) -> None:
        self._fotograma += 1
        for indice, producto in enumerate(productos):
            if indice in duenos or producto.clase not in self._sitios:
                continue
            alto = producto.caja[3] - producto.caja[1]
            sitio = self._sitio_cercano(producto)
            if sitio is None:
                sitio = _Sitio(producto.centro, self._fotograma)
                self._sitios[producto.clase].append(sitio)
            else:
                # El sitio se acerca muy despacio a donde se ve el producto: así sigue la deriva lenta
                # de la cámara, pero no a una botella que alguien está levantando poco a poco
                (x, y), (nx, ny), a = sitio.punto, producto.centro, self.suavizado_sitio
                sitio.punto = (x + (nx - x) * a, y + (ny - y) * a)
                sitio.llevado_por = None  # se ve suelto en su sitio: nadie lo lleva
            sitio.ver(self._fotograma, producto.centro, alto)
        # Se olvidan los sitios que llevan mucho sin verse (el producto se fue o la cámara se movió)
        for clase, sitios in self._sitios.items():
            self._sitios[clase] = [s for s in sitios if self._fotograma - s.ultimo_fotograma <= self.fotogramas_reposo]

    def _empezaba_a_moverse(self, sitio: _Sitio) -> bool:
        """Justo antes de desaparecer se estaba moviendo sin encogerse.

        "Moverse" es haber avanzado respecto a ~10 fotogramas antes, o respecto a ~40 antes
        (así también se detecta a quien lo levanta muy despacio). Siempre se descuenta lo que
        se ha movido la cámara, medido con los demás productos sueltos: si todos se desplazan
        igual es la cámara, no una mano. Si el recuadro encoge, lo tapaban a medias."""
        fotograma, centro, alto = sitio.vistas[-1]
        altos = sorted(a for f, _, a in sitio.vistas if f < fotograma - 3)
        if not altos:
            return False
        alto_normal = altos[len(altos) // 2]
        if alto < self.alto_minimo_relativo * alto_normal:
            return False
        for atras, margen in ((10, 2), (40, 10)):
            antes = sitio.vista_cerca(fotograma - atras, margen)
            if antes is None:
                continue
            fotograma_antes, centro_antes = antes
            dx, dy = self._movimiento_camara(sitio, fotograma_antes, fotograma)
            movido = dist((centro[0] - dx, centro[1] - dy), centro_antes)
            if movido >= self.movimiento_inicio * alto_normal:
                return True
        return False

    def _movimiento_camara(self, excepto: _Sitio, desde: int, hasta: int) -> tuple[float, float]:
        """Cuánto se han desplazado en la imagen los demás productos sueltos entre dos fotogramas
        (la mediana). Como esos productos no los toca nadie, ese desplazamiento es la cámara."""
        dxs, dys = [], []
        for sitios in self._sitios.values():
            for otro in sitios:
                if otro is excepto:
                    continue
                inicio, fin = otro.vista_cerca(desde, 3), otro.vista_cerca(hasta, 3)
                if inicio and fin:
                    dxs.append(fin[1][0] - inicio[1][0])
                    dys.append(fin[1][1] - inicio[1][1])
        if not dxs:
            return 0.0, 0.0  # no hay otros productos con los que comparar: se asume cámara quieta
        return median(dxs), median(dys)

    def _detectar_desapariciones(self, personas: list[Persona]) -> None:
        """Un producto que empieza a moverse de su sitio y desaparece junto a una muñeca lo
        tiene esa persona en la mano, aunque YOLO ya no lo vea (p. ej. lo gira para mirarlo
        o la mano lo tapa). Si solo desaparece sin haberse movido, es que alguien lo tapa."""
        for clase, sitios in self._sitios.items():
            for sitio in sitios:
                if sitio.llevado_por is not None or self._fotograma - sitio.ultimo_fotograma != self.fotogramas_desaparecer:
                    continue
                if not self._empezaba_a_moverse(sitio):
                    continue  # no se estaba moviendo, o encogía: solo lo han tapado
                ultimo_centro = sitio.vistas[-1][1]
                cercanas = [(dist(ultimo_centro, muneca), persona) for persona in personas
                            for muneca in persona.munecas
                            if dist(ultimo_centro, muneca) <= self.distancia_desaparecer * persona.altura]
                if cercanas:
                    persona = min(cercanas, key=lambda c: c[0])[1]
                    sitio.llevado_por = persona.id
                    self._estado(persona.id, clase).ocultos += 1

    def _asignar_duenos(self, personas: list[Persona], productos: list[Producto]) -> dict[int, int]:
        """Asigna cada producto que se ha movido a la muñeca más cercana, si está lo bastante cerca."""
        duenos: dict[int, int] = {}
        for indice, producto in enumerate(productos):
            if self._en_reposo(producto):
                continue
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

        if estado.ocultos and self._soltados(estado, clase):
            # El producto que llevaba sin que YOLO lo viera ha vuelto a aparecer suelto
            estado.ocultos = max(0, estado.ocultos - self._soltados(estado, clase))
        cantidad = max(en_mano.get((persona_id, clase), 0), estado.ocultos)

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
        estado.ocultos = min(estado.ocultos, estado.en_mano)
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
        # Lo que regala ya no lo puede seguir teniendo "oculto" en la mano
        estado_donante.ocultos = min(estado_donante.ocultos, estado_donante.en_mano)
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
