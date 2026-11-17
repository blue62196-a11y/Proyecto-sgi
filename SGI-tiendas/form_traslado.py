import streamlit as st
import pandas as pd
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

class ErrorNegocio(Exception):
    pass

def _dec(valor):
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def registrar_traslado(conn, id_tienda_origen, id_tienda_destino, id_usuario, lineas):
    if not lineas:
        raise ErrorNegocio("El traslado no tiene productos.")
    if id_tienda_origen == id_tienda_destino:
        raise ErrorNegocio("La tienda de origen y destino no pueden ser la misma.")

    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        # 1. Crear el encabezado del traslado
        cur.execute(
            "INSERT INTO traslado (ID_Tienda_Origen, ID_Tienda_Destino, ID_Usuario, Fecha_Traslado, Estado_Traslado) VALUES (%s, %s, %s, CURDATE(), 'COMPLETADO')",
            (id_tienda_origen, id_tienda_destino, id_usuario)
        )
        id_traslado = cur.lastrowid

        # 2. Procesar cada producto
        for l in lineas:
            cantidad = _dec(l["cantidad"])
            id_prod = l["id_producto"]
            
            cur.execute(
                "SELECT SUM(Existencias) as Total_Stock FROM inventario WHERE ID_Tienda = %s AND ID_Producto = %s",
                (id_tienda_origen, id_prod)
            )
            stock_actual = cur.fetchone()["Total_Stock"] or 0
            
            if _dec(stock_actual) < cantidad:
                raise ErrorNegocio(f"No hay suficiente stock de {l['nombre']} para trasladar. Disponibles: {stock_actual}")

            # Detalle del traslado
            cur.execute(
                "INSERT INTO detalle_traslado (ID_Traslado, ID_Producto, Cantidad) VALUES (%s, %s, %s)",
                (id_traslado, id_prod, cantidad)
            )

            # Restar del inventario de origen
            cur.execute(
                """UPDATE inventario SET Existencias = Existencias - %s 
                   WHERE ID_Tienda = %s AND ID_Producto = %s LIMIT 1""",
                (cantidad, id_tienda_origen, id_prod)
            )

            # Sumar al inventario de destino
            cur.execute(
                """INSERT INTO inventario (ID_Tienda, ID_Producto, Fecha_Vencimiento, Existencias)
                   VALUES (%s, %s, '9999-12-31', %s)
                   ON DUPLICATE KEY UPDATE Existencias = Existencias + VALUES(Existencias)""",
                (id_tienda_destino, id_prod, cantidad)
            )

        conn.commit()
        return id_traslado
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def _consultar(get_connection, sql, params=()):
    conn = get_connection()
    if conn is None: return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.
