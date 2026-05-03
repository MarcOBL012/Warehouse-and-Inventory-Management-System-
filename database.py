import sqlite3
import os

DB_NAME = "inventario.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Tabla 12 SUNAT - Tipos de Operación
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS TipoOperacion (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_sunat TEXT UNIQUE NOT NULL,
        descripcion TEXT NOT NULL,
        impacto TEXT NOT NULL, -- 'INGRESO', 'EGRESO', 'NEUTRO'
        afecta_costo BOOLEAN NOT NULL -- 1 si afecta promedio, 0 si no
    )
    """)

    # Almacenes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Almacen (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL,
        ubicacion TEXT
    )
    """)

    # Articulos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Articulo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_sunat TEXT UNIQUE NOT NULL,
        descripcion TEXT NOT NULL,
        unidad_medida TEXT NOT NULL,
        categoria TEXT
    )
    """)

    # Movimientos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Movimiento (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha DATETIME NOT NULL,
        articulo_id INTEGER NOT NULL,
        almacen_id INTEGER NOT NULL,
        tipo_operacion_id INTEGER NOT NULL,
        tipo_documento TEXT,
        num_documento TEXT,
        cantidad REAL NOT NULL,
        costo_unitario REAL NOT NULL,
        costo_total REAL NOT NULL,
        notas TEXT,
        FOREIGN KEY (articulo_id) REFERENCES Articulo(id),
        FOREIGN KEY (almacen_id) REFERENCES Almacen(id),
        FOREIGN KEY (tipo_operacion_id) REFERENCES TipoOperacion(id)
    )
    """)

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()
    print("Tablas creadas exitosamente.")
