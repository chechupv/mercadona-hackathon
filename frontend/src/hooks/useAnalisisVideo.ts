import { useCallback, useEffect, useState } from 'react'
import { vaciarCarritos } from '../services/api'
import { detenerVideo, obtenerEstadoVision, subirVideo, type EstadoVision } from '../services/vision'

const ERROR_SIN_VISION = 'No se puede conectar con el servicio de visión. ¿Está arrancado en el puerto 8000?'

/** Sube vídeos al servicio de visión y sigue su progreso. */
export function useAnalisisVideo() {
  const [estado, setEstado] = useState<EstadoVision | null>(null)
  const [disponible, setDisponible] = useState(true)
  const [subiendo, setSubiendo] = useState(false)
  const [error, setError] = useState('')
  const [haEmpezado, setHaEmpezado] = useState(false)  // para no enseñar el vídeo de una sesión anterior

  // Mientras se procesa se pregunta cada segundo; si no, cada 5 s (para saber si el servicio está arrancado)
  const procesando = estado?.procesando ?? false
  useEffect(() => {
    let cancelado = false
    const consultar = async () => {
      try {
        const nuevo = await obtenerEstadoVision()
        if (!cancelado) {
          setEstado(nuevo)
          setDisponible(true)
        }
      } catch {
        if (!cancelado) setDisponible(false)
      }
    }
    const primera = setTimeout(() => void consultar(), 0)
    const intervalo = setInterval(() => void consultar(), procesando ? 1000 : 5000)
    return () => {
      cancelado = true
      clearTimeout(primera)
      clearInterval(intervalo)
    }
  }, [procesando])

  const analizar = useCallback(async (video: File, vaciarAntes: boolean, cobrarAlFinal: boolean) => {
    setSubiendo(true)
    setError('')
    try {
      // El tracker vuelve a empezar por la persona 1: sin vaciar, se sumaría a las cestas anteriores
      if (vaciarAntes) await vaciarCarritos()
      setEstado(await subirVideo(video, cobrarAlFinal))
      setHaEmpezado(true)
    } catch (err) {
      setError(err instanceof TypeError ? ERROR_SIN_VISION : err instanceof Error ? err.message : ERROR_SIN_VISION)
    } finally {
      setSubiendo(false)
    }
  }, [])

  const detener = useCallback(async () => {
    try {
      setEstado(await detenerVideo())
    } catch {
      setError(ERROR_SIN_VISION)
    }
  }, [])

  return { estado, disponible, subiendo, error: error || estado?.error || '', haEmpezado, analizar, detener }
}
