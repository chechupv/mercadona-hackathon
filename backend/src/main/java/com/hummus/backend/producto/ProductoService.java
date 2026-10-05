package com.hummus.backend.producto;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class ProductoService {

    private final ProductoRepository productoRepository;

    public ProductoService(ProductoRepository productoRepository) {
        this.productoRepository = productoRepository;
    }

    @Transactional(readOnly = true)
    public Producto buscar(String codigo) {
        return productoRepository.findById(codigo)
                .orElseThrow(() -> new ProductoDesconocidoException(codigo));
    }
}
