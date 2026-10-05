import type { ResultadoProcesamiento } from '../types/procesamiento'

const videoProcessingUrl = import.meta.env.VITE_VIDEO_PROCESSING_URL ?? '/api/videos/process'

export async function processVideo(video: File): Promise<ResultadoProcesamiento> {
  const formData = new FormData()
  formData.append('video', video)

  const response = await fetch(videoProcessingUrl, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    throw new Error(`No se pudo procesar el vídeo (${response.status})`)
  }

  return response.json() as Promise<ResultadoProcesamiento>
}
