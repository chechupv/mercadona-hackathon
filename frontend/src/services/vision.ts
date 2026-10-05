import { VISION_URL } from '../config'

export interface EstadoVision {
  procesando: boolean
  archivo: string | null
  fotograma: number
  total: number
  error: string | null
}

/** Dirección del vídeo procesado en directo (MJPEG): se usa directamente como src de un <img> */
export const URL_DIRECTO = `${VISION_URL}/api/directo`

async function respuesta<T>(peticion: Promise<Response>): Promise<T> {
  const response = await peticion
  if (!response.ok) {
    const cuerpo = await response.json().catch(() => null)
    throw new Error(cuerpo?.detail ?? `El servicio de visión respondió ${response.status}`)
  }
  return response.json()
}

export function subirVideo(video: File, cobrarAlFinal: boolean): Promise<EstadoVision> {
  const formData = new FormData()
  formData.append('video', video)
  formData.append('cobrarAlFinal', String(cobrarAlFinal))
  return respuesta(fetch(`${VISION_URL}/api/videos`, { method: 'POST', body: formData }))
}

export function obtenerEstadoVision(): Promise<EstadoVision> {
  return respuesta(fetch(`${VISION_URL}/api/estado`))
}

export function detenerVideo(): Promise<EstadoVision> {
  return respuesta(fetch(`${VISION_URL}/api/detener`, { method: 'POST' }))
}
