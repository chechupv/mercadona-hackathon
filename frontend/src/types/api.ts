// Mismos campos que los DTO del backend (ver README.md del repo)

export interface LineaCarrito {
  producto: string
  nombre: string
  cantidad: number
  precioUnitario: number
  subtotal: number
}

export interface Carrito {
  personaId: number
  lineas: LineaCarrito[]
  totalUnidades: number
  total: number
}

export type Accion = 'COGER' | 'DEVOLVER'

export interface Evento {
  id: number
  personaId: number
  producto: string
  nombre: string
  accion: Accion
  fecha: string
}

export interface Ticket {
  id: number
  personaId: number
  fecha: string
  lineas: LineaCarrito[]
  totalUnidades: number
  total: number
}
