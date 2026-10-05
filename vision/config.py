"""Ajustes de la visión. Todo lo que hay que tocar para afinar la demo está aquí."""

# --- Backend ---
BACKEND_URL = "http://localhost:8080"
TIMEOUT_API = 2  # segundos

# --- Cámara ---
# 0 = webcam del portátil, 1 = segunda cámara, o la ruta de un vídeo: "demo.mp4"
CAMARA = 0
MOSTRAR_VENTANA = True

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

# --- Detección ---
CONFIANZA_PERSONA = 0.5
CONFIANZA_PRODUCTO = 0.3   # bajo a propósito: una botella en la mano se ve peor
CONFIANZA_MUNECA = 0.5

# --- Cuándo se considera que la persona tiene el producto en la mano ---
# Distancia máxima entre el centro del producto y la muñeca, como fracción de la
# altura de la persona (0.15 = 15 %). Así funciona igual de cerca que de lejos.
# Si no detecta que has cogido la botella, súbelo. Si suma botellas que están
# solo cerca, bájalo.
DISTANCIA_MUNECA = 0.15

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
