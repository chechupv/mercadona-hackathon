FROM python:3.12-slim
WORKDIR /app

# Librerías del sistema que necesita OpenCV
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# PyTorch solo CPU: la versión con CUDA ocupa varios GB y en Docker Desktop no se usa la GPU
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Los modelos se descargan al construir la imagen, no al subir el primer vídeo
RUN python -c "from ultralytics import YOLO; YOLO('yolo11n.pt'); YOLO('yolo11n-pose.pt')"

COPY . .

# Dentro de Docker no hay pantalla: nada de ventanas de OpenCV
ENV MOSTRAR_VENTANA=0
EXPOSE 8000
CMD ["python", "servidor.py"]
