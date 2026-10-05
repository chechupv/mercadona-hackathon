package com.hummus.backend;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.context.WebApplicationContext;

@SpringBootTest
class DocumentacionApiTests {

    @Autowired
    WebApplicationContext context;

    @Test
    void swaggerDocumentaTodosLosEndpoints() throws Exception {
        MockMvc mvc = MockMvcBuilders.webAppContextSetup(context).build();

        mvc.perform(get("/v3/api-docs"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.info.title").value("Mercadona Just Walk Out"))
                .andExpect(jsonPath("$.paths['/api/eventos']").exists())
                .andExpect(jsonPath("$.paths['/api/carritos']").exists())
                .andExpect(jsonPath("$.paths['/api/productos']").exists())
                .andExpect(jsonPath("$.paths['/api/tickets']").exists());
    }
}
