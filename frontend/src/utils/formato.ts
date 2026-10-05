const euros = new Intl.NumberFormat('es-ES', { style: 'currency', currency: 'EUR' })
const hora = new Intl.DateTimeFormat('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' })

export function formatearEuros(cantidad: number): string {
  return euros.format(cantidad)
}

export function formatearHora(fechaIso: string): string {
  return hora.format(new Date(fechaIso))
}

export function plural(n: number, singular: string, pluralTexto: string): string {
  return `${n} ${n === 1 ? singular : pluralTexto}`
}
