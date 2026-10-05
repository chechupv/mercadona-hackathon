import { useRef, useState, type ChangeEvent, type DragEvent, type KeyboardEvent } from 'react'
import { useAnalisisVideo } from '../hooks/useAnalisisVideo'
import { URL_DIRECTO } from '../services/vision'

/** Sube un vídeo grabado y lo analiza: las cestas de abajo se van llenando mientras se procesa. */
export default function AnalizarVideoCard() {
  const { estado, disponible, subiendo, error, haEmpezado, analizar, detener } = useAnalisisVideo()
  const [arrastrando, setArrastrando] = useState(false)
  const [vaciarAntes, setVaciarAntes] = useState(true)
  const [cobrarAlFinal, setCobrarAlFinal] = useState(true)
  const inputRef = useRef<HTMLInputElement>(null)

  const procesando = estado?.procesando ?? false
  const ocupado = procesando || subiendo
  const progreso = estado && estado.total > 0 ? Math.round((estado.fotograma / estado.total) * 100) : 0

  function elegir(file?: File) {
    if (!file || ocupado) return
    void analizar(file, vaciarAntes, cobrarAlFinal)
  }

  function handleChange(event: ChangeEvent<HTMLInputElement>) {
    elegir(event.target.files?.[0])
    event.target.value = ''
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setArrastrando(false)
    elegir(event.dataTransfer.files[0])
  }

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      inputRef.current?.click()
    }
  }

  return (
    <section className="result-card video-card" aria-label="Analizar un vídeo">
      <div className="result-header">
        <div>
          <div className="eyebrow result-eyebrow"><span /> ANÁLISIS DE VÍDEO</div>
          <h2>Sube un vídeo de la tienda</h2>
          <p>Se analiza solo y las cestas se van llenando mientras se procesa.</p>
        </div>
        <span className={`state-badge${!disponible ? ' is-paused' : procesando ? ' is-progress' : ' is-active'}`}>
          {!disponible ? 'Visión apagada' : procesando ? 'Analizando' : 'Lista'}
        </span>
      </div>

      {haEmpezado && (
        <div className="video-preview">
          <img src={URL_DIRECTO} alt="Vídeo analizado en directo, con las personas y los productos marcados" />
          {procesando && <span className="video-live"><span /> ANALIZANDO</span>}
        </div>
      )}

      {procesando ? (
        <div className="video-progress" aria-live="polite">
          <div className="video-progress-text">
            <strong>{estado?.archivo}</strong>
            <span>{estado?.total ? `${progreso} % · fotograma ${estado.fotograma} de ${estado.total}` : 'Cargando modelos...'}</span>
          </div>
          <div className="progress-track" role="progressbar" aria-valuenow={progreso} aria-valuemin={0} aria-valuemax={100}>
            <div className="progress-fill" style={{ width: `${progreso}%` }} />
          </div>
          <button className="text-button" type="button" onClick={() => void detener()}>Detener análisis</button>
        </div>
      ) : (
        <>
          <div
            className={`drop-zone video-drop${arrastrando ? ' is-dragging' : ''}`}
            role="button"
            tabIndex={0}
            aria-label="Seleccionar o arrastrar un vídeo"
            aria-disabled={ocupado || !disponible}
            onClick={() => !ocupado && inputRef.current?.click()}
            onKeyDown={handleKeyDown}
            onDragOver={(event) => { event.preventDefault(); setArrastrando(true) }}
            onDragLeave={() => setArrastrando(false)}
            onDrop={handleDrop}
          >
            <input ref={inputRef} className="file-input" type="file" accept="video/*" onChange={handleChange} />
            <div className="upload-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 14v4.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </div>
            {subiendo ? (
              <><strong>Subiendo vídeo...</strong><span>Empezará a analizarse en cuanto termine</span></>
            ) : (
              <>
                <strong>{haEmpezado ? 'Arrastra otro vídeo' : 'Arrastra tu vídeo aquí'}</strong>
                <span>o <span className="browse-link">explora tus archivos</span></span>
                <small>MP4, MOV o WEBM · la mesa con los productos tiene que verse en el plano</small>
              </>
            )}
          </div>
          <div className="video-options">
            <label><input type="checkbox" checked={vaciarAntes} onChange={(e) => setVaciarAntes(e.target.checked)} /> Vaciar las cestas antes de empezar</label>
            <label><input type="checkbox" checked={cobrarAlFinal} onChange={(e) => setCobrarAlFinal(e.target.checked)} /> Cobrar al acabar el vídeo a quien siga en el plano</label>
          </div>
        </>
      )}

      {error && <p className="error-message" role="alert">{error}</p>}
    </section>
  )
}
