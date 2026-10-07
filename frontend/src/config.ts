/** Dirección del backend. Se puede cambiar con VITE_API_URL en un archivo .env */
export const API_URL: string = import.meta.env.VITE_API_URL ?? 'http://localhost:8080'

/** WebSocket STOMP del backend: http://... -> ws://.../ws */
export const WS_URL = `${API_URL.replace(/^http/, 'ws')}/ws`

/** Servidor de la visión (vision/servidor.py), que procesa los vídeos que se suben. VITE_VISION_URL en .env */
export const VISION_URL: string = import.meta.env.VITE_VISION_URL ?? 'http://localhost:8000'

/** Cuántos eventos se muestran en la actividad en directo */
export const MAX_EVENTOS = 8
