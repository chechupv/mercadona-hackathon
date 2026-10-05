import type { LineaCarrito } from '../types/api'
import { formatearEuros } from '../utils/formato'

type LineaProductoProps = {
  linea: LineaCarrito
}

export default function LineaProducto({ linea }: LineaProductoProps) {
  return (
    <li className="product-line">
      <span>{linea.nombre}</span>
      <span className="product-meta">
        <span className="product-qty" aria-label={`Cantidad: ${linea.cantidad}`}>× {linea.cantidad}</span>
        <span>{formatearEuros(linea.subtotal)}</span>
      </span>
    </li>
  )
}
