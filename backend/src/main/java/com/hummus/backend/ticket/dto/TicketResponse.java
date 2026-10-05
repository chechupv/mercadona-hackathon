package com.hummus.backend.ticket.dto;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

import com.hummus.backend.ticket.Ticket;

public record TicketResponse(
        Long id,
        Long personaId,
        Instant fecha,
        List<LineaTicket> lineas,
        int totalUnidades,
        BigDecimal total) {

    public record LineaTicket(
            String producto,
            String nombre,
            int cantidad,
            BigDecimal precioUnitario,
            BigDecimal subtotal) {
    }

    public static TicketResponse from(Ticket ticket) {
        List<LineaTicket> lineas = ticket.getLineas().stream()
                .map(linea -> new LineaTicket(linea.getProductoCodigo(), linea.getNombre(), linea.getCantidad(),
                        linea.getPrecioUnitario(), linea.getSubtotal()))
                .toList();
        return new TicketResponse(ticket.getId(), ticket.getPersonaId(), ticket.getFecha(), lineas,
                ticket.getTotalUnidades(), ticket.getTotal());
    }
}
