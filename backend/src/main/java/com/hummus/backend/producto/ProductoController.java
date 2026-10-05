package com.hummus.backend.producto;

import java.util.List;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import com.hummus.backend.producto.dto.ProductoResponse;

@RestController
@RequestMapping("/api/productos")
public class ProductoController {

    private final ProductoService productoService;

    public ProductoController(ProductoService productoService) {
        this.productoService = productoService;
    }

    /** Catálogo completo, ordenado por nombre. */
    @GetMapping
    public List<ProductoResponse> listar() {
        return productoService.listar();
    }
}
