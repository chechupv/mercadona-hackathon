import { API_URL } from '../config'
import type { Carrito, Evento } from '../types/api'

async function pedir<T>(ruta: string, opciones?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${ruta}`, opciones)

  if (!response.ok) {
    throw new Error(`El backend respondió ${response.status} en ${ruta}`)
  }

  return (response.status === 204 ? undefined : response.json()) as Promise<T>
}

export function obtenerCarritos(): Promise<Carrito[]> {
  return pedir('/api/carritos')
}

export function obtenerEventos(limite: number): Promise<Evento[]> {
  return pedir(`/api/eventos?limite=${limite}`)
}

/** Vacía todos los carritos para repetir la demo. El historial se conserva en el backend. */
export function vaciarCarritos(): Promise<void> {
  return pedir('/api/carritos', { method: 'DELETE' })
}
