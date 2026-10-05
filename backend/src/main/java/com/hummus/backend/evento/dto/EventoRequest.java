package com.hummus.backend.evento.dto;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record EventoRequest(
        @NotNull @Positive Long personaId,
        @NotBlank String producto,
        @NotNull Accion accion) {
}
