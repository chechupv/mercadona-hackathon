"""Ajustes de la visión. Todo lo que hay que tocar para afinar la demo está aquí."""

import os

# --- Backend ---
# Se puede cambiar con la variable de entorno BACKEND_URL (en Docker es http://backend:8080)
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8080")
TIMEOUT_API = 2  # segundos

# --- Servidor (servidor.py: recibe los vídeos que se suben desde la web) ---
PUERTO_SERVIDOR = int(os.environ.get("PUERTO_SERVIDOR", "8000"))
FRONT_ORIGIN = os.environ.get("FRONT_ORIGIN", "http://localhost:5173")  # quién puede llamarle (CORS)

# --- Cámara ---
# 0 = webcam del portátil, 1 = segunda cámara, o la ruta de un vídeo: "demo.mp4"
CAMARA = 0
MOSTRAR_VENTANA = os.environ.get("MOSTRAR_VENTANA", "1") != "0"  # en Docker es 0: no hay pantalla

# --- Modelos (se descargan solos la primera vez) ---
MODELO_POSE = "yolo11n-pose.pt"   # personas + puntos del cuerpo (muñecas)
MODELO_OBJETOS = "yolo11n.pt"     # productos
TRACKER = "botsort.yaml"          # mantiene el mismo ID de persona entre fotogramas

# Clases que cuentan como producto. Cada una tiene que existir como "codigo" en
# backend/src/main/resources/data.sql, o el backend responderá "Producto desconocido".
#
# Con yolo11n.pt solo valen las clases de COCO (80 objetos genéricos). Estas son las que
# tienen sentido en un supermercado:
PRODUCTOS = [
    "bottle", "cup", "wine glass", "bowl",
    "banana", "apple", "orange", "broccoli", "carrot",
    "sandwich", "hot dog", "pizza", "donut", "cake",
    "toothbrush",
]

# Para productos que COCO no conoce (un brick de leche, una lata...), usa YOLO-World:
# detecta lo que le escribas, sin entrenar. Es más lento que yolo11n.
#   MODELO_OBJETOS = "yolov8s-worldv2.pt"
#   PRODUCTOS = ["water bottle", "milk carton", "soda can", "banana"]
# Escribe los nombres en inglés y añádelos con ese mismo texto a data.sql.

# --- Variantes: productos que YOLO ve iguales y se distinguen por su aspecto ---
# Ejemplo: YOLO llama "bottle" al agua, a la cantimplora y a la Coca-Cola. Cada una se
# distingue comparando su color con fotos de ejemplo en referencias/<codigo>/
# (créalas con crear_referencias.py). Al backend se envía el código de la variante,
# que tiene que existir en data.sql. Las botellas que no se parecen a ninguna se ignoran.
# Deja el diccionario vacío ({}) para no usar variantes.
VARIANTES = {
    "bottle": ["agua", "cantimplora", "solan", "cocacola"],
}
CARPETA_REFERENCIAS = "referencias"
# Cuánto se tiene que parecer a una foto de ejemplo (0 = idéntico, 1 = nada que ver).
# Si confunde productos, bájalo; si deja de reconocer alguno, súbelo.
DISTANCIA_MAXIMA_VARIANTE = 0.8


def codigos_de_producto() -> list[str]:
    """Lo que se envía al backend: cada clase de PRODUCTOS, o sus variantes si las tiene."""
    return [codigo for clase in PRODUCTOS for codigo in VARIANTES.get(clase, [clase])]


# --- Detección ---
CONFIANZA_PERSONA = 0.5
CONFIANZA_PRODUCTO = 0.3   # bajo a propósito: una botella en la mano se ve peor
CONFIANZA_MUNECA = 0.5
# Resolución a la que YOLO busca productos. 640 es lo normal; súbela (960, 1280) si los
# productos salen pequeños en el vídeo. Más alta = detecta mejor pero va más lento.
TAMANO_IMAGEN = 960

# --- Cuándo se considera que la persona tiene el producto en la mano ---
# Distancia máxima entre el centro del producto y la muñeca, como fracción de la
# altura de la persona (0.15 = 15 %). Así funciona igual de cerca que de lejos.
# Si no detecta que has cogido la botella, súbelo. Si suma botellas que están
# solo cerca, bájalo.
DISTANCIA_MUNECA = 0.15

# Un producto solo puede estar "en la mano" si se ha movido del sitio donde estaba suelto:
# así no se cuenta el producto de al lado cuando alguien alarga el brazo para coger otro.
# Tiene que haberse desplazado esta fracción de su propia altura (0.5 = media botella).
DESPLAZAMIENTO_COGER = 0.5
# Cuántos fotogramas se recuerda un sitio sin ver el producto (150 = 5 s a 30 fps):
# así no se olvida un producto solo porque alguien lo tape un momento.
FOTOGRAMAS_REPOSO = 150
# Lo rápido que el sitio sigue al producto (0-1). Bajo para seguir la deriva lenta de la
# cámara pero no a una botella que alguien está levantando poco a poco.
SUAVIZADO_SITIO = 0.05

# Si al cogerlo YOLO deja de ver el producto (lo gira para mirarlo, la mano lo tapa...),
# se le atribuye a la persona si, justo antes de desaparecer:
#   - se estaba moviendo: en ~10 fotogramas avanzó MOVIMIENTO_INICIO veces su altura,
#   - sin encogerse: su recuadro mide al menos ALTO_MINIMO_RELATIVO de lo normal
#     (si encoge es que alguien lo tapa a medias al pasar por delante),
#   - y había una muñeca cerca (DISTANCIA_DESAPARECER, fracción de la altura de la persona).
# Se comprueba cuando lleva FOTOGRAMAS_DESAPARECER fotogramas sin verse.
FOTOGRAMAS_DESAPARECER = 3
MOVIMIENTO_INICIO = 0.25
ALTO_MINIMO_RELATIVO = 0.75
DISTANCIA_DESAPARECER = 0.3

# Fotogramas seguidos que tiene que mantenerse el cambio para contarlo.
# Soltar pide más porque la mano tapa la botella a ratos y YOLO la pierde.
# Si suma y resta solo, súbelos.
FOTOGRAMAS_COGER = 8
FOTOGRAMAS_SOLTAR = 15

# Para restar, la botella tiene que aparecer SUELTA en la escena (en la mesa).
# Si solo deja de verse, se asume que la persona se la lleva.
# Las botellas sueltas se cuentan con la mediana de estos fotogramas, para que un
# fallo puntual de YOLO no cuente como "ha aparecido una botella".
VENTANA_LIBRES = 9

# --- Salida de la tienda ---
# Si una persona desaparece del plano durante estos segundos, se finaliza su compra
# (POST /api/tickets). Pon FINALIZAR_AL_SALIR = False para desactivarlo.
FINALIZAR_AL_SALIR = True
SEGUNDOS_SALIDA = 3
