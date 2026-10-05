-- Catálogo de la demo. "codigo" es la clase que detecta YOLO.
-- MERGE inserta o actualiza, así no falla al arrancar otra vez.
MERGE INTO producto (codigo, nombre, precio) KEY (codigo) VALUES
    ('bottle', 'Agua Bronchales 1,5 L', 0.45),
    ('cup', 'Café con leche', 1.20);
