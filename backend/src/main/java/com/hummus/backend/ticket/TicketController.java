package com.hummus.backend.ticket;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.hummus.backend.ticket.dto.FinalizarCompraRequest;
import com.hummus.backend.ticket.dto.TicketResponse;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;

@RestController
@RequestMapping("/api/tickets")
public class TicketController {

    private final TicketService ticketService;

    public TicketController(TicketService ticketService) {
        this.ticketService = ticketService;
    }

    /** Finaliza la compra de una persona (por ejemplo, cuando sale de la tienda). */
    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public TicketResponse finalizar(@Valid @RequestBody FinalizarCompraRequest request) {
        return ticketService.finalizar(request.personaId());
    }

    @GetMapping
    public List<TicketResponse> ultimos(@RequestParam(defaultValue = "20") @Min(1) @Max(200) int limite) {
        return ticketService.ultimos(limite);
    }

    @GetMapping("/{id}")
    public ResponseEntity<TicketResponse> buscar(@PathVariable Long id) {
        return ResponseEntity.of(ticketService.buscar(id));
    }
}
