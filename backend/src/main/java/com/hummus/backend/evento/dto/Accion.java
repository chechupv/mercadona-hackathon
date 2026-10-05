package com.hummus.backend.evento.dto;

public enum Accion {
    COGER,
    DEVOLVER,
    /** Una persona le da el producto a otra. No cambia ningún carrito: lo sigue pagando quien lo cogió. */
    REGALAR
}
