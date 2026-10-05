import type { ReactNode } from 'react'
import type { Evento } from '../types/api'
import { formatearHora } from '../utils/formato'

type ListaActividadProps = {
  eventos: Evento[]
}

const ESTILO = {
  COGER: { clase: 'is-add', etiqueta: '+1' },
  DEVOLVER: { clase: 'is-remove', etiqueta: '−1' },
  REGALAR: { clase: 'is-gift', etiqueta: '→' },
} as const

function describir(evento: Evento): ReactNode {
  switch (evento.accion) {
    case 'COGER':
      return <><strong>Persona {evento.personaId}</strong> ha cogido {evento.nombre}</>
    case 'DEVOLVER':
      return <><strong>Persona {evento.personaId}</strong> ha devuelto {evento.nombre}</>
    case 'REGALAR':
      return <><strong>Persona {evento.personaId}</strong> le ha dado {evento.nombre} a <strong>Persona {evento.receptorId}</strong> · lo paga quien lo cogió</>
  }
}

export default function ListaActividad({ eventos }: ListaActividadProps) {
  return (
    <ul className="activity-list" aria-live="polite">
      {eventos.map((evento) => {
        const estilo = ESTILO[evento.accion]
        return (
          <li key={evento.id} className="activity-item">
            <span className={`activity-badge ${estilo.clase}`} aria-hidden="true">{estilo.etiqueta}</span>
            <div>
              {describir(evento)}
              <time dateTime={evento.fecha}>{formatearHora(evento.fecha)}</time>
            </div>
          </li>
        )
      })}
    </ul>
  )
}
