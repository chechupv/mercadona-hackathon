package com.hummus.backend.carrito;

import com.hummus.backend.producto.Producto;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;

/** Una fila del carrito: cuántas unidades de un producto lleva una persona. */
@Entity
@Table(uniqueConstraints = @UniqueConstraint(columnNames = { "persona_id", "producto_codigo" }))
public class LineaCarrito {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "persona_id", nullable = false)
    private Long personaId;

    @ManyToOne(optional = false)
    @JoinColumn(name = "producto_codigo")
    private Producto producto;

    @Column(nullable = false)
    private int cantidad;

    protected LineaCarrito() {
    }

    public LineaCarrito(Long personaId, Producto producto) {
        this.personaId = personaId;
        this.producto = producto;
    }

    public void sumar() {
        cantidad++;
    }

    public void restar() {
        cantidad--;
    }

    public Long getId() {
        return id;
    }

    public Long getPersonaId() {
        return personaId;
    }

    public Producto getProducto() {
        return producto;
    }

    public int getCantidad() {
        return cantidad;
    }
}
