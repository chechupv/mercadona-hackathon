package com.hummus.backend.common.websocket;

import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.event.TransactionalEventListener;

@Component
public class NotificacionListener {

    private final SimpMessagingTemplate messagingTemplate;

    public NotificacionListener(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    /**
     * Se ejecuta después del commit: si la transacción falla, no se envía nada.
     * fallbackExecution = true hace que también funcione si se publica fuera de una transacción.
     */
    @TransactionalEventListener(fallbackExecution = true)
    public void enviar(Notificacion notificacion) {
        messagingTemplate.convertAndSend(notificacion.topic(), notificacion.contenido());
    }
}
