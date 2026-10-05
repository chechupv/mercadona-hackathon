import { useEffect, useRef } from 'react'
import type { Ticket } from '../types/api'
import { formatearEuros, formatearHora, plural } from '../utils/formato'
import LineaProducto from './LineaProducto'

type TicketCardProps = {
  ticket: Ticket
  onCerrar: () => void
}

export default function TicketCard({ ticket, onCerrar }: TicketCardProps) {
  const ref = useRef<HTMLElement>(null)

  // Cuando llega un ticket nuevo, se baja hasta él para que se vea en el vídeo
  useEffect(() => {
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [ticket.id])

  return (
    <section ref={ref} className="result-card ticket-card" aria-live="polite">
      <div className="result-header">
        <div>
          <div className="eyebrow result-eyebrow"><span /> COMPRA FINALIZADA · {formatearHora(ticket.fecha)}</div>
          <h2>Ticket de la persona {ticket.personaId}</h2>
          <p>{plural(ticket.lineas.length, 'producto', 'productos')} · {plural(ticket.totalUnidades, 'unidad', 'unidades')} · Ticket n.º {ticket.id}</p>
        </div>
        <button className="text-button" type="button" onClick={onCerrar}>Cerrar</button>
      </div>
      <ul className="product-list">
        {ticket.lineas.map((linea) => <LineaProducto key={linea.producto} linea={linea} />)}
      </ul>
      <div className="ticket-total">
        <span>Total cobrado</span>
        <strong>{formatearEuros(ticket.total)}</strong>
      </div>
    </section>
  )
}
