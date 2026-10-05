"""Envía los eventos al backend sin congelar la cámara."""

from concurrent.futures import ThreadPoolExecutor

import requests

import config

# Un solo hilo en segundo plano: el bucle de la cámara no espera a la respuesta
# y los eventos llegan al backend en el mismo orden en que ocurren.
_executor = ThreadPoolExecutor(max_workers=1)


def enviar_evento(persona_id: int, producto: str, accion: str, receptor_id: int | None = None) -> None:
    """accion: "COGER", "DEVOLVER" o "REGALAR" (en REGALAR hay que indicar receptor_id)."""
    # int() porque el ID del tracker puede ser un tipo de numpy que requests no sabe convertir
    cuerpo = {"personaId": int(persona_id), "producto": producto, "accion": accion}
    if receptor_id is not None:
        cuerpo["receptorId"] = int(receptor_id)
    _executor.submit(_post, "/api/eventos", cuerpo)


def finalizar_compra(persona_id: int) -> None:
    _executor.submit(_post, "/api/tickets", {"personaId": int(persona_id)})


def cerrar() -> None:
    """Espera a que se envíen los eventos pendientes antes de salir."""
    _executor.shutdown(wait=True)


def _post(ruta: str, cuerpo: dict) -> None:
    try:
        respuesta = requests.post(f"{config.BACKEND_URL}{ruta}", json=cuerpo, timeout=config.TIMEOUT_API)
    except requests.RequestException as error:
        print(f"[api] No se pudo conectar con el backend ({ruta}): {error}")
        return

    if respuesta.ok:
        print(f"[api] {ruta} {cuerpo} -> {respuesta.status_code}")
        return

    try:
        detalle = respuesta.json().get("detail", respuesta.text)
    except ValueError:
        detalle = respuesta.text
    print(f"[api] {ruta} {cuerpo} -> {respuesta.status_code}: {detalle}")
