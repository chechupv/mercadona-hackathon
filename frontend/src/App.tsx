import './AppStyles.css'
import { useState } from 'react'
import AnalizarVideoCard from './components/AnalizarVideoCard'
import CarritoCard from './components/CarritoCard'
import ListaActividad from './components/ListaActividad'
import TicketCard from './components/TicketCard'
import { useTiendaEnDirecto } from './hooks/useTiendaEnDirecto'
import { plural } from './utils/formato'

type Seccion = 'menu' | 'compras' | 'camaras' | 'incidencias'

const camarasIniciales = [
  { id: 'CAM-01', nombre: 'Entrada principal', ubicacion: 'Acceso norte', activa: true },
  { id: 'CAM-02', nombre: 'Pasillo de bebidas', ubicacion: 'Zona de frescos', activa: true },
  { id: 'CAM-03', nombre: 'Almacén', ubicacion: 'Zona de carga', activa: false },
]

const incidenciasIniciales = [
  { id: 'INC-024', titulo: 'Cámara sin señal', zona: 'Almacén · CAM-03', prioridad: 'Alta', estado: 'Abierta' },
  { id: 'INC-023', titulo: 'Lector de caja no responde', zona: 'Caja 2', prioridad: 'Media', estado: 'En curso' },
  { id: 'INC-022', titulo: 'Reposición pendiente', zona: 'Pasillo de bebidas', prioridad: 'Baja', estado: 'Resuelta' },
]

function App() {
  const { carritos, eventos, ticket, conectado, reiniciando, error, reiniciar, cerrarTicket } = useTiendaEnDirecto()
  const [seccion, setSeccion] = useState<Seccion>('menu')
  const [camaras, setCamaras] = useState(camarasIniciales)
  const [incidencias, setIncidencias] = useState(incidenciasIniciales)

  const unidades = carritos.reduce((total, carrito) => total + carrito.totalUnidades, 0)

  return (
    <div className="app-shell">
      <header className="topbar">
        <button className="brand brand-button" type="button" onClick={() => setSeccion('menu')} aria-label="Volver al menú principal">
          <span className="brand-mark" aria-hidden="true">M</span>
          <span>Mercadona<span className="brand-dot">.</span></span>
        </button>
        <span className="topbar-label">GESTIÓN DE TIENDA</span>
        {seccion === 'compras' && <span className={`status-pill${conectado ? '' : ' is-offline'}`} role="status">
          <span /> {conectado ? 'En directo' : 'Conectando...'}
        </span>}
      </header>

      <main id="inicio" className="main-content">
        {seccion === 'menu' ? (
          <>
            <section className="intro">
              <div className="eyebrow"><span /> PANEL DE CONTROL</div>
              <h1>¿Qué quieres<br /><span>gestionar?</span></h1>
              <p className="intro-copy">Selecciona una interfaz para consultar la actividad y gestionar los recursos de la tienda.</p>
            </section>
            <section className="menu-grid" aria-label="Interfaces disponibles">
              <button className="menu-card" type="button" onClick={() => setSeccion('compras')}>
                <span className="menu-card-icon" aria-hidden="true">⌑</span>
                <span className="menu-card-number">01 · EN DIRECTO</span>
                <strong>Visualización de sistema</strong>
                <span className="menu-card-description">Demostración funcionamiento del sistema</span>
                <span className="menu-card-link">Abrir interfaz <span aria-hidden="true">→</span></span>
              </button>
              <button className="menu-card" type="button" onClick={() => setSeccion('camaras')}>
                <span className="menu-card-icon" aria-hidden="true">◉</span>
                <span className="menu-card-number">02 · DISPOSITIVOS</span>
                <strong>Gestor de cámaras</strong>
                <span className="menu-card-description">Revisa las cámaras instaladas y su estado de conexión.</span>
                <span className="menu-card-link">Abrir interfaz <span aria-hidden="true">→</span></span>
              </button>
              <button className="menu-card" type="button" onClick={() => setSeccion('incidencias')}>
                <span className="menu-card-icon" aria-hidden="true">!</span>
                <span className="menu-card-number">03 · SEGUIMIENTO</span>
                <strong>Gestor de incidencias</strong>
                <span className="menu-card-description">Consulta incidencias de ejemplo y actualiza su estado.</span>
                <span className="menu-card-link">Abrir interfaz <span aria-hidden="true">→</span></span>
              </button>
            </section>
          </>
        ) : seccion === 'camaras' ? (
          <>
            <section className="intro">
              <div className="eyebrow"><span /> DISPOSITIVOS</div>
              <h1>Gestor de<br /><span>cámaras</span></h1>
              <p className="intro-copy">Consulta el estado de las cámaras y activa o pausa cada dispositivo.</p>
            </section>
            <section className="management-panel" aria-label="Listado de cámaras">
              <div className="management-heading"><div><h2>Cámaras de la tienda</h2><p>{camaras.filter((camara) => camara.activa).length} de {camaras.length} dispositivos activos</p></div><span className="sample-label">DATOS DE EJEMPLO</span></div>
              <div className="management-list">
                {camaras.map((camara) => <article className="management-row" key={camara.id}>
                  <span className={`device-icon${camara.activa ? ' is-active' : ''}`} aria-hidden="true">◉</span>
                  <div className="management-details"><strong>{camara.nombre}</strong><span>{camara.id} · {camara.ubicacion}</span></div>
                  <span className={`state-badge${camara.activa ? ' is-active' : ' is-paused'}`}>{camara.activa ? 'Activa' : 'Pausada'}</span>
                  <button className="text-button" type="button" onClick={() => setCamaras((actuales) => actuales.map((item) => item.id === camara.id ? { ...item, activa: !item.activa } : item))}>{camara.activa ? 'Pausar' : 'Activar'}</button>
                </article>)}
              </div>
            </section>
          </>
        ) : seccion === 'incidencias' ? (
          <>
            <section className="intro">
              <div className="eyebrow"><span /> SEGUIMIENTO</div>
              <h1>Gestor de<br /><span>incidencias</span></h1>
              <p className="intro-copy">Revisa las incidencias notificadas y marca las que ya estén resueltas.</p>
            </section>
            <section className="management-panel" aria-label="Listado de incidencias">
              <div className="management-heading"><div><h2>Incidencias recientes</h2><p>{incidencias.filter((incidencia) => incidencia.estado !== 'Resuelta').length} pendientes de resolución</p></div><span className="sample-label">DATOS DE EJEMPLO</span></div>
              <div className="management-list">
                {incidencias.map((incidencia) => <article className="management-row incident-row" key={incidencia.id}>
                  <span className={`priority-mark priority-${incidencia.prioridad.toLowerCase()}`} aria-hidden="true">!</span>
                  <div className="management-details"><strong>{incidencia.titulo}</strong><span>{incidencia.id} · {incidencia.zona}</span></div>
                  <span className={`state-badge${incidencia.estado === 'Resuelta' ? ' is-active' : incidencia.estado === 'En curso' ? ' is-progress' : ' is-paused'}`}>{incidencia.estado}</span>
                  {incidencia.estado !== 'Resuelta' && <button className="text-button" type="button" onClick={() => setIncidencias((actuales) => actuales.map((item) => item.id === incidencia.id ? { ...item, estado: 'Resuelta' } : item))}>Resolver</button>}
                </article>)}
              </div>
            </section>
          </>
        ) : (
          <>
        <section className="intro">
          <div className="eyebrow"><span /> TU COMPRA, MÁS FÁCIL</div>
          <h1>¿Qué hay en<br /><span>tu cesta?</span></h1>
          <p className="intro-copy">Sube un vídeo de la tienda: cada producto que alguien coja aparecerá en su cesta al momento. Sin escanear y sin pasar por caja.</p>
        </section>

        <AnalizarVideoCard />

        <section className="workspace" aria-label="Cestas en directo">
          <div className="upload-card">
            <div className="card-heading">
              <div className="step-number">01</div>
              <div>
                <h2>Cestas en directo</h2>
                <p>{plural(carritos.length, 'persona', 'personas')} comprando · {plural(unidades, 'unidad', 'unidades')} en total</p>
              </div>
            </div>

            {carritos.length > 0 ? (
              <div className="cart-list">
                {carritos.map((carrito) => <CarritoCard key={carrito.personaId} carrito={carrito} />)}
              </div>
            ) : (
              <div className="waiting-zone">
                <div className="upload-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="none"><path d="M3.5 5h2l2.2 10.2a1.5 1.5 0 0 0 1.5 1.2h7.6a1.5 1.5 0 0 0 1.5-1.1L20 9H7M10 20.2h.01M17 20.2h.01" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" /></svg>
                </div>
                <strong>Esperando a que alguien coja un producto</strong>
                <span>Ponte delante de la cámara y coge una botella</span>
              </div>
            )}

            {error && <p className="error-message" role="alert">{error}</p>}

            <button className="process-button" type="button" onClick={reiniciar} disabled={!conectado || reiniciando}>
              {reiniciando ? <><span className="spinner" /> Reiniciando...</> : <>Reiniciar demo <span aria-hidden="true">↺</span></>}
            </button>
            <p className="privacy-note"><span aria-hidden="true">◆</span> No se guardan imágenes: solo los productos que coges.</p>
          </div>

          <aside className="info-card">
            <div className="info-icon" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none"><path d="M3 12h4l2.5-6 5 12 2.5-6h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </div>
            <span className="info-kicker">ACTIVIDAD EN DIRECTO</span>
            {/* El espacio antes del <br /> evita que en móvil, donde se oculta el salto, se junten las palabras */}
            <h3>Lo que pasa <br />en la tienda</h3>
            {eventos.length > 0 ? (
              <ListaActividad eventos={eventos} />
            ) : (
              <ol className="steps-list">
                <li><span>1</span> Ponte delante de la cámara</li>
                <li><span>2</span> Coge un producto</li>
                <li><span>3</span> Sal del plano para pagar</li>
              </ol>
            )}
            <div className="info-decoration" aria-hidden="true">✳</div>
          </aside>
        </section>

        {ticket && <TicketCard ticket={ticket} onCerrar={cerrarTicket} />}
          </>
        )}

        <footer className="page-footer"><span>HECHO PARA SIMPLIFICAR TU DÍA</span><span>Compra fácil, vida fácil.</span></footer>
      </main>
    </div>
  )
}

export default App
