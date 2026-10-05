"""Bucle principal: cámara -> YOLO -> interacciones -> backend.

Uso:  python main.py
Pulsa Q en la ventana para salir.
"""

import time
from collections import Counter, defaultdict

import cv2

import cliente_api
import config
from detector import Detector, Persona, Producto
from interaccion import Interacciones

VERDE = (80, 200, 80)
NARANJA = (0, 165, 255)
GRIS = (160, 160, 160)
AZUL = (255, 160, 0)


def main() -> None:
    camara = cv2.VideoCapture(config.CAMARA)
    if not camara.isOpened():
        raise SystemExit(f"No se pudo abrir la cámara {config.CAMARA!r}. Cambia CAMARA en config.py")

    print("Cargando modelos (la primera vez se descargan)...")
    detector = Detector()
    interacciones = Interacciones()
    carritos: dict[int, Counter] = defaultdict(Counter)  # solo para pintarlo en la ventana
    print("Listo. Pulsa Q en la ventana para salir.")

    try:
        while True:
            ok, frame = camara.read()
            if not ok:
                break  # fin del vídeo o cámara desconectada

            personas, productos = detector.detectar(frame)
            resultado = interacciones.actualizar(personas, productos, time.monotonic())

            for evento in resultado.eventos:
                print(f"Persona {evento.persona_id}: {evento.accion} {evento.producto}")
                carrito = carritos[evento.persona_id]
                if evento.accion == "COGER":
                    carrito[evento.producto] += 1
                elif carrito[evento.producto] > 0:
                    carrito[evento.producto] -= 1
                cliente_api.enviar_evento(evento.persona_id, evento.producto, evento.accion)

            for persona_id in resultado.salidas:
                print(f"Persona {persona_id} ha salido del plano")
                carritos.pop(persona_id, None)
                if config.FINALIZAR_AL_SALIR:
                    cliente_api.finalizar_compra(persona_id)

            if config.MOSTRAR_VENTANA:
                dibujar(frame, personas, productos, resultado.duenos, carritos)
                cv2.imshow("Mercadona - vision", frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    break
    finally:
        camara.release()
        cv2.destroyAllWindows()
        cliente_api.cerrar()


def dibujar(frame, personas: list[Persona], productos: list[Producto],
            duenos: dict[int, int], carritos: dict[int, Counter]) -> None:
    for persona in personas:
        x1, y1, x2, y2 = map(int, persona.caja)
        cv2.rectangle(frame, (x1, y1), (x2, y2), VERDE, 2)
        cv2.putText(frame, f"Persona {persona.id}", (x1, max(20, y1 - 8)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, VERDE, 2)

        # Carrito local debajo del nombre
        lineas = [f"{nombre} x{cantidad}" for nombre, cantidad in carritos[persona.id].items() if cantidad > 0]
        for i, linea in enumerate(lineas):
            cv2.putText(frame, linea, (x1 + 4, y1 + 22 + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, AZUL, 2)

        for x, y in persona.munecas:
            cv2.circle(frame, (int(x), int(y)), 6, AZUL, -1)

    for indice, producto in enumerate(productos):
        x1, y1, x2, y2 = map(int, producto.caja)
        # Naranja = en la mano de alguien; gris = suelto
        dueno = duenos.get(indice)
        color = NARANJA if dueno is not None else GRIS
        etiqueta = f"{producto.clase} {producto.confianza:.2f}" + (f" -> P{dueno}" if dueno is not None else "")
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, etiqueta, (x1, max(20, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


if __name__ == "__main__":
    main()
