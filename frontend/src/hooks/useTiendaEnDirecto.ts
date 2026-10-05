import { useCallback, useEffect, useRef, useState } from 'react'
import { MAX_EVENTOS } from '../config'
import { obtenerCarritos, obtenerEventos, vaciarCarritos } from '../services/api'
import { conectarTienda } from '../services/socket'
import type { Carrito, Evento, Ticket } from '../types/api'

const ERROR_SIN_BACKEND = 'No se puede conectar con el backend. ¿Está arrancado en el puerto 8080?'

/** Junta eventos sin repetir, los más recientes primero */
function juntarEventos(actuales: Evento[], nuevos: Evento[]): Evento[] {
  const porId = new Map([...actuales, ...nuevos].map((evento) => [evento.id, evento]))
  return [...porId.values()].sort((a, b) => b.id - a.id).slice(0, MAX_EVENTOS)
}

export function useTiendaEnDirecto() {
  const [carritos, setCarritos] = useState<Carrito[]>([])
  const [eventos, setEventos] = useState<Evento[]>([])
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [conectado, setConectado] = useState(false)
  const [reiniciando, setReiniciando] = useState(false)
  const [error, setError] = useState('')

  // Sube cada vez que llegan carritos por el socket: así una respuesta HTTP más
  // antigua no pisa datos más nuevos
  const versionCarritos = useRef(0)

  const cargarEstado = useCallback(async () => {
    const version = versionCarritos.current
    try {
      const [carritosIniciales, eventosIniciales] = await Promise.all([obtenerCarritos(), obtenerEventos(MAX_EVENTOS)])
      if (versionCarritos.current === version) setCarritos(carritosIniciales)
      setEventos((actuales) => juntarEventos(actuales, eventosIniciales))
      setError('')
    } catch {
      setError(ERROR_SIN_BACKEND)
    }
  }, [])

  useEffect(() => {
    return conectarTienda({
      onConexion: (ok) => {
        setConectado(ok)
        // En cada (re)conexión se pide el estado por si cambió mientras estábamos desconectados
        if (ok) void cargarEstado()
        else setError(ERROR_SIN_BACKEND)
      },
      onCarritos: (nuevos) => {
        versionCarritos.current++
        setCarritos(nuevos)
      },
      onEvento: (evento) => setEventos((actuales) => juntarEventos(actuales, [evento])),
      onTicket: setTicket,
    })
  }, [cargarEstado])

  const reiniciar = useCallback(async () => {
    setReiniciando(true)
    try {
      await vaciarCarritos()
      setEventos([])
      setTicket(null)
    } catch {
      setError(ERROR_SIN_BACKEND)
    } finally {
      setReiniciando(false)
    }
  }, [])

  const cerrarTicket = useCallback(() => setTicket(null), [])

  return { carritos, eventos, ticket, conectado, reiniciando, error, reiniciar, cerrarTicket }
}
