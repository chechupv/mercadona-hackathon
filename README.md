# MercaFlow

Demo de carrito automático: una cámara detecta a la persona y la botella, y cada vez que la coge o la devuelve el carrito suma o resta en tiempo real.

```
Vídeo subido desde la web → vision/ (Python + YOLO) → POST /api/eventos → backend/ (Spring Boot + H2) → WebSocket → frontend/ (React)
```

## Arrancar con Docker (recomendado)

Solo necesitas Docker Desktop abierto. Desde la raíz del repo:

```bash
docker compose up --build
```

- **Front:** http://localhost:5173
- **Backend:** http://localhost:8080 (Swagger en `/swagger-ui.html`, consola H2 en `/h2-console`)
- **Visión:** http://localhost:8000 (recibe los vídeos que se suben desde la web)

La primera vez tarda bastante (unos 10 minutos) porque descarga PyTorch y los modelos de YOLO. Las siguientes es casi instantáneo. Para pararlo, `docker compose down`. Para empezar con la base de datos vacía, `docker compose down -v`.

### Analizar un vídeo

1. Abre http://localhost:5173 → **Visualización de sistema**.
2. Arrastra un vídeo a **"Sube un vídeo de la tienda"** (o pulsa para elegirlo).
3. Se analiza solo: arriba se ve el vídeo con las personas y los productos marcados, y abajo las cestas y la actividad se actualizan en directo. Con **Detener análisis** se para.

Por defecto vacía las cestas antes de empezar (el tracker vuelve a numerar desde la persona 1) y, al acabar el vídeo, cobra a quien siga en el plano. Las dos cosas se pueden desmarcar.

Si quieres usar la **webcam** en directo, eso sí tiene que ir fuera de Docker (ver [Visión](#visión)), porque Docker en Windows no puede acceder a la cámara.

## Arrancar sin Docker

| Parte | Requisitos | Comando | URL |
|---|---|---|---|
| Backend | JDK 21 | `cd backend && ./mvnw spring-boot:run` | http://localhost:8080 |
| Frontend | Node 20+ | `cd frontend && npm install && npm run dev` | http://localhost:5173 |
| Visión (subir vídeos desde la web) | Python 3.11+ | `cd vision && venv\Scripts\python servidor.py` | http://localhost:8000 |
| Visión (webcam o terminal) | Python 3.11+ | `cd vision && venv\Scripts\python main.py` (ver [Visión](#visión)) | Se abre una ventana |

Herramientas del backend:

- **Swagger** (probar la API desde el navegador): http://localhost:8080/swagger-ui.html
- **Consola H2** (ver las tablas): http://localhost:8080/h2-console. JDBC URL `jdbc:h2:file:./data/mercadona`, usuario `sa`, sin contraseña.
- **Tests**: `cd backend && ./mvnw test`

El catálogo de productos está en `backend/src/main/resources/data.sql`. El `codigo` de cada producto tiene que ser la clase que detecta YOLO (`bottle`, `cup`…).

## Visión

La primera vez, crea un entorno virtual dentro de `vision/`:

```bash
python -m venv venv
venv\Scripts\activate          # en Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
python main.py
```

Al arrancar descarga los modelos de YOLO (unos 12 MB). Se abre una ventana con:

- **Recuadro verde:** la persona, con su ID y su carrito.
- **Puntos azules:** las muñecas.
- **Recuadro naranja:** un producto en la mano de alguien (`-> P1`). Gris si está suelto.

Cómo decide el +1 y el −1 (`interaccion.py`):

- **Coger (+1):** la botella **se ha movido de su sitio en la mesa**, su centro está cerca de una muñeca durante `FOTOGRAMAS_COGER` fotogramas **y desaparece una botella suelta de la escena**. Que tenga que moverse evita contar la botella de al lado cuando alguien alarga el brazo para coger otra.
- **Regalar:** si le aparece en la mano sin que falte ninguna en la mesa y a otra persona se le acaba de quedar la mano vacía, se la han dado. Como en Amazon Go, **paga quien la cogió de la estantería**: quien la recibe no paga. Si quien la recibe la deja en la mesa, se le resta a quien la pagaba.
- **Dejarla (−1):** la botella ya no está en la mano **y aparece una botella suelta más en la escena** (la ha dejado en la mesa) durante `FOTOGRAMAS_SOLTAR` fotogramas.
- **Cogerla aunque YOLO la pierda:** si la botella empieza a moverse de su sitio y desaparece junto a una muñeca (por ejemplo, la persona la gira para mirarla), se considera que la tiene esa persona. Si solo desaparece sin moverse, o su recuadro encoge, es que alguien la tapa al pasar y no cuenta.
- **Llevársela:** si la botella simplemente deja de verse (la mano la tapa, la persona se gira o sale del plano con ella), sigue en el carrito.
- **Salir:** si la persona desaparece `SEGUNDOS_SALIDA` segundos, se finaliza su compra. Si dejó algo en la mesa justo antes de irse, se resta antes de generar el ticket.

Para que funcione, **la mesa tiene que verse en el plano**: si la botella se deja fuera de cámara, el sistema cree que se la ha llevado.

### Productos que reconoce

Con el modelo por defecto (`yolo11n.pt`) reconoce 15 productos de supermercado: `bottle`, `cup`, `wine glass`, `bowl`, `banana`, `apple`, `orange`, `broccoli`, `carrot`, `sandwich`, `hot dog`, `pizza`, `donut`, `cake` y `toothbrush`. Son clases genéricas: distingue una botella de un plátano, pero no una marca de otra.

Para productos que no están en esa lista (un brick de leche, una lata de refresco…) se puede usar **YOLO-World**, que detecta lo que le escribas sin entrenar nada. En `config.py`:

```python
MODELO_OBJETOS = "yolov8s-worldv2.pt"
PRODUCTOS = ["water bottle", "milk carton", "soda can", "banana"]
```

Escribe los nombres en inglés y añade cada uno, con el mismo texto, a `backend/src/main/resources/data.sql`. Es más lento que `yolo11n` (unos 200 ms por fotograma en CPU) y la primera vez instala una librería extra (necesita git e internet).

Para añadir o quitar productos con el modelo normal, edita `PRODUCTOS` en `config.py` y `data.sql`: los dos tienen que tener los mismos códigos.

### Distinguir productos que YOLO ve iguales (variantes)

YOLO llama `bottle` igual al agua, a una cantimplora o a una Coca-Cola. Para distinguirlas, cada botella detectada se compara por color con **fotos de ejemplo** guardadas en `vision/referencias/<codigo>/`. No hay que entrenar nada: para enseñarle un producto nuevo, basta con añadir su foto.

1. Graba un vídeo con los productos en la mesa, sin tapar.
2. Crea las fotos de ejemplo a partir de un fotograma, dando los nombres **de izquierda a derecha**:
   ```bash
   venv\Scripts\python crear_referencias.py video.mp4 --fotograma 0 --nombres agua cantimplora solan cocacola
   ```
   Abre `referencias/vista_previa.jpg` para comprobar que cada nombre ha caído en su producto. Conviene repetirlo con 2 o 3 fotogramas distintos (más cerca, más lejos) para que sea más fiable.
3. Pon los mismos códigos en `VARIANTES` de `config.py`:
   ```python
   VARIANTES = {"bottle": ["agua", "cantimplora", "solan", "cocacola"]}
   ```
4. Añade cada código con su nombre y precio a `data.sql`.

Si confunde productos, baja `DISTANCIA_MAXIMA_VARIANTE`; si deja de reconocer alguno cuando está en la mano, súbelo. Para no usar variantes, deja `VARIANTES = {}`.

**Si grabáis en otro sitio o con otra luz** (exterior, fondo blanco, cámara mucho más lejos), el mismo producto puede verse con colores muy distintos y el clasificador lo ignora. Solución: añadid una foto de ejemplo de esa escena con `crear_referencias.py` (un fotograma en que se vea el producto en la mesa). Las fotos nuevas se suman a las que ya hay.

Todo se ajusta en `config.py`:

| Problema | Qué tocar |
|---|---|
| No detecta que has cogido la botella | Sube `DISTANCIA_MUNECA` o baja `CONFIANZA_PRODUCTO` |
| Suma una botella que solo está cerca | Baja `DISTANCIA_MUNECA` |
| Suma y resta solo | Sube `FOTOGRAMAS_COGER` y `FOTOGRAMAS_SOLTAR` |
Para probar la lógica sin cámara: `python -m unittest test_interaccion test_detector`.

### Con vídeos grabados

```bash
python main.py --elegir                                          # abre una ventana para elegir el vídeo (empieza en Descargas)
python main.py videos/demo.mp4                                   # procesa el vídeo y lo muestra en la ventana
python main.py videos/demo.mp4 --guardar salida.mp4              # además guarda el vídeo con los recuadros pintados
python main.py videos/demo.mp4 --cobrar-al-final                 # al acabar, genera el ticket de quien siga en el plano
python main.py videos/demo.mp4 --sin-ventana --guardar salida.mp4  # sin ventana, algo más rápido
python main.py videos/demo.mp4 --resolucion 1280                 # si los productos salen pequeños (cámara lejos)
```

- El vídeo puede estar en cualquier carpeta. En vez de escribir la ruta, arrastra el archivo a la terminal y se pega solo.
- Pulsa **Reiniciar demo** en el front antes de cada vídeo: el tracker vuelve a empezar por la persona 1 y se sumaría al carrito anterior.
- En un vídeo se usa el tiempo del propio vídeo, así que da igual que el ordenador procese más lento o más rápido.
- Los vídeos (`*.mp4`, `*.mov`…) están en el `.gitignore`: no se suben a GitHub.

## API

### Visión → Backend

`POST /api/eventos`: la persona coge o devuelve un producto.

```json
{ "personaId": 1, "producto": "bottle", "accion": "COGER" }
```

- `accion` puede ser `COGER`, `DEVOLVER` o `REGALAR`.
- Devuelve el carrito actualizado de esa persona.
- Un `DEVOLVER` de más se ignora: la cantidad nunca baja de 0.
- `REGALAR` registra que una persona le da el producto a otra. No cambia ningún carrito, porque lo sigue pagando quien lo cogió. `personaId` es quien lo da y `receptorId` (obligatorio) quien lo recibe:

```json
{ "personaId": 1, "producto": "bottle", "accion": "REGALAR", "receptorId": 2 }
```

`POST /api/tickets`: finaliza la compra (por ejemplo, cuando la persona sale del plano).

```json
{ "personaId": 1 }
```

- Devuelve `201` con el ticket, y el carrito de esa persona se vacía.
- Si el carrito está vacío, devuelve `409`.

### Front → Backend

| Método | Ruta | Para qué |
|---|---|---|
| `GET` | `/api/carritos` | Todos los carritos (estado inicial al abrir la página) |
| `GET` | `/api/carritos/{personaId}` | Un carrito (`404` si está vacío) |
| `DELETE` | `/api/carritos` | Vaciar todos los carritos entre tomas del vídeo |
| `GET` | `/api/productos` | Catálogo, ordenado por nombre |
| `GET` | `/api/eventos?limite=20` | Historial, los más recientes primero (`limite` de 1 a 200) |
| `GET` | `/api/tickets?limite=20` | Últimos tickets |
| `GET` | `/api/tickets/{id}` | Un ticket |

### Backend → Front (WebSocket)

STOMP en `ws://localhost:8080/ws`. Los mensajes se envían solo cuando el cambio ya se ha guardado en la base de datos.

| Topic | Cuándo | Contenido |
|---|---|---|
| `/topic/carritos` | Cualquier cambio en los carritos | Lista completa de carritos (sustituye el estado del front) |
| `/topic/eventos` | Cada COGER, DEVOLVER o REGALAR | El evento, para mostrar "Persona 1 ha cogido Agua" o "Persona 1 le ha dado Agua a Persona 2" |
| `/topic/tickets` | Cada compra finalizada | El ticket |

### Formatos

Carrito:

```json
{
  "personaId": 1,
  "lineas": [
    { "producto": "bottle", "nombre": "Agua Solán de cabras 1,5 L", "cantidad": 2, "precioUnitario": 0.45, "subtotal": 0.90 }
  ],
  "totalUnidades": 2,
  "total": 0.90
}
```

Evento:

```json
{ "id": 7, "personaId": 1, "producto": "bottle", "nombre": "Agua Solán de cabras 1,5 L", "accion": "COGER", "receptorId": null, "fecha": "2026-10-05T10:15:30Z" }
```

Ticket: los mismos campos que el carrito, más `id` y `fecha`.

Errores (formato ProblemDetail):

```json
{ "status": 400, "title": "Bad Request", "detail": "Producto desconocido: banana" }
{ "status": 400, "detail": "Invalid request content.", "errores": ["personaId: must not be null"] }
{ "status": 409, "detail": "La persona 1 no tiene productos en el carrito" }
```

## Cómo escalaría a una tienda real

Esta demo usa una sola cámara y la persona no sale del plano. En una tienda real se usarían varias cámaras: cada una detecta personas con YOLO, la homografía de OpenCV pasa su posición a coordenadas del plano de la tienda, y OSNet o DINOv2 generan una huella visual (ropa y silueta, sin datos biométricos) para mantener el mismo ID y el mismo carrito al pasar de una cámara a otra.
