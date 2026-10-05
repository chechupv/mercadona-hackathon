package com.hummus.backend.ticket;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.OneToMany;
import jakarta.persistence.OrderBy;

/** Compra finalizada: lo que llevaba la persona al salir de la tienda. */
@Entity
public class Ticket {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private Long personaId;

    @Column(nullable = false)
    private Instant fecha;

    @Column(nullable = false)
    private int totalUnidades;

    @Column(nullable = false, precision = 10, scale = 2)
    private BigDecimal total = BigDecimal.ZERO;

    @OneToMany(mappedBy = "ticket", cascade = CascadeType.ALL, orphanRemoval = true)
    @OrderBy("id")
    private List<LineaTicket> lineas = new ArrayList<>();

    protected Ticket() {
    }

    public Ticket(Long personaId) {
        this.personaId = personaId;
        this.fecha = Instant.now();
    }

    public void agregarLinea(String productoCodigo, String nombre, int cantidad, BigDecimal precioUnitario) {
        LineaTicket linea = new LineaTicket(this, productoCodigo, nombre, cantidad, precioUnitario);
        lineas.add(linea);
        totalUnidades += cantidad;
        total = total.add(linea.getSubtotal());
    }

    public Long getId() {
        return id;
    }

    public Long getPersonaId() {
        return personaId;
    }

    public Instant getFecha() {
        return fecha;
    }

    public int getTotalUnidades() {
        return totalUnidades;
    }

    public BigDecimal getTotal() {
        return total;
    }

    public List<LineaTicket> getLineas() {
        return lineas;
    }
}
