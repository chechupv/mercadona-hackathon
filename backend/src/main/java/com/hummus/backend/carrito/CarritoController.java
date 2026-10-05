package com.hummus.backend.carrito;

import java.util.List;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.ResponseStatus;
import org.springframework.web.bind.annotation.RestController;

import com.hummus.backend.carrito.dto.CarritoResponse;

@RestController
@RequestMapping("/api/carritos")
public class CarritoController {

    private final CarritoService carritoService;

    public CarritoController(CarritoService carritoService) {
        this.carritoService = carritoService;
    }

    @GetMapping
    public List<CarritoResponse> listar() {
        return carritoService.listar();
    }

    @GetMapping("/{personaId}")
    public ResponseEntity<CarritoResponse> buscar(@PathVariable Long personaId) {
        return ResponseEntity.of(carritoService.buscar(personaId));
    }

    /** Para reiniciar entre tomas del vídeo. El historial de eventos se conserva. */
    @DeleteMapping
    @ResponseStatus(HttpStatus.NO_CONTENT)
    public void vaciar() {
        carritoService.vaciarTodos();
    }
}
