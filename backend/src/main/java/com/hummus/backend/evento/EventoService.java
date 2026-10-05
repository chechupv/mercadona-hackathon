package com.hummus.backend.evento;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hummus.backend.carrito.CarritoService;
import com.hummus.backend.carrito.dto.CarritoResponse;
import com.hummus.backend.evento.dto.EventoRequest;
import com.hummus.backend.producto.ProductoService;

@Service
public class EventoService {

    private final ProductoService productoService;
    private final CarritoService carritoService;
    private final EventoRepository eventoRepository;

    public EventoService(ProductoService productoService, CarritoService carritoService,
            EventoRepository eventoRepository) {
        this.productoService = productoService;
        this.carritoService = carritoService;
        this.eventoRepository = eventoRepository;
    }

    @Transactional
    public CarritoResponse procesar(EventoRequest evento) {
        // Lanza ProductoDesconocidoException (400) si YOLO manda algo que no está en el catálogo
        productoService.buscar(evento.producto());

        eventoRepository.save(new Evento(evento.personaId(), evento.producto(), evento.accion()));

        return switch (evento.accion()) {
            case COGER -> carritoService.sumar(evento.personaId(), evento.producto());
            case DEVOLVER -> carritoService.restar(evento.personaId(), evento.producto());
        };
    }
}
