package com.hummus.backend.evento;

import java.util.List;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.domain.Limit;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hummus.backend.carrito.CarritoService;
import com.hummus.backend.carrito.dto.CarritoResponse;
import com.hummus.backend.common.websocket.Notificacion;
import com.hummus.backend.evento.dto.EventoRequest;
import com.hummus.backend.evento.dto.EventoResponse;
import com.hummus.backend.producto.Producto;
import com.hummus.backend.producto.ProductoService;

@Service
public class EventoService {

    /** El front recibe aquí cada evento nuevo, para mostrar "Persona 1 ha cogido Agua". */
    public static final String TOPIC = "/topic/eventos";

    private final ProductoService productoService;
    private final CarritoService carritoService;
    private final EventoRepository eventoRepository;
    private final ApplicationEventPublisher eventPublisher;

    public EventoService(ProductoService productoService, CarritoService carritoService,
            EventoRepository eventoRepository, ApplicationEventPublisher eventPublisher) {
        this.productoService = productoService;
        this.carritoService = carritoService;
        this.eventoRepository = eventoRepository;
        this.eventPublisher = eventPublisher;
    }

    @Transactional
    public CarritoResponse procesar(EventoRequest evento) {
        // Lanza ProductoDesconocidoException (400) si YOLO manda algo que no está en el catálogo
        Producto producto = productoService.buscar(evento.producto());

        Evento guardado = eventoRepository.save(new Evento(evento.personaId(), evento.producto(), evento.accion()));
        eventPublisher.publishEvent(new Notificacion(TOPIC, EventoResponse.from(guardado, producto.getNombre())));

        return switch (evento.accion()) {
            case COGER -> carritoService.sumar(evento.personaId(), evento.producto());
            case DEVOLVER -> carritoService.restar(evento.personaId(), evento.producto());
        };
    }

    @Transactional(readOnly = true)
    public List<EventoResponse> ultimos(int limite) {
        return eventoRepository.findByOrderByIdDesc(Limit.of(limite)).stream()
                .map(evento -> EventoResponse.from(evento, productoService.nombreDe(evento.getProducto())))
                .toList();
    }
}
