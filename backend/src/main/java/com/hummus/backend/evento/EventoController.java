package com.hummus.backend.evento;

import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hummus.backend.carrito.dto.CarritoResponse;
import com.hummus.backend.evento.dto.EventoRequest;

import jakarta.validation.Valid;

@RestController
@RequestMapping("/api/eventos")
public class EventoController {

    private final EventoService eventoService;

    public EventoController(EventoService eventoService) {
        this.eventoService = eventoService;
    }

    @PostMapping
    public CarritoResponse registrar(@Valid @RequestBody EventoRequest evento) {
        return eventoService.procesar(evento);
    }
}
