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

# Clases de YOLO que cuentan como producto. Tienen que existir en data.sql del backend.
PRODUCTOS = ["bottle", "cup"]

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

# --- Salida de la tienda ---
# Si una persona desaparece del plano durante estos segundos, se finaliza su compra
# (POST /api/tickets). Pon FINALIZAR_AL_SALIR = False para desactivarlo.
FINALIZAR_AL_SALIR = True
SEGUNDOS_SALIDA = 3
