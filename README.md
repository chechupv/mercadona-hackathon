# Mercadona Just Walk Out

Demo de carrito automático: una cámara detecta a la persona y la botella, y cada vez que la coge o la devuelve el carrito suma o resta en tiempo real.

```
Cámara → vision/ (Python + YOLO) → POST /api/eventos → backend/ (Spring Boot + H2) → WebSocket → frontend/ (React)
```

## Arrancar con Docker (recomendado)

Solo necesitas Docker Desktop abierto. Desde la raíz del repo:

```bash
docker compose up --build
```

- **Front:** http://localhost:5173
- **Backend:** http://localhost:8080 (Swagger en `/swagger-ui.html`, consola H2 en `/h2-console`)

La primera vez tarda unos minutos porque descarga las imágenes y las dependencias. Las siguientes es casi instantáneo. Para pararlo, `docker compose down`. Para empezar con la base de datos vacía, `docker compose down -v`.

La visión se arranca aparte, en tu ordenador (ver [Visión](#visión)), porque Docker en Windows no puede usar la webcam ni abrir ventanas. Envía los eventos a `localhost:8080` igual que sin Docker.

## Arrancar sin Docker

| Parte | Requisitos | Comando | URL |
|---|---|---|---|
| Backend | JDK 21 | `cd backend && ./mvnw spring-boot:run` | http://localhost:8080 |
| Frontend | Node 20+ | `cd frontend && npm install && npm run dev` | http://localhost:5173 |
| Visión | Python 3.11+ y webcam | `cd vision && python main.py` (ver [Visión](#visión)) | Se abre una ventana |

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

- **Coger (+1):** el centro de la botella está cerca de una muñeca durante `FOTOGRAMAS_COGER` fotogramas.
- **Dejarla (−1):** la botella ya no está en la mano **y aparece una botella suelta más en la escena** (la ha dejado en la mesa) durante `FOTOGRAMAS_SOLTAR` fotogramas.
- **Llevársela:** si la botella simplemente deja de verse (la mano la tapa, la persona se gira o sale del plano con ella), sigue en el carrito.
- **Salir:** si la persona desaparece `SEGUNDOS_SALIDA` segundos, se finaliza su compra. Si dejó algo en la mesa justo antes de irse, se resta antes de generar el ticket.

Para que funcione, **la mesa tiene que verse en el plano**: si la botella se deja fuera de cámara, el sistema cree que se la ha llevado.

Todo se ajusta en `config.py`:

| Problema | Qué tocar |
|---|---|
| No detecta que has cogido la botella | Sube `DISTANCIA_MUNECA` o baja `CONFIANZA_PRODUCTO` |
| Suma una botella que solo está cerca | Baja `DISTANCIA_MUNECA` |
| Suma y resta solo | Sube `FOTOGRAMAS_COGER` y `FOTOGRAMAS_SOLTAR` |
Para probar la lógica sin cámara: `python -m unittest test_interaccion`.

### Con vídeos grabados

```bash
python main.py --elegir                                          # abre una ventana para elegir el vídeo (empieza en Descargas)
python main.py videos/demo.mp4                                   # procesa el vídeo y lo muestra en la ventana
python main.py videos/demo.mp4 --guardar salida.mp4              # además guarda el vídeo con los recuadros pintados
python main.py videos/demo.mp4 --cobrar-al-final                 # al acabar, genera el ticket de quien siga en el plano
python main.py videos/demo.mp4 --sin-ventana --guardar salida.mp4  # sin ventana, algo más rápido
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

- `accion` puede ser `COGER` o `DEVOLVER`.
- Devuelve el carrito actualizado de esa persona.
- Un `DEVOLVER` de más se ignora: la cantidad nunca baja de 0.

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
| `/topic/eventos` | Cada COGER o DEVOLVER | El evento, para mostrar "Persona 1 ha cogido Agua" |
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
{ "id": 7, "personaId": 1, "producto": "bottle", "nombre": "Agua Solán de cabras 1,5 L", "accion": "COGER", "fecha": "2026-10-05T10:15:30Z" }
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
