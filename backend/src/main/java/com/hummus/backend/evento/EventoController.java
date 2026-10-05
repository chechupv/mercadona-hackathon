package com.hummus.backend.evento;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.hummus.backend.carrito.dto.CarritoResponse;
import com.hummus.backend.evento.dto.EventoRequest;
import com.hummus.backend.evento.dto.EventoResponse;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

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

    /** Historial, los más recientes primero. */
    @GetMapping
    public List<EventoResponse> ultimos(@RequestParam(defaultValue = "20") @Min(1) @Max(200) int limite) {
        return eventoService.ultimos(limite);
    }
}
