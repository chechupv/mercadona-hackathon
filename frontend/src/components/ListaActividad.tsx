import type { Evento } from '../types/api'
import { formatearHora } from '../utils/formato'

type ListaActividadProps = {
  eventos: Evento[]
}

export default function ListaActividad({ eventos }: ListaActividadProps) {
  return (
    <ul className="activity-list" aria-live="polite">
      {eventos.map((evento) => {
        const coge = evento.accion === 'COGER'
        return (
          <li key={evento.id} className="activity-item">
            <span className={`activity-badge ${coge ? 'is-add' : 'is-remove'}`} aria-hidden="true">{coge ? '+1' : '−1'}</span>
            <div>
              <strong>Persona {evento.personaId}</strong> {coge ? 'ha cogido' : 'ha devuelto'} {evento.nombre}
              <time dateTime={evento.fecha}>{formatearHora(evento.fecha)}</time>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
