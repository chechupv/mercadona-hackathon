package com.hummus.backend.common.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;

/** Título y descripción que aparecen en Swagger UI. */
@Configuration
public class OpenApiConfig {

    @Bean
    public OpenAPI openApi() {
        return new OpenAPI().info(new Info()
                .title("Mercadona Just Walk Out")
                .version("0.0.1")
                .description("""
                        API del carrito automático. La visión envía COGER o DEVOLVER a /api/eventos \
                        y el front recibe los cambios por WebSocket (ws://localhost:8080/ws): \
                        /topic/carritos, /topic/eventos y /topic/tickets."""));
    }
}
