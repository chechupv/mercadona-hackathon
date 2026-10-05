package com.hummus.backend.evento;

import java.time.Instant;

import com.hummus.backend.evento.dto.Accion;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;

/** Historial: cada COGER o DEVOLVER que llega desde la visión. */
@Entity
public class Evento {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long personaId;

    @Column(nullable = false)
    private String producto;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Accion accion;

    @Column(nullable = false)
    private Instant fecha;

    protected Evento() {
    }

    public Evento(Long personaId, String producto, Accion accion) {
        this.personaId = personaId;
        this.producto = producto;
        this.accion = accion;
        this.fecha = Instant.now();
    }

    public Long getId() {
        return id;
    }

    public Long getPersonaId() {
        return personaId;
    }

    public String getProducto() {
        return producto;
    }

    public Accion getAccion() {
        return accion;
    }

    public Instant getFecha() {
        return fecha;
    }
}
