-- Catálogo de la demo. "codigo" es la clase que detecta YOLO (tiene que coincidir con
-- PRODUCTOS en vision/config.py). MERGE inserta o actualiza, así no falla al arrancar otra vez.
MERGE INTO producto (codigo, nombre, precio) KEY (codigo) VALUES
    -- Bebidas y menaje
    ('bottle', 'Agua Solán de cabras 1,5 L', 0.45),
    ('cup', 'Café con leche', 1.20),
    ('wine glass', 'Copa de vino', 1.50),
    ('bowl', 'Ensalada en bol', 2.10),
    -- Fruta y verdura
    ('banana', 'Plátano de Canarias', 0.35),
    ('apple', 'Manzana Golden', 0.40),
    ('orange', 'Naranja de zumo', 0.30),
    ('broccoli', 'Brócoli', 1.25),
    ('carrot', 'Zanahoria', 0.15),
    -- Comida preparada y bollería
    ('sandwich', 'Sándwich mixto', 1.80),
    ('hot dog', 'Perrito caliente', 1.50),
    ('pizza', 'Pizza barbacoa', 2.95),
    ('donut', 'Dónut glaseado', 0.90),
    ('cake', 'Tarta de queso', 4.50),
    -- Droguería
    ('toothbrush', 'Cepillo de dientes', 1.20);

--Commit para MVP 1.0
