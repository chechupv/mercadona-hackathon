"""Crea las fotos de ejemplo del clasificador a partir de un fotograma de un vídeo.

Detecta los productos de una clase de YOLO en ese fotograma, los ordena de izquierda a
derecha y guarda cada recorte en referencias/<nombre>/.

Ejemplo (cuatro botellas en la mesa, de izquierda a derecha):
  python crear_referencias.py video.mp4 --fotograma 0 --nombres agua cantimplora solan cocacola

Conviene repetirlo con 2 o 3 fotogramas distintos (otra luz, otra distancia) para que
el clasificador sea más fiable. Revisa referencias/vista_previa.jpg para comprobar que
cada nombre ha caído en el producto correcto.
"""

import argparse
from pathlib import Path

import cv2

import config

CARPETA = Path(__file__).parent / config.CARPETA_REFERENCIAS


def main() -> None:
    parser = argparse.ArgumentParser(description="Crea fotos de ejemplo para el clasificador visual")
    parser.add_argument("video", help="vídeo del que sacar el fotograma")
    parser.add_argument("--fotograma", type=int, default=0, help="número de fotograma (por defecto, el primero)")
    parser.add_argument("--nombres", nargs="+", required=True, help="código de cada producto, de izquierda a derecha")
    parser.add_argument("--clase", default="bottle", help="clase de YOLO que detectar (por defecto, bottle)")
    args = parser.parse_args()

    from ultralytics import YOLO  # se importa aquí para que --help vaya rápido

    camara = cv2.VideoCapture(args.video)
    camara.set(cv2.CAP_PROP_POS_FRAMES, args.fotograma)
    ok, frame = camara.read()
    if not ok:
        raise SystemExit(f"No se pudo leer el fotograma {args.fotograma} de {args.video}")

    modelo = YOLO(config.MODELO_OBJETOS)
    clase = next((i for i, nombre in modelo.names.items() if nombre == args.clase), None)
    if clase is None:
        raise SystemExit(f"{config.MODELO_OBJETOS} no conoce la clase '{args.clase}'")
    resultado = modelo.predict(frame, classes=[clase], conf=config.CONFIANZA_PRODUCTO,
                               imgsz=config.TAMANO_IMAGEN, verbose=False)[0]
    cajas = sorted((tuple(map(int, caja)) for caja in resultado.boxes.xyxy.tolist()), key=lambda c: c[0])

    if len(cajas) != len(args.nombres):
        raise SystemExit(f"Se han detectado {len(cajas)} '{args.clase}' pero has dado {len(args.nombres)} nombres. "
                         f"Prueba con otro --fotograma en el que se vean todos sin tapar.")

    vista = frame.copy()
    nombre_video = Path(args.video).stem
    for (x1, y1, x2, y2), nombre in zip(cajas, args.nombres):
        destino = CARPETA / nombre
        destino.mkdir(parents=True, exist_ok=True)
        archivo = destino / f"{nombre_video}_f{args.fotograma}.jpg"
        cv2.imwrite(str(archivo), frame[y1:y2, x1:x2])
        print(f"{nombre:>15} -> {archivo.relative_to(CARPETA.parent)}")
        cv2.rectangle(vista, (x1, y1), (x2, y2), (0, 165, 255), 2)
        cv2.putText(vista, nombre, (x1, max(15, y1 - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    cv2.imwrite(str(CARPETA / "vista_previa.jpg"), vista)
    print(f"Comprueba que cada nombre está bien puesto en {CARPETA / 'vista_previa.jpg'}")


if __name__ == "__main__":
    main()
