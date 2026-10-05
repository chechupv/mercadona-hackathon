package com.hummus.backend.ticket;

public class CarritoVacioException extends RuntimeException {

    public CarritoVacioException(Long personaId) {
        super("La persona " + personaId + " no tiene productos en el carrito");
    }
}
