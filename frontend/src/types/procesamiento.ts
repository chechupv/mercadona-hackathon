export interface ProductoSeleccionado {
  id: number | string
  nombre: string
  cantidad: number
}

export interface ResultadoProcesamiento {
  productos: ProductoSeleccionado[]
}
