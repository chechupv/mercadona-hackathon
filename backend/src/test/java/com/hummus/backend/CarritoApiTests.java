package com.hummus.backend;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.delete;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.options;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.header;
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

import com.hummus.backend.evento.EventoRepository;

@SpringBootTest
class CarritoApiTests {

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
    void cogerYDevolverActualizaElCarrito() throws Exception {
        evento(1, "bottle", "COGER");
        evento(1, "bottle", "COGER")
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.lineas[0].producto").value("bottle"))
                .andExpect(jsonPath("$.lineas[0].cantidad").value(2))
                .andExpect(jsonPath("$.total").value(0.90));

        evento(1, "bottle", "DEVOLVER").andExpect(jsonPath("$.totalUnidades").value(1));
        mvc.perform(get("/api/carritos/1")).andExpect(jsonPath("$.totalUnidades").value(1));

        evento(1, "bottle", "DEVOLVER");
        // Un DEVOLVER de más no deja la cantidad en negativo
        evento(1, "bottle", "DEVOLVER").andExpect(jsonPath("$.totalUnidades").value(0));

        mvc.perform(get("/api/carritos")).andExpect(content().json("[]"));
        assertEquals(5, eventoRepository.count());
    }

    @Test
    void cadaPersonaTieneSuCarrito() throws Exception {
        evento(1, "bottle", "COGER");
        evento(2, "cup", "COGER");

        mvc.perform(get("/api/carritos"))
                .andExpect(jsonPath("$.length()").value(2))
                .andExpect(jsonPath("$[0].personaId").value(1))
                .andExpect(jsonPath("$[1].lineas[0].producto").value("cup"));
    }

    @Test
    void erroresDevuelven400o404() throws Exception {
        evento(1, "laptop", "COGER")
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.detail").value("Producto desconocido: laptop"));

        mvc.perform(post("/api/eventos").contentType(MediaType.APPLICATION_JSON)
                .content("{\"producto\":\"\",\"accion\":\"COGER\"}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.errores.length()").value(2));

        evento(1, "bottle", "ROBAR").andExpect(status().isBadRequest());
        mvc.perform(get("/api/carritos/9")).andExpect(status().isNotFound());
    }

    @Test
    void vaciarYCors() throws Exception {
        evento(1, "bottle", "COGER");
        mvc.perform(delete("/api/carritos")).andExpect(status().isNoContent());
        mvc.perform(get("/api/carritos")).andExpect(content().json("[]"));

        mvc.perform(options("/api/eventos")
                .header("Origin", "http://localhost:5173")
                .header("Access-Control-Request-Method", "POST"))
                .andExpect(header().string("Access-Control-Allow-Origin", "http://localhost:5173"));
    }

    private ResultActions evento(long personaId, String producto, String accion) throws Exception {
        String json = "{\"personaId\":%d,\"producto\":\"%s\",\"accion\":\"%s\"}"
                .formatted(personaId, producto, accion);
        return mvc.perform(post("/api/eventos").contentType(MediaType.APPLICATION_JSON).content(json));
    }
}
