package com.hummus.backend.evento.dto;

import java.time.Instant;

import com.hummus.backend.evento.Evento;

public record EventoResponse(
        Long id,
        Long personaId,
        String producto,
        String nombre,
        Accion accion,
        Instant fecha) {

    public static EventoResponse from(Evento evento, String nombreProducto) {
        return new EventoResponse(evento.getId(), evento.getPersonaId(), evento.getProducto(), nombreProducto,
                evento.getAccion(), evento.getFecha());
    }
}
