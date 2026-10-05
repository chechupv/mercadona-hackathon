package com.hummus.backend.evento.dto;

import jakarta.validation.constraints.AssertTrue;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

/**
 * @param personaId  en COGER y DEVOLVER, quien paga; en REGALAR, quien da el producto
 * @param receptorId solo en REGALAR: quien recibe el producto
 */
public record EventoRequest(
        @NotNull @Positive Long personaId,
        @NotBlank String producto,
        @NotNull Accion accion,
        @Positive Long receptorId) {

    @AssertTrue(message = "receptorId es obligatorio en REGALAR y tiene que ser distinto de personaId")
    public boolean isReceptorValido() {
        if (accion != Accion.REGALAR) {
            return true;
        }
        return receptorId != null && !receptorId.equals(personaId);
    }
}
