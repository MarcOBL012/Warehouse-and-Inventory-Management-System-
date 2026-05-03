import sqlite3
import random
from datetime import datetime, timedelta
from database import create_tables, get_db_connection

def seed():
    create_tables()
    conn = get_db_connection()
    cursor = conn.cursor()

    # --- 1. Tipos de Operación (Tabla 12 SUNAT) ---
    operaciones = [
        ('01', 'VENTA NACIONAL', 'EGRESO', 0),
        ('02', 'COMPRA NACIONAL', 'INGRESO', 1),
        ('11', 'SALIDA POR TRANSFERENCIA ENTRE ALMACENES', 'EGRESO', 0),
        ('11I', 'INGRESO POR TRANSFERENCIA ENTRE ALMACENES', 'INGRESO', 1), 
        ('16', 'SALDO INICIAL', 'INGRESO', 1),
        ('21', 'SALIDA POR DEVOLUCIÓN AL PROVEEDOR', 'EGRESO', 0),
        ('99', 'OTROS', 'NEUTRO', 0)
    ]
    for op in operaciones:
        cursor.execute('''
            INSERT OR IGNORE INTO TipoOperacion (codigo_sunat, descripcion, impacto, afecta_costo)
            VALUES (?, ?, ?, ?)
        ''', op)
    
    # Obtener IDs de operaciones
    cursor.execute("SELECT id, codigo_sunat FROM TipoOperacion")
    op_ids = {row['codigo_sunat']: row['id'] for row in cursor.fetchall()}

    # --- 2. Almacenes ---
    almacenes = [
        ('ALMACEN PRINCIPAL', 'LIMA - CENTRO'),
        ('ALMACEN NORTE', 'PIURA'),
        ('ALMACEN SUR', 'AREQUIPA')
    ]
    for alm in almacenes:
        cursor.execute('INSERT INTO Almacen (nombre, ubicacion) VALUES (?, ?)', alm)
    
    cursor.execute("SELECT id FROM Almacen")
    almacen_ids = [row['id'] for row in cursor.fetchall()]

    # --- 3. Artículos ---
    articulos = [
        ('ART001', 'LAPTOP LENOVO THINKPAD', 'UND', 'EQUIPOS'),
        ('ART002', 'MONITOR DELL 24"', 'UND', 'PERIFERICOS'),
        ('ART003', 'TECLADO MECANICO LOGITECH', 'UND', 'PERIFERICOS'),
        ('ART004', 'MOUSE INALAMBRICO', 'UND', 'PERIFERICOS'),
        ('ART005', 'IMPRESORA EPSON ECOTANK', 'UND', 'EQUIPOS'),
        ('ART006', 'TINTA NEGRA EPSON 664', 'LIT', 'SUMINISTROS'),
        ('ART007', 'PAPEL BOND A4 MILLAR', 'MIL', 'SUMINISTROS'),
        ('ART008', 'CABLE HDMI 2M', 'UND', 'CABLES'),
        ('ART009', 'DISCO DURO EXTERNO 1TB', 'UND', 'ALMACENAMIENTO'),
        ('ART010', 'MEMORIA RAM 16GB DDR4', 'UND', 'COMPONENTES')
    ]
    for art in articulos:
        cursor.execute('''
            INSERT OR IGNORE INTO Articulo (codigo_sunat, descripcion, unidad_medida, categoria)
            VALUES (?, ?, ?, ?)
        ''', art)
    
    cursor.execute("SELECT id FROM Articulo")
    articulo_ids = [row['id'] for row in cursor.fetchall()]

    # --- 4. Movimientos (Generación de 1 mes: Mayo 2026) ---
    start_date = datetime(2026, 5, 1)
    
    # 4.1 Saldos Iniciales (Día 1)
    for art_id in articulo_ids:
        for alm_id in almacen_ids:
            cantidad = random.randint(10, 50)
            costo_u = random.uniform(50.0, 500.0)
            costo_t = cantidad * costo_u
            cursor.execute('''
                INSERT INTO Movimiento (fecha, articulo_id, almacen_id, tipo_operacion_id, tipo_documento, num_documento, cantidad, costo_unitario, costo_total, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (start_date.strftime('%Y-%m-%d %H:%M:%S'), art_id, alm_id, op_ids['16'], '00', '0000', cantidad, costo_u, costo_t, 'Carga Inicial'))

    # Para hacer que la generación de movimientos tenga un costo razonable para los egresos, 
    # simplificaremos la simulación usando costos aleatorios cercanos, ya que el motor de Kardex 
    # recalculará los verdaderos costos promedio al momento de generar el reporte.
    # Es decir, la BD guardará los costos de "compras" reales, y para ventas el motor tomará los generados 
    # pero a nivel DB pondremos un valor placeholder o estimado que el motor sobreescribirá en tiempo real.
    
    # 4.2 Movimientos Diarios
    for day in range(2, 31):
        current_date = start_date + timedelta(days=day-1)
        
        # 2 a 5 movimientos por día
        for _ in range(random.randint(2, 5)):
            art_id = random.choice(articulo_ids)
            alm_id = random.choice(almacen_ids)
            op_code = random.choice(['01', '02', '11']) # Venta, Compra, Transferencia Salida
            
            hora = current_date.replace(hour=random.randint(8, 18), minute=random.randint(0, 59))
            fecha_str = hora.strftime('%Y-%m-%d %H:%M:%S')
            
            if op_code == '02': # Compra
                cant = random.randint(5, 20)
                costo_u = random.uniform(50.0, 500.0) # Precio mercado
                cursor.execute('''
                    INSERT INTO Movimiento (fecha, articulo_id, almacen_id, tipo_operacion_id, tipo_documento, num_documento, cantidad, costo_unitario, costo_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (fecha_str, art_id, alm_id, op_ids['02'], '01', f'F001-{random.randint(1000,9999)}', cant, costo_u, cant*costo_u))
                
            elif op_code == '01': # Venta
                cant = random.randint(1, 10)
                cursor.execute('''
                    INSERT INTO Movimiento (fecha, articulo_id, almacen_id, tipo_operacion_id, tipo_documento, num_documento, cantidad, costo_unitario, costo_total)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (fecha_str, art_id, alm_id, op_ids['01'], '03', f'B001-{random.randint(1000,9999)}', cant, 0.0, 0.0)) # Costo se calcula en Kardex
                
            elif op_code == '11': # Transferencia
                cant = random.randint(1, 5)
                # Almacén destino distinto
                alm_dest_id = random.choice([a for a in almacen_ids if a != alm_id])
                
                # Salida del origen
                cursor.execute('''
                    INSERT INTO Movimiento (fecha, articulo_id, almacen_id, tipo_operacion_id, tipo_documento, num_documento, cantidad, costo_unitario, costo_total, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (fecha_str, art_id, alm_id, op_ids['11'], '09', f'GR-{random.randint(1000,9999)}', cant, 0.0, 0.0, f'Hacia Almacen {alm_dest_id}'))
                
                # Ingreso al destino (1 segundo despues)
                fecha_dest = (hora + timedelta(seconds=1)).strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    INSERT INTO Movimiento (fecha, articulo_id, almacen_id, tipo_operacion_id, tipo_documento, num_documento, cantidad, costo_unitario, costo_total, notas)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (fecha_dest, art_id, alm_dest_id, op_ids['11I'], '09', f'GR-{random.randint(1000,9999)}', cant, 0.0, 0.0, f'Desde Almacen {alm_id}'))

    conn.commit()
    conn.close()
    print("Datos semilla insertados correctamente.")

if __name__ == "__main__":
    seed()
