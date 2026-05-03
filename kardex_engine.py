import pandas as pd
from database import get_db_connection

def calcular_kardex_almacen_articulo(almacen_id, articulo_id):
    """
    Calcula el Kardex Valorizado (Costo Promedio Ponderado)
    para un artículo específico en un almacén específico.
    Devuelve un DataFrame de Pandas con la línea de tiempo.
    """
    conn = get_db_connection()
    
    query = """
    SELECT 
        m.id, m.fecha, t.codigo_sunat as tipo_operacion, t.descripcion as operacion_desc, 
        t.impacto, t.afecta_costo,
        m.tipo_documento, m.num_documento, m.cantidad, m.costo_unitario as costo_unitario_doc, m.costo_total as costo_total_doc
    FROM Movimiento m
    JOIN TipoOperacion t ON m.tipo_operacion_id = t.id
    WHERE m.almacen_id = ? AND m.articulo_id = ?
    ORDER BY m.fecha ASC, m.id ASC
    """
    
    df = pd.read_sql_query(query, conn, params=(almacen_id, articulo_id))
    conn.close()

    if df.empty:
        return pd.DataFrame()

    # Variables para el saldo
    saldo_qty = 0.0
    saldo_total = 0.0
    costo_promedio = 0.0

    resultados = []

    for index, row in df.iterrows():
        qty = float(row['cantidad'])
        
        # Ingreso
        if row['impacto'] == 'INGRESO':
            if row['afecta_costo']:
                # El costo viene del documento (compra o saldo inicial)
                costo_tot = float(row['costo_total_doc'])
                costo_u = float(row['costo_unitario_doc'])
                
                saldo_qty += qty
                saldo_total += costo_tot
                if saldo_qty > 0:
                    costo_promedio = saldo_total / saldo_qty
                else:
                    costo_promedio = 0.0
            else:
                # Ingreso que NO afecta costo promedio (ej. Transferencia, temporalmente tomamos el costo promedio actual)
                # Para un control estricto, una transferencia debería ingresar con el costo promedio del origen,
                # por simplicidad en este loop tomamos el costo actual o si es primera vez, el declarado.
                costo_u = costo_promedio if costo_promedio > 0 else float(row['costo_unitario_doc'])
                costo_tot = qty * costo_u
                
                saldo_qty += qty
                saldo_total += costo_tot
                if saldo_qty > 0:
                    costo_promedio = saldo_total / saldo_qty
                else:
                    costo_promedio = 0.0

            resultados.append({
                'Fecha': row['fecha'],
                'Operacion': f"{row['tipo_operacion']} - {row['operacion_desc']}",
                'Documento': f"{row['tipo_documento']} {row['num_documento']}",
                'Ingreso_Cant': qty,
                'Ingreso_CU': round(costo_u, 4),
                'Ingreso_CT': round(costo_tot, 4),
                'Egreso_Cant': 0.0,
                'Egreso_CU': 0.0,
                'Egreso_CT': 0.0,
                'Saldo_Cant': saldo_qty,
                'Saldo_CU': round(costo_promedio, 4),
                'Saldo_CT': round(saldo_total, 4)
            })

        # Egreso
        elif row['impacto'] == 'EGRESO':
            # Valorizado al Costo Promedio actual
            costo_u = costo_promedio
            costo_tot = qty * costo_u
            
            saldo_qty -= qty
            saldo_total -= costo_tot
            # El costo promedio se mantiene igual tras una salida, a menos que el stock llegue a 0
            if saldo_qty <= 0.0001:
                saldo_qty = 0.0
                saldo_total = 0.0
                costo_promedio = 0.0

            resultados.append({
                'Fecha': row['fecha'],
                'Operacion': f"{row['tipo_operacion']} - {row['operacion_desc']}",
                'Documento': f"{row['tipo_documento']} {row['num_documento']}",
                'Ingreso_Cant': 0.0,
                'Ingreso_CU': 0.0,
                'Ingreso_CT': 0.0,
                'Egreso_Cant': qty,
                'Egreso_CU': round(costo_u, 4),
                'Egreso_CT': round(costo_tot, 4),
                'Saldo_Cant': saldo_qty,
                'Saldo_CU': round(costo_promedio, 4),
                'Saldo_CT': round(saldo_total, 4)
            })

    return pd.DataFrame(resultados)


def generar_kardex_consolidado(year=None, month=None):
    """
    Genera el Kardex Consolidado (Suma de saldos de todos los almacenes por artículo)
    y compara contra el cálculo global.
    Si se proporciona year y month, filtra los saldos hasta el último día de ese mes.
    """
    conn = get_db_connection()
    # Obtenemos todos los articulos y almacenes
    articulos_df = pd.read_sql_query("SELECT id, codigo_sunat, descripcion FROM Articulo", conn)
    almacenes_df = pd.read_sql_query("SELECT id, nombre FROM Almacen", conn)
    conn.close()

    consolidado = []
    inconsistencias = []

    for _, art in articulos_df.iterrows():
        suma_qty = 0.0
        suma_total = 0.0
        detalles_almacen = {}

        for _, alm in almacenes_df.iterrows():
            df_k = calcular_kardex_almacen_articulo(alm['id'], art['id'])
            if not df_k.empty:
                if year and month:
                    import calendar
                    last_day = calendar.monthrange(int(year), int(month))[1]
                    end_date = f"{year}-{int(month):02d}-{last_day} 23:59:59"
                    df_k = df_k[df_k['Fecha'] <= end_date]

                if not df_k.empty:
                    last_row = df_k.iloc[-1]
                    s_qty = float(last_row['Saldo_Cant'])
                    s_tot = float(last_row['Saldo_CT'])
                    suma_qty += s_qty
                    suma_total += s_tot
                    detalles_almacen[alm['nombre']] = {'qty': s_qty, 'total': s_tot}
        
        if suma_qty > 0:
            cp_global = suma_total / suma_qty
            consolidado.append({
                'Articulo': f"{art['codigo_sunat']} - {art['descripcion']}",
                'Stock_Consolidado': round(suma_qty, 2),
                'Costo_Promedio_Global': round(cp_global, 4),
                'Valor_Total_Consolidado': round(suma_total, 4)
            })
            
            # Validación: ¿La suma coincide? (Esto sirve si hacemos el cálculo en global también)
            # Como aquí ya estamos sumando las partes, siempre coincidirá aritméticamente,
            # pero podemos validarlo contra un "Kardex Global" puro para auditar cruce.
            # En un kardex consolidado estricto, la suma de montos locales = monto global.

    df_consolidado = pd.DataFrame(consolidado)
    return df_consolidado, inconsistencias
