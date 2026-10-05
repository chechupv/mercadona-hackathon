package com.hummus.backend.producto;

public class ProductoDesconocidoException extends RuntimeException {

    public ProductoDesconocidoException(String codigo) {
        super("Producto desconocido: " + codigo);
    }
}
