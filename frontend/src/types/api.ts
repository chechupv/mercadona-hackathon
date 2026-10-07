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

export type Accion = 'COGER' | 'DEVOLVER' | 'REGALAR'

export interface Evento {
  id: number
  /** En COGER y DEVOLVER, quien paga; en REGALAR, quien da el producto */
  personaId: number
  producto: string
  nombre: string
  accion: Accion
  /** Solo en REGALAR: quien recibe el producto */
  receptorId: number | null
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
