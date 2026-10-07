package com.hummus.backend.carrito;

import java.math.BigDecimal;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

import org.springframework.context.ApplicationEventPublisher;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.hummus.backend.carrito.dto.CarritoResponse;
import com.hummus.backend.common.websocket.Notificacion;
import com.hummus.backend.producto.Producto;
import com.hummus.backend.producto.ProductoService;

@Service
@Transactional
public class CarritoService {

    /** El front recibe aquí la lista completa de carritos tras cada cambio. */
    public static final String TOPIC = "/topic/carritos";

    private final LineaCarritoRepository lineaRepository;
    private final ProductoService productoService;
    private final ApplicationEventPublisher eventPublisher;

    public CarritoService(LineaCarritoRepository lineaRepository, ProductoService productoService,
            ApplicationEventPublisher eventPublisher) {
        this.lineaRepository = lineaRepository;
        this.productoService = productoService;
        this.eventPublisher = eventPublisher;
    }

    public CarritoResponse sumar(Long personaId, String codigo) {
        LineaCarrito linea = lineaRepository.findByPersonaIdAndProductoCodigo(personaId, codigo)
                .orElseGet(() -> new LineaCarrito(personaId, productoService.buscar(codigo)));
        linea.sumar();
        lineaRepository.save(linea);
        return notificarYDevolver(personaId);
    }

    public CarritoResponse restar(Long personaId, String codigo) {
        lineaRepository.findByPersonaIdAndProductoCodigo(personaId, codigo).ifPresent(linea -> {
            // Nunca baja de 0: al llegar a 0 se borra la línea
            if (linea.getCantidad() > 1) {
                linea.restar();
            } else {
                lineaRepository.delete(linea);
            }
        });
        return notificarYDevolver(personaId);
    }

    @Transactional(readOnly = true)
    public List<CarritoResponse> listar() {
        Map<Long, List<LineaCarrito>> porPersona = lineaRepository.findAllByOrderByPersonaIdAscIdAsc().stream()
                .collect(Collectors.groupingBy(LineaCarrito::getPersonaId, LinkedHashMap::new, Collectors.toList()));
        return porPersona.entrySet().stream()
                .map(entry -> toResponse(entry.getKey(), entry.getValue()))
                .toList();
    }

    @Transactional(readOnly = true)
    public Optional<CarritoResponse> buscar(Long personaId) {
        List<LineaCarrito> lineas = lineaRepository.findByPersonaIdOrderByIdAsc(personaId);
        return lineas.isEmpty() ? Optional.empty() : Optional.of(toResponse(personaId, lineas));
    }

    /** El carrito de una persona; vacío si no lleva nada. */
    @Transactional(readOnly = true)
    public CarritoResponse obtener(Long personaId) {
        return toResponse(personaId, lineaRepository.findByPersonaIdOrderByIdAsc(personaId));
    }

    /** Se usa al finalizar la compra: el carrito pasa a ser un ticket. */
    public void vaciar(Long personaId) {
        lineaRepository.deleteByPersonaId(personaId);
        eventPublisher.publishEvent(new Notificacion(TOPIC, listar()));
    }

    public void vaciarTodos() {
        lineaRepository.deleteAllInBatch();
        eventPublisher.publishEvent(new Notificacion(TOPIC, List.of()));
    }

    private CarritoResponse notificarYDevolver(Long personaId) {
        eventPublisher.publishEvent(new Notificacion(TOPIC, listar()));
        return toResponse(personaId, lineaRepository.findByPersonaIdOrderByIdAsc(personaId));
    }

    private CarritoResponse toResponse(Long personaId, List<LineaCarrito> lineas) {
        List<CarritoResponse.LineaCarrito> lineasResponse = lineas.stream()
                .map(linea -> {
                    Producto producto = linea.getProducto();
                    BigDecimal subtotal = producto.getPrecio().multiply(BigDecimal.valueOf(linea.getCantidad()));
                    return new CarritoResponse.LineaCarrito(producto.getCodigo(), producto.getNombre(),
                            linea.getCantidad(), producto.getPrecio(), subtotal);
                })
                .toList();

        int totalUnidades = lineasResponse.stream().mapToInt(CarritoResponse.LineaCarrito::cantidad).sum();
        BigDecimal total = lineasResponse.stream()
                .map(CarritoResponse.LineaCarrito::subtotal)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
        return new CarritoResponse(personaId, lineasResponse, totalUnidades, total);
    }
}
