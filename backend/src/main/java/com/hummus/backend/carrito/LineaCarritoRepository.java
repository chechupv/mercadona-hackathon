package com.hummus.backend.carrito;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;

public interface LineaCarritoRepository extends JpaRepository<LineaCarrito, Long> {

    Optional<LineaCarrito> findByPersonaIdAndProductoCodigo(Long personaId, String codigo);

    List<LineaCarrito> findByPersonaIdOrderByIdAsc(Long personaId);

    List<LineaCarrito> findAllByOrderByPersonaIdAscIdAsc();

    void deleteByPersonaId(Long personaId);
}
