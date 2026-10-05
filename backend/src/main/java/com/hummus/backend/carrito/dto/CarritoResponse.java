package com.hummus.backend.carrito.dto;

import java.math.BigDecimal;
import java.util.List;

public record CarritoResponse(
        Long personaId,
        List<LineaCarrito> lineas,
        int totalUnidades,
        BigDecimal total) {

    public record LineaCarrito(
            String producto,
            String nombre,
            int cantidad,
            BigDecimal precioUnitario,
            BigDecimal subtotal) {
    }
}
