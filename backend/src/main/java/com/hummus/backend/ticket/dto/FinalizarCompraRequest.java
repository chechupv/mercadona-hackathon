package com.hummus.backend.ticket.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record FinalizarCompraRequest(@NotNull @Positive Long personaId) {
}
