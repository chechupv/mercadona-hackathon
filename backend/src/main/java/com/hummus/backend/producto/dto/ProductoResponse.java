package com.hummus.backend.producto.dto;

import java.math.BigDecimal;

import com.hummus.backend.producto.Producto;

public record ProductoResponse(String codigo, String nombre, BigDecimal precio) {

    public static ProductoResponse from(Producto producto) {
        return new ProductoResponse(producto.getCodigo(), producto.getNombre(), producto.getPrecio());
    }
}
