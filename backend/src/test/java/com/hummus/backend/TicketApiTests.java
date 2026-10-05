package com.hummus.backend;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.ResultActions;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import com.hummus.backend.ticket.TicketRepository;

import tools.jackson.databind.json.JsonMapper;

@SpringBootTest
class TicketApiTests {

    @Autowired
    WebApplicationContext context;

    @Autowired
    TicketRepository ticketRepository;

    MockMvc mvc;

    @BeforeEach
    void setUp() throws Exception {
        mvc = MockMvcBuilders.webAppContextSetup(context).build();
        mvc.perform(delete("/api/carritos"));
        ticketRepository.deleteAll();
    }

    @Test
    void finalizarConvierteElCarritoEnTicketYLoVacia() throws Exception {
        evento(1, "bottle", "COGER");
        evento(1, "bottle", "COGER");
        evento(1, "cup", "COGER");
        evento(2, "cup", "COGER");

        String json = finalizar(1)
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.personaId").value(1))
                .andExpect(jsonPath("$.lineas.length()").value(2))
                .andExpect(jsonPath("$.lineas[0].producto").value("bottle"))
                .andExpect(jsonPath("$.lineas[0].cantidad").value(2))
                .andExpect(jsonPath("$.totalUnidades").value(3))
                .andExpect(jsonPath("$.fecha").isString())
                .andReturn().getResponse().getContentAsString();

        // El carrito de la persona 1 queda vacío; el de la persona 2 no se toca
        mvc.perform(get("/api/carritos/1")).andExpect(status().isNotFound());
        mvc.perform(get("/api/carritos/2")).andExpect(jsonPath("$.totalUnidades").value(1));

        long id = JsonMapper.builder().build().readTree(json).get("id").asLong();
        mvc.perform(get("/api/tickets/" + id)).andExpect(jsonPath("$.totalUnidades").value(3));
        mvc.perform(get("/api/tickets")).andExpect(jsonPath("$[0].id").value(id));
    }

    @Test
    void finalizarSinProductosDevuelve409() throws Exception {
        finalizar(1)
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.detail").value("La persona 1 no tiene productos en el carrito"));
        mvc.perform(get("/api/tickets")).andExpect(content().json("[]"));
    }

    @Test
    void erroresDevuelven400o404() throws Exception {
        mvc.perform(post("/api/tickets").contentType(MediaType.APPLICATION_JSON).content("{}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errores[0]").value("personaId: must not be null"));
        mvc.perform(get("/api/tickets/999")).andExpect(status().isNotFound());
    }

    private ResultActions finalizar(long personaId) throws Exception {
        return mvc.perform(post("/api/tickets").contentType(MediaType.APPLICATION_JSON)
                .content("{\"personaId\":%d}".formatted(personaId)));
    }

    private void evento(long personaId, String producto, String accion) throws Exception {
        mvc.perform(post("/api/eventos").contentType(MediaType.APPLICATION_JSON)
                .content("{\"personaId\":%d,\"producto\":\"%s\",\"accion\":\"%s\"}"
                        .formatted(personaId, producto, accion)))
                .andExpect(status().isOk());
    }
}
