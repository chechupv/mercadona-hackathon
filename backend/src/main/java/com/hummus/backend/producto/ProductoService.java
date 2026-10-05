package com.hummus.backend.producto;

import java.util.List;

import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hummus.backend.producto.dto.ProductoResponse;

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

    /** Para el historial: si el producto ya no está en el catálogo, devuelve el código en vez de fallar. */
    @Transactional(readOnly = true)
    public String nombreDe(String codigo) {
        return productoRepository.findById(codigo).map(Producto::getNombre).orElse(codigo);
    }

    @Transactional(readOnly = true)
    public List<ProductoResponse> listar() {
        return productoRepository.findAll(Sort.by("nombre")).stream()
                .map(ProductoResponse::from)
                .toList();
    }
}
