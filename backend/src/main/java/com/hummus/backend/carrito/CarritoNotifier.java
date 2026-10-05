package com.hummus.backend.carrito;

import java.util.List;

import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import com.hummus.backend.carrito.dto.CarritoResponse;

@Component
public class CarritoNotifier {

    public static final String TOPIC = "/topic/carritos";

    private final SimpMessagingTemplate messagingTemplate;

    public CarritoNotifier(SimpMessagingTemplate messagingTemplate) {
        this.messagingTemplate = messagingTemplate;
    }

    /** Envía siempre la lista completa: el front solo tiene que reemplazar su estado. */
    public void notificar(List<CarritoResponse> carritos) {
        messagingTemplate.convertAndSend(TOPIC, carritos);
    }
}
