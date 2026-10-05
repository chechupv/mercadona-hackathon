import type { ProductoSeleccionado } from '../types/procesamiento'

type LineaProductoProps = {
  producto: ProductoSeleccionado
}

export default function LineaProducto({ producto }: LineaProductoProps) {
  return (
    <li className="product-line">
      <span>{producto.nombre}</span>
      <span aria-label={`Cantidad: ${producto.cantidad}`}>× {producto.cantidad}</span>
    </li>
  )
}
