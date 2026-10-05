# --- 1. Compilar ---
FROM node:22-alpine AS build
WORKDIR /app

# Primero solo las dependencias, para aprovechar la caché de Docker
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Vite mete esta URL en el JavaScript al compilar. Es la dirección del backend
# vista desde el navegador (tu ordenador), no desde dentro de Docker.
ARG VITE_API_URL=http://localhost:8080
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# --- 2. Servir los archivos estáticos con nginx ---
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
