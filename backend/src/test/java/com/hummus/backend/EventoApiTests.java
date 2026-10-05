package com.hummus.backend;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

import com.hummus.backend.evento.EventoRepository;

@SpringBootTest
class EventoApiTests {

    @Autowired
    WebApplicationContext context;

    @Autowired
    EventoRepository eventoRepository;

    MockMvc mvc;

    @BeforeEach
    void setUp() throws Exception {
        mvc = MockMvcBuilders.webAppContextSetup(context).build();
        mvc.perform(delete("/api/carritos"));
        eventoRepository.deleteAll();
    }

    @Test
    void elHistorialDevuelveLosMasRecientesPrimero() throws Exception {
        evento(1, "bottle", "COGER");
        evento(2, "cup", "COGER");
        evento(1, "bottle", "DEVOLVER");

        mvc.perform(get("/api/eventos"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.length()").value(3))
                .andExpect(jsonPath("$[0].accion").value("DEVOLVER"))
                .andExpect(jsonPath("$[0].producto").value("bottle"))
                .andExpect(jsonPath("$[0].nombre").isString())
                .andExpect(jsonPath("$[0].fecha").isString())
                .andExpect(jsonPath("$[2].personaId").value(1));
    }

    @Test
    void elLimiteFunciona() throws Exception {
        evento(1, "bottle", "COGER");
        evento(1, "bottle", "COGER");

        mvc.perform(get("/api/eventos").param("limite", "1"))
                .andExpect(jsonPath("$.length()").value(1));
        mvc.perform(get("/api/eventos").param("limite", "0"))
                .andExpect(status().isBadRequest());
    }

    private void evento(long personaId, String producto, String accion) throws Exception {
        mvc.perform(post("/api/eventos").contentType(MediaType.APPLICATION_JSON)
                .content("{\"personaId\":%d,\"producto\":\"%s\",\"accion\":\"%s\"}"
                        .formatted(personaId, producto, accion)))
                .andExpect(status().isOk());
    }
}
