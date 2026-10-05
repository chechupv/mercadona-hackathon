package com.hummus.backend.ticket;

import java.util.List;
import java.util.Optional;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.data.domain.Limit;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hummus.backend.carrito.CarritoService;
import com.hummus.backend.carrito.dto.CarritoResponse;
import com.hummus.backend.common.websocket.Notificacion;
import com.hummus.backend.ticket.dto.TicketResponse;

@Service
public class TicketService {

    /** El front recibe aquí cada ticket nuevo, para mostrarlo al salir la persona. */
    public static final String TOPIC = "/topic/tickets";

    private final TicketRepository ticketRepository;
    private final CarritoService carritoService;
    private final ApplicationEventPublisher eventPublisher;

    public TicketService(TicketRepository ticketRepository, CarritoService carritoService,
            ApplicationEventPublisher eventPublisher) {
        this.ticketRepository = ticketRepository;
        this.carritoService = carritoService;
        this.eventPublisher = eventPublisher;
    }

    /** Convierte el carrito en un ticket y lo vacía. Todo en una transacción: o se hace entero o nada. */
    @Transactional
    public TicketResponse finalizar(Long personaId) {
        CarritoResponse carrito = carritoService.buscar(personaId)
                .orElseThrow(() -> new CarritoVacioException(personaId));

        Ticket ticket = new Ticket(personaId);
        carrito.lineas().forEach(linea ->
                ticket.agregarLinea(linea.producto(), linea.nombre(), linea.cantidad(), linea.precioUnitario()));

        TicketResponse response = TicketResponse.from(ticketRepository.save(ticket));
        carritoService.vaciar(personaId);
        eventPublisher.publishEvent(new Notificacion(TOPIC, response));
        return response;
    }

    @Transactional(readOnly = true)
    public List<TicketResponse> ultimos(int limite) {
        return ticketRepository.findByOrderByIdDesc(Limit.of(limite)).stream()
                .map(TicketResponse::from)
                .toList();
    }

    @Transactional(readOnly = true)
    public Optional<TicketResponse> buscar(Long id) {
        return ticketRepository.findById(id).map(TicketResponse::from);
    }
}
