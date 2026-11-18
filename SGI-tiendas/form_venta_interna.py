import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

class ErrorNegocio(Exception): pass

def _dec(valor):
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def registrar_venta_interna(conn, id_cd, id_tienda_destino, id_usuario, lineas):
    if not lineas: raise ErrorNegocio("No hay productos en la nota.")
    
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        
        # 1. Crear el traslado en estado "EN TRANSITO"
        cur.execute(
            "INSERT INTO traslado (ID_Tienda_Origen, ID_Tienda_Destino, ID_Usuario, Fecha_Traslado, Estado_Traslado) VALUES (%s, %s, %s, CURDATE(), 'EN TRANSITO')",
            (id_cd, id_tienda_destino, id_usuario)
        )
        id_traslado = cur.lastrowid

        # 2. Registrar venta del CD a precio de costo (simulada o real según tu BD)
        cur.execute(
            "INSERT INTO venta (ID_Tienda, ID_Usuario, Fecha_Venta, Total_Venta) VALUES (%s, %s, CURDATE(), %s)",
            (id_cd, id_usuario, sum(l['subtotal'] for l in lineas))
        )
        id_venta = cur.lastrowid

        for l in lineas:
            cantidad, costo = _dec(l["cantidad"]), _dec(l["costo"])
            id_prod = l["id_producto"]
            
            # Verificar stock en CD
            cur.execute("SELECT SUM(Existencias) as Disp FROM inventario WHERE ID_Tienda = %s AND ID_Producto = %s", (id_cd, id_prod))
            disp = cur.fetchone()["Disp"] or 0
            if _dec(disp) < cantidad:
                raise ErrorNegocio(f"Stock insuficiente para {l['nombre']}. Hay {disp}.")

            # Detalle traslado
            cur.execute("INSERT INTO detalle_traslado (ID_Traslado, ID_Producto, Cantidad) VALUES (%s, %s, %s)", (id_traslado, id_prod, cantidad))
            
            # Detalle venta interna (al costo)
            cur.execute("INSERT INTO detalle_venta (ID_Venta, ID_Producto, Cantidad, Precio_Unitario, Subtotal) VALUES (%s, %s, %s, %s, %s)",
                        (id_venta, id_prod, cantidad, costo, cantidad * costo))

            # Restar del inventario del CD (Pero NO sumamos a la tienda destino aún)
            cur.execute("UPDATE inventario SET Existencias = Existencias - %s WHERE ID_Tienda = %s AND ID_Producto = %s LIMIT 1", (cantidad, id_cd, id_prod))

        conn.commit()
        return id_traslado, id_venta
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def _consultar(get_connection, sql, params=()):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor(dictionary=True)
            cur.execute(sql, params)
            return cur.fetchall()
        finally:
            conn.close()
    return []

def pantalla_venta_interna(get_connection):
    st.title("🚚 Despacho CD (Venta Interna)")
    st.markdown("Envía productos a sucursales en estado 'En Tránsito'.")

    id_tienda = st.session_state.id_tienda
    
    # Solo permitir acceso si es el CD (asumiendo que el CD tiene un ID específico, ej. 1)
    # Si tienes una bandera en BD, puedes validarlo aquí.
    
    tiendas = _consultar(get_connection, "SELECT ID_Tienda, Nombre FROM tienda WHERE ID_Tienda != %s", (id_tienda,))
    if not tiendas: return st.warning("No hay sucursales destino.")
    
    tiendas_opts = {t["Nombre"]: t["ID_Tienda"] for t in tiendas}
    id_destino = tiendas_opts[st.selectbox("Tienda Destino", list(tiendas_opts.keys()))]

    productos = _consultar(get_connection, "SELECT P.ID_Producto, P.Cod_Producto, P.Nombre, SUM(I.Existencias) as Disp FROM inventario I JOIN producto P ON I.ID_Producto = P.ID_Producto WHERE I.ID_Tienda = %s AND I.Existencias > 0 GROUP BY P.ID_Producto", (id_tienda,))
    
    if not productos: return st.info("No hay inventario en el CD.")

    if "carrito_vi" not in st.session_state: st.session_state.carrito_vi = []

    prod_opts = {f"{p['Cod_Producto']} - {p['Nombre']} (Disp: {p['Disp']})": p for p in productos}
    c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
    prod_sel = prod_opts[c1.selectbox("Producto", list(prod_opts.keys()))]
    cantidad = c2.number_input("Cant.", min_value=1, value=1)
    costo = c3.number_input("Costo $", min_value=0.01, value=1.00)

    if c4.button("➕ Agregar al despacho", use_container_width=True):
        if cantidad > int(prod_sel['Disp']):
            st.error("Excede el stock disponible.")
        else:
            st.session_state.carrito_vi.append({
                "id_producto": prod_sel["ID_Producto"], "nombre": prod_sel["Nombre"],
                "cantidad": cantidad, "costo": costo, "subtotal": float(cantidad)*float(costo)
            })
            st.rerun()

    if st.session_state.carrito_vi:
        st.dataframe(pd.DataFrame(st.session_state.carrito_vi), use_container_width=True)
        if st.button("✅ Confirmar Salida de CD", type="primary"):
            try:
                id_t, id_v = registrar_venta_interna(get_connection(), id_tienda, id_destino, st.session_state.id_usuario, st.session_state.carrito_vi)
                st.success(f"Despacho exitoso. Traslado #{id_t} en tránsito.")
                st.session_state.carrito_vi = []
            except ErrorNegocio as e:
                st.error(str(e))
