import './AppStyles.css'
import CarritoCard from './components/CarritoCard'
import ListaActividad from './components/ListaActividad'
import TicketCard from './components/TicketCard'
import { useTiendaEnDirecto } from './hooks/useTiendaEnDirecto'
import { plural } from './utils/formato'

function App() {
  const { carritos, eventos, ticket, conectado, reiniciando, error, reiniciar, cerrarTicket } = useTiendaEnDirecto()

  const unidades = carritos.reduce((total, carrito) => total + carrito.totalUnidades, 0)

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#inicio" aria-label="Mercadona, inicio">
          <span className="brand-mark" aria-hidden="true">M</span>
          <span>Mercadona<span className="brand-dot">.</span></span>
        </a>
        <span className="topbar-label">CAJA AUTOMÁTICA</span>
        <span className={`status-pill${conectado ? '' : ' is-offline'}`} role="status">
          <span /> {conectado ? 'En directo' : 'Conectando...'}
        </span>
      </header>

      <main id="inicio" className="main-content">
        <section className="intro">
          <div className="eyebrow"><span /> TU COMPRA, MÁS FÁCIL</div>
          <h1>¿Qué hay en<br /><span>tu cesta?</span></h1>
          <p className="intro-copy">Coge un producto delante de la cámara y aparecerá en tu cesta al momento. Sin escanear y sin pasar por caja.</p>
        </section>

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

        <footer className="page-footer"><span>HECHO PARA SIMPLIFICAR TU DÍA</span><span>Compra fácil, vida fácil.</span></footer>
      </main>
    </div>
  )
}

export default App
