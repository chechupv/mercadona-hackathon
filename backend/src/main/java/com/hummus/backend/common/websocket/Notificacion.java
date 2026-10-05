package com.hummus.backend.common.websocket;

/**
 * Mensaje pendiente de enviar por WebSocket.
 * Los services lo publican con ApplicationEventPublisher y NotificacionListener
 * lo envía cuando la transacción se ha guardado.
 */
public record Notificacion(String topic, Object contenido) {
}
