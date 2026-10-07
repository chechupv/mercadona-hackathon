"""Servidor de la visión: recibe vídeos subidos desde la web y los procesa.

Uso:  python servidor.py          (en Docker arranca solo con docker compose up)

  POST /api/videos    sube un vídeo (multipart: "video" y "cobrarAlFinal") y empieza a procesarlo
  GET  /api/estado    si está procesando, por qué fotograma va y si ha habido algún error
  POST /api/detener   para el vídeo que se está procesando
  GET  /api/directo   el vídeo procesado en directo, con los recuadros pintados (MJPEG: <img src=...>)

Los eventos (COGER, DEVOLVER...) se envían al backend igual que con main.py.
"""

import asyncio
import os
import shutil
import tempfile
import threading
from dataclasses import dataclass, field

import cv2
import numpy as np
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import config
import main

ANCHO_DIRECTO = 960  # el vídeo en directo se reduce a este ancho para que vaya fluido en la web


@dataclass
class _Estado:
    procesando: bool = False
    archivo: str | None = None
    fotograma: int = 0
    total: int = 0
    error: str | None = None
    jpeg: bytes | None = None  # último fotograma pintado
    version: int = 0           # sube con cada fotograma nuevo
    detener: threading.Event = field(default_factory=threading.Event)
    candado: threading.Lock = field(default_factory=threading.Lock)

    def resumen(self) -> dict:
        with self.candado:
            return {"procesando": self.procesando, "archivo": self.archivo, "fotograma": self.fotograma,
                    "total": self.total, "error": self.error}


estado = _Estado()
app = FastAPI(title="Mercadona - visión")
app.add_middleware(CORSMiddleware, allow_origins=[config.FRONT_ORIGIN], allow_methods=["*"], allow_headers=["*"])


@app.post("/api/videos", status_code=202)
def subir_video(video: UploadFile = File(...), cobrar_al_final: bool = Form(True, alias="cobrarAlFinal")) -> dict:
    with estado.candado:
        if estado.procesando:
            raise HTTPException(409, "Ya se está procesando un vídeo. Espera a que acabe o detenlo.")
        estado.procesando = True

    # Se guarda en un archivo temporal porque OpenCV necesita leerlo desde disco
    sufijo = os.path.splitext(video.filename or "")[1] or ".mp4"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=sufijo) as temporal:
            shutil.copyfileobj(video.file, temporal)
    except Exception:
        with estado.candado:
            estado.procesando = False
        raise

    with estado.candado:
        estado.archivo = video.filename
        estado.fotograma, estado.total, estado.error = 0, 0, None
        estado.detener.clear()
    threading.Thread(target=_procesar, args=(temporal.name, cobrar_al_final), daemon=True).start()
    return estado.resumen()


@app.get("/api/estado")
def obtener_estado() -> dict:
    return estado.resumen()


@app.post("/api/detener")
def detener() -> dict:
    estado.detener.set()
    return estado.resumen()


@app.get("/api/directo")
async def directo() -> StreamingResponse:
    """Emite cada fotograma nuevo como JPEG (MJPEG): el navegador lo muestra como un vídeo en un <img>."""
    async def fotogramas():
        ultima = -1
        while True:
            with estado.candado:
                version, jpeg = estado.version, estado.jpeg
            if jpeg is not None and version != ultima:
                ultima = version
                yield (b"--fotograma\r\nContent-Type: image/jpeg\r\nContent-Length: "
                       + str(len(jpeg)).encode() + b"\r\n\r\n" + jpeg + b"\r\n")
            await asyncio.sleep(0.03)

    return StreamingResponse(fotogramas(), media_type="multipart/x-mixed-replace; boundary=fotograma")


def _procesar(ruta: str, cobrar_al_final: bool) -> None:
    try:
        main.procesar(ruta, cobrar_al_final=cobrar_al_final, al_fotograma=_publicar, detener=estado.detener)
    except ValueError:
        with estado.candado:
            estado.error = "No se ha podido leer el archivo. ¿Es un vídeo (MP4, MOV, WEBM...)?"
    except Exception as error:  # cualquier otro fallo se enseña en la web en lugar de tumbar el servidor
        with estado.candado:
            estado.error = str(error)
    finally:
        with estado.candado:
            estado.procesando = False
        os.remove(ruta)


def _publicar(frame: np.ndarray, fotograma: int, total: int) -> None:
    alto, ancho = frame.shape[:2]
    if ancho > ANCHO_DIRECTO:
        frame = cv2.resize(frame, (ANCHO_DIRECTO, int(alto * ANCHO_DIRECTO / ancho)))
    ok, jpeg = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    with estado.candado:
        estado.fotograma, estado.total = fotograma, total
        if ok:
            estado.jpeg = jpeg.tobytes()
            estado.version += 1


if __name__ == "__main__":
    print(f"Servidor de visión en http://localhost:{config.PUERTO_SERVIDOR} (backend: {config.BACKEND_URL})")
    uvicorn.run(app, host="0.0.0.0", port=config.PUERTO_SERVIDOR)
