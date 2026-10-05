"""Bucle principal: cámara o vídeo -> YOLO -> interacciones -> backend.

Uso:
  python main.py                                  webcam (CAMARA de config.py)
  python main.py videos/demo.mp4                  un vídeo grabado (puedes arrastrarlo a la terminal)
  python main.py --elegir                         abre una ventana para elegir el vídeo
  python main.py videos/demo.mp4 --guardar salida.mp4 --cobrar-al-final
Pulsa Q en la ventana para salir.
"""

import argparse
import os
import time
from collections import Counter, defaultdict

import cv2

import cliente_api
import config
from detector import Detector, Persona, Producto
from interaccion import Interacciones

VENTANA = "Mercadona - vision"
VERDE = (80, 200, 80)
NARANJA = (0, 165, 255)
GRIS = (160, 160, 160)
AZUL = (255, 160, 0)


def leer_argumentos() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Visión del carrito automático")
    parser.add_argument("fuente", nargs="?", help="vídeo a procesar, o número de webcam (por defecto, CAMARA de config.py)")
    parser.add_argument("--elegir", action="store_true", help="abre una ventana para elegir el vídeo (empieza en Descargas)")
    parser.add_argument("--guardar", metavar="SALIDA.mp4", help="guarda el vídeo con los recuadros y carritos pintados")
    parser.add_argument("--sin-ventana", action="store_true", help="no abre la ventana (va algo más rápido)")
    parser.add_argument("--cobrar-al-final", action="store_true",
                        help="al acabar el vídeo, finaliza la compra de quien siga en el plano")
    parser.add_argument("--resolucion", type=int, metavar="PX",
                        help=f"resolución a la que se buscan productos (por defecto {config.TAMANO_IMAGEN}); "
                             f"súbela a 1280 si los productos salen pequeños")
    return parser.parse_args()


def main() -> None:
    args = leer_argumentos()
    if args.resolucion:
        config.TAMANO_IMAGEN = args.resolucion

    if args.elegir:
        args.fuente = elegir_video()
    fuente = args.fuente if args.fuente is not None else config.CAMARA
    if isinstance(fuente, str) and fuente.isdigit():
        fuente = int(fuente)  # "0" desde la terminal es la webcam, no un archivo
    es_video = isinstance(fuente, str)
    if es_video and not os.path.isfile(fuente):
        raise SystemExit(f"No existe el vídeo {fuente!r}")

    camara = cv2.VideoCapture(fuente)
    if not camara.isOpened():
        raise SystemExit(f"No se pudo abrir {fuente!r}. Cambia CAMARA en config.py o pasa la ruta de un vídeo")

    fps = camara.get(cv2.CAP_PROP_FPS) or 30
    total = int(camara.get(cv2.CAP_PROP_FRAME_COUNT)) if es_video else 0
    mostrar = config.MOSTRAR_VENTANA and not args.sin_ventana
    escritor = None

    print("Cargando modelos (la primera vez se descargan)...")
    detector = Detector()
    interacciones = Interacciones()
    carritos: dict[int, Counter] = defaultdict(Counter)  # solo para pintarlo en la ventana
    if mostrar:
        cv2.namedWindow(VENTANA, cv2.WINDOW_NORMAL)  # redimensionable: los vídeos del móvil no caben en pantalla
    print("Listo. Pulsa Q en la ventana para salir." if mostrar else "Listo.")

    fotograma = 0
    try:
        while True:
            ok, frame = camara.read()
            if not ok:
                break  # fin del vídeo o cámara desconectada
            fotograma += 1

            # En un vídeo se usa el tiempo del propio vídeo, no el del reloj: así SEGUNDOS_SALIDA
            # funciona igual aunque el ordenador procese más lento o más rápido que el vídeo
            ahora = fotograma / fps if es_video else time.monotonic()

            personas, productos = detector.detectar(frame)
            resultado = interacciones.actualizar(personas, productos, ahora)

            for evento in resultado.eventos:
                carrito = carritos[evento.persona_id]
                if evento.accion == "REGALAR":
                    print(f"Persona {evento.persona_id} le da {evento.producto} a la persona {evento.receptor_id} "
                          f"(lo sigue pagando quien lo cogió)")
                else:
                    print(f"Persona {evento.persona_id}: {evento.accion} {evento.producto}")
                    if evento.accion == "COGER":
                        carrito[evento.producto] += 1
                    elif carrito[evento.producto] > 0:
                        carrito[evento.producto] -= 1
                cliente_api.enviar_evento(evento.persona_id, evento.producto, evento.accion, evento.receptor_id)

            for persona_id in resultado.salidas:
                print(f"Persona {persona_id} ha salido del plano")
                carritos.pop(persona_id, None)
                if config.FINALIZAR_AL_SALIR:
                    cliente_api.finalizar_compra(persona_id)

            if mostrar or args.guardar:
                dibujar(frame, personas, productos, resultado.duenos, carritos)

            if args.guardar:
                if escritor is None:
                    alto, ancho = frame.shape[:2]
                    escritor = cv2.VideoWriter(args.guardar, cv2.VideoWriter_fourcc(*"mp4v"), fps, (ancho, alto))
                escritor.write(frame)

            if mostrar:
                cv2.imshow(VENTANA, frame)
                if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                    break
            elif es_video and fotograma % 100 == 0:
                print(f"  {fotograma}/{total} fotogramas")

        if args.cobrar_al_final:
            for persona_id in interacciones.personas_en_plano():
                print(f"Fin del vídeo: se finaliza la compra de la persona {persona_id}")
                cliente_api.finalizar_compra(persona_id)
    finally:
        camara.release()
        if escritor is not None:
            escritor.release()
            print(f"Vídeo guardado en {args.guardar}")
        cv2.destroyAllWindows()
        cliente_api.cerrar()


def elegir_video() -> str:
    """Ventana de Windows/Mac para elegir un archivo, empezando en Descargas."""
    from tkinter import Tk, filedialog

    raiz = Tk()
    raiz.withdraw()                    # sin ventana principal, solo el diálogo
    raiz.attributes("-topmost", True)  # que salga delante de la terminal
    descargas = os.path.join(os.path.expanduser("~"), "Downloads")
    ruta = filedialog.askopenfilename(
        title="Elige el vídeo a procesar",
        initialdir=descargas if os.path.isdir(descargas) else os.path.expanduser("~"),
        filetypes=[("Vídeos", "*.mp4 *.mov *.avi *.mkv *.webm"), ("Todos los archivos", "*.*")],
    )
    raiz.destroy()
    if not ruta:
        raise SystemExit("No se ha elegido ningún vídeo")
    return ruta


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
