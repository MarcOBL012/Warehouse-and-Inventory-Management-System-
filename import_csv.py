import sqlite3
import pandas as pd
import os
from database import create_tables

DB_NAME = "inventario.db"

def reset_db():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    create_tables()

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def import_data():
    reset_db()
    conn = get_conn()
    cursor = conn.cursor()

    # 1. Insertar Tipos de Operación (Tabla 12)
    operaciones = [
        ('01', 'VENTA NACIONAL', 'EGRESO', 0),
        ('02', 'COMPRA NACIONAL', 'INGRESO', 1),
        ('11', 'SALIDA POR TRANSFERENCIA ENTRE ALMACENES', 'EGRESO', 0),
        ('11I', 'INGRESO POR TRANSFERENCIA ENTRE ALMACENES', 'INGRESO', 1), 
        ('16', 'SALDO INICIAL', 'INGRESO', 1),
        ('21', 'SALIDA POR DEVOLUCIÓN AL PROVEEDOR', 'EGRESO', 0),
        ('99', 'OTROS', 'NEUTRO', 0)
    ]
    cursor.executemany('''
        INSERT INTO TipoOperacion (codigo_sunat, descripcion, impacto, afecta_costo)
        VALUES (?, ?, ?, ?)
    ''', operaciones)
    
    # Mapeo de operaciones
    cursor.execute("SELECT id, codigo_sunat FROM TipoOperacion")
    op_map = {row['codigo_sunat']: row['id'] for row in cursor.fetchall()}

    # 2. Importar Artículos
    print("Importando Artículos...")
    df_articulos = pd.read_csv("sercoplus_articulos.csv")
    for _, row in df_articulos.iterrows():
        cursor.execute('''
            INSERT INTO Articulo (codigo_sunat, descripcion, unidad_medida, categoria)
            VALUES (?, ?, ?, ?)
        ''', (row['codigo_sunat'], row['descripcion'], row['unidad_medida'], row['categoria']))
    
    cursor.execute("SELECT id, codigo_sunat FROM Articulo")
    art_map = {row['codigo_sunat']: row['id'] for row in cursor.fetchall()}

    # 3. Importar Almacenes dinámicamente y Movimientos
    print("Importando Movimientos...")
    df_mov = pd.read_csv("sercoplus_movimientos.csv")
    
    # Identificar almacenes únicos
    almacenes_unicos = df_mov['nombre_almacen'].unique()
    for alm in almacenes_unicos:
        cursor.execute('INSERT INTO Almacen (nombre, ubicacion) VALUES (?, ?)', (alm, 'UBICACION DESCONOCIDA'))
    
    cursor.execute("SELECT id, nombre FROM Almacen")
    alm_map = {row['nombre']: row['id'] for row in cursor.fetchall()}

    # Insertar movimientos
    movimientos_data = []
    for _, row in df_mov.iterrows():
        # Formatear el código de operación para asegurar que es un string válido con ceros a la izquierda ('01', '02')
        op_sunat = str(row['codigo_operacion_sunat']).zfill(2)
        # Algunos CSV pandas parsean el '01' como 1
        
        # Validar tipo_documento (00, 01, 03)
        doc_type = str(row['tipo_documento']).zfill(2)
        
        movimientos_data.append((
            row['fecha'],
            art_map[row['codigo_articulo']],
            alm_map[row['nombre_almacen']],
            op_map[op_sunat],
            doc_type,
            str(row['num_documento']),
            float(row['cantidad']),
            float(row['costo_total']) / float(row['cantidad']) if float(row['cantidad']) > 0 and float(row['costo_total']) > 0 else 0.0,
            float(row['costo_total'])
        ))
        
    cursor.executemany('''
        INSERT INTO Movimiento (fecha, articulo_id, almacen_id, tipo_operacion_id, tipo_documento, num_documento, cantidad, costo_unitario, costo_total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', movimientos_data)

    conn.commit()
    conn.close()
    print("¡Importación Finalizada! Base de datos actualizada con los datos reales.")

if __name__ == "__main__":
    import_data()
