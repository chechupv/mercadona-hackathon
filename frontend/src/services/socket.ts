import { Client } from '@stomp/stompjs'
import { WS_URL } from '../config'
import type { Carrito, Evento, Ticket } from '../types/api'

export interface SuscriptoresTienda {
  onConexion: (conectado: boolean) => void
  onCarritos: (carritos: Carrito[]) => void
  onEvento: (evento: Evento) => void
  onTicket: (ticket: Ticket) => void
}

/** Se conecta al WebSocket del backend y se reconecta solo si se cae. Devuelve la función para desconectar. */
export function conectarTienda(suscriptores: SuscriptoresTienda): () => void {
  const client = new Client({
    brokerURL: WS_URL,
    reconnectDelay: 2000,
    onConnect: () => {
      client.subscribe('/topic/carritos', (mensaje) => suscriptores.onCarritos(JSON.parse(mensaje.body)))
      client.subscribe('/topic/eventos', (mensaje) => suscriptores.onEvento(JSON.parse(mensaje.body)))
      client.subscribe('/topic/tickets', (mensaje) => suscriptores.onTicket(JSON.parse(mensaje.body)))
      suscriptores.onConexion(true)
    },
    onWebSocketClose: () => suscriptores.onConexion(false),
  })

  client.activate()
  return () => void client.deactivate()
}
