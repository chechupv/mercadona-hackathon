import { useRef, useState, type ChangeEvent, type DragEvent, type KeyboardEvent } from 'react'
import './AppStyles.css'
import { processVideo } from './services/api'
import type { ResultadoProcesamiento } from './types/procesamiento'
import LineaProducto from './components/LineaProducto'

function App() {
  const [video, setVideo] = useState<File | null>(null)
  const [resultado, setResultado] = useState<ResultadoProcesamiento | null>(null)
  const [error, setError] = useState('')
  const [procesando, setProcesando] = useState(false)
  const [arrastrando, setArrastrando] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  function seleccionarVideo(file?: File) {
    if (!file) return

    if (!file.type.startsWith('video/')) {
      setError('Selecciona un archivo de vídeo para continuar.')
      return
    }

    setVideo(file)
    setResultado(null)
    setError('')
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    seleccionarVideo(event.target.files?.[0])
    event.target.value = ''
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault()
    setArrastrando(false)
    seleccionarVideo(event.dataTransfer.files[0])
  }

  function handleDropZoneKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      inputRef.current?.click()
    }
  }

  async function handleProcesar() {
    if (!video) return

    setProcesando(true)
    setError('')
    setResultado(null)

    try {
      setResultado(await processVideo(video))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No se ha podido procesar el vídeo.')
    } finally {
      setProcesando(false)
    }
  }

  function limpiar() {
    setVideo(null)
    setResultado(null)
    setError('')
  }

  const unidades = resultado?.productos.reduce((total, producto) => total + producto.cantidad, 0) ?? 0

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#inicio" aria-label="Mercadona, inicio">
          <span className="brand-mark" aria-hidden="true">M</span>
          <span>Mercadona<span className="brand-dot">.</span></span>
        </a>
        <span className="topbar-label">HERRAMIENTA DE ESCANEO</span>
        <span className="status-pill"><span /> Análisis inteligente</span>
      </header>

      <main id="inicio" className="main-content">
        <section className="intro">
          <div className="eyebrow"><span /> TU COMPRA, MÁS FÁCIL</div>
          <h1>¿Qué hay en<br /><span>tu cesta?</span></h1>
          <p className="intro-copy">Sube un vídeo de tu compra y detectaremos los productos por ti. Rápido, sencillo y sin pasar por caja.</p>
        </section>

        <section className="workspace" aria-label="Analizar vídeo de compra">
          <div className="upload-card">
            <div className="card-heading">
              <div className="step-number">01</div>
              <div>
                <h2>Sube tu vídeo</h2>
                <p>Elige un vídeo claro de los productos de tu cesta.</p>
              </div>
            </div>

            <div
              className={`drop-zone${arrastrando ? ' is-dragging' : ''}${video ? ' has-file' : ''}`}
              role="button"
              tabIndex={0}
              aria-label="Seleccionar o arrastrar un vídeo"
              onClick={() => inputRef.current?.click()}
              onKeyDown={handleDropZoneKeyDown}
              onDragOver={(event) => { event.preventDefault(); setArrastrando(true) }}
              onDragLeave={() => setArrastrando(false)}
              onDrop={handleDrop}
            >
              <input ref={inputRef} className="file-input" type="file" accept="video/*" onChange={handleFileChange} />
              <div className="upload-icon" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none"><path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5M5 14v4.5A1.5 1.5 0 0 0 6.5 20h11a1.5 1.5 0 0 0 1.5-1.5V14" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>
              </div>
              {video ? (
                <>
                  <strong className="file-name">{video.name}</strong>
                  <span>{(video.size / (1024 * 1024)).toFixed(1)} MB · Pulsa para cambiar el vídeo</span>
                </>
              ) : (
                <>
                  <strong>Arrastra tu vídeo aquí</strong>
                  <span>o <span className="browse-link">explora tus archivos</span></span>
                  <small>MP4, MOV o WEBM · Máximo recomendado: 100 MB</small>
                </>
              )}
            </div>

            {error && <p className="error-message" role="alert">{error}</p>}

            <button className="process-button" type="button" onClick={handleProcesar} disabled={!video || procesando}>
              {procesando ? <><span className="spinner" /> Analizando vídeo...</> : <>Analizar mi compra <span aria-hidden="true">→</span></>}
            </button>
            <p className="privacy-note"><span aria-hidden="true">◆</span> Tu vídeo se utiliza únicamente para identificar productos.</p>
          </div>

          <aside className="info-card">
            <div className="info-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none"><path d="M4 7.5h16v12H4zM8 7.5l1.5-3h5L16 7.5M12 11v5m-2.5-2.5h5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </div>
            <span className="info-kicker">EN TRES PASOS</span>
            <h3>De la cesta<br />a tu lista</h3>
            <ol className="steps-list">
              <li><span>1</span> Graba tus productos</li>
              <li><span>2</span> Sube el vídeo aquí</li>
              <li><span>3</span> Revisa tu lista detectada</li>
            </ol>
            <div className="info-decoration" aria-hidden="true">✳</div>
          </aside>
        </section>

        {procesando && (
          <section className="result-card loading-card" aria-live="polite">
            <div className="loading-mark"><span className="spinner" /></div>
            <div><h2>Estamos revisando tu cesta</h2><p>Puede tardar unos segundos, no cierres esta página.</p></div>
          </section>
        )}

        {resultado && (
          <section className="result-card" aria-live="polite">
            <div className="result-header">
              <div>
                <div className="eyebrow result-eyebrow"><span /> ANÁLISIS COMPLETADO</div>
                <h2>Tu lista de la compra</h2>
                <p>{resultado.productos.length} {resultado.productos.length === 1 ? 'producto' : 'productos'} detectados · {unidades} {unidades === 1 ? 'unidad' : 'unidades'} en total</p>
              </div>
              <button className="text-button" type="button" onClick={limpiar}>Analizar otro vídeo</button>
            </div>
            {resultado.productos.length > 0 ? (
              <ul className="product-list">{resultado.productos.map((producto) => <LineaProducto key={producto.id} producto={producto} />)}</ul>
            ) : (
              <p className="empty-results">No se han detectado productos en este vídeo. Prueba con una toma más cercana y con buena iluminación.</p>
            )}
          </section>
        )}

        <footer className="page-footer"><span>HECHO PARA SIMPLIFICAR TU DÍA</span><span>Compra fácil, vida fácil.</span></footer>
      </main>
    </div>
  )
}

export default App
