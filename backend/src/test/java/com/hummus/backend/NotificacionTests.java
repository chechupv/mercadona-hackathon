package com.hummus.backend;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.clearInvocations;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import com.hummus.backend.carrito.CarritoService;
import com.hummus.backend.evento.EventoService;
import com.hummus.backend.ticket.TicketService;

@SpringBootTest
class NotificacionTests {

    @Autowired
    WebApplicationContext context;

    @MockitoBean
    SimpMessagingTemplate messagingTemplate;

    MockMvc mvc;

    @BeforeEach
    void setUp() throws Exception {
        mvc = MockMvcBuilders.webAppContextSetup(context).build();
        mvc.perform(delete("/api/carritos"));
        clearInvocations(messagingTemplate);
    }

    @Test
    void unCambioEnElCarritoSeEnviaPorWebSocket() throws Exception {
        mvc.perform(post("/api/eventos").contentType(MediaType.APPLICATION_JSON)
                .content("{\"personaId\":1,\"producto\":\"bottle\",\"accion\":\"COGER\"}"))
                .andExpect(status().isOk());

        verify(messagingTemplate).convertAndSend(eq(CarritoService.TOPIC), any(Object.class));
        verify(messagingTemplate).convertAndSend(eq(EventoService.TOPIC), any(Object.class));
    }

    @Test
    void finalizarLaCompraEnviaElTicketYElCarritoVacio() throws Exception {
        mvc.perform(post("/api/eventos").contentType(MediaType.APPLICATION_JSON)
                .content("{\"personaId\":1,\"producto\":\"bottle\",\"accion\":\"COGER\"}"));
        clearInvocations(messagingTemplate);

        mvc.perform(post("/api/tickets").contentType(MediaType.APPLICATION_JSON).content("{\"personaId\":1}"))
                .andExpect(status().isCreated());

        verify(messagingTemplate).convertAndSend(eq(TicketService.TOPIC), any(Object.class));
        verify(messagingTemplate).convertAndSend(eq(CarritoService.TOPIC), any(Object.class));
    }

    @Test
    void unEventoQueFallaNoEnviaNada() throws Exception {
        mvc.perform(post("/api/eventos").contentType(MediaType.APPLICATION_JSON)
                .content("{\"personaId\":1,\"producto\":\"laptop\",\"accion\":\"COGER\"}"))
                .andExpect(status().isBadRequest());

        verifyNoInteractions(messagingTemplate);
    }
}
