package com.hummus.backend.ticket;

import java.util.List;

import org.springframework.data.domain.Limit;
import org.springframework.data.jpa.repository.JpaRepository;

public interface TicketRepository extends JpaRepository<Ticket, Long> {

    /** Los más recientes primero. */
    List<Ticket> findByOrderByIdDesc(Limit limit);
}
