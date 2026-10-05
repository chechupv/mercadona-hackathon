import type { Carrito } from '../types/api'
import { formatearEuros, plural } from '../utils/formato'
import LineaProducto from './LineaProducto'

type CarritoCardProps = {
  carrito: Carrito
}

export default function CarritoCard({ carrito }: CarritoCardProps) {
  return (
    <article className="cart-block" aria-label={`Cesta de la persona ${carrito.personaId}`}>
      <header className="cart-header">
        <span className="cart-avatar" aria-hidden="true">P{carrito.personaId}</span>
        <div>
          <strong>Persona {carrito.personaId}</strong>
          <span>{plural(carrito.totalUnidades, 'unidad', 'unidades')}</span>
        </div>
        <span className="cart-total">{formatearEuros(carrito.total)}</span>
      </header>
      <ul className="product-list">
        {/* La key incluye la cantidad: al cambiar, la línea se vuelve a montar y se resalta */}
        {carrito.lineas.map((linea) => <LineaProducto key={`${linea.producto}-${linea.cantidad}`} linea={linea} />)}
      </ul>
    </article>
  )
}
