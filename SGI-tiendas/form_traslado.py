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
            # Si agregaste la columna a la BD, puedes incluir l['precio'] en el INSERT de abajo
            
            cur.execute(
                "SELECT SUM(Existencias) as Total_Stock FROM inventario WHERE ID_Tienda = %s AND ID_Producto = %s",
                (id_tienda_origen, id_prod)
            )
            stock_actual = cur.fetchone()["Total_Stock"] or 0
            
            if _dec(stock_actual) < cantidad:
                raise ErrorNegocio(f"No hay suficiente stock de {l['nombre']} para trasladar. Disponibles: {stock_actual}")

            # Detalle del traslado (OJO: si creas la columna Costo_Unitario en tu BD, agrégala aquí)
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
        return cur.fetchall()
    finally:
        conn.close()

def pantalla_registrar_traslado(get_connection):
    st.title("🚚 Registrar Traslado (Venta Interna)")
    st.markdown("Envía inventario a otra sucursal registrando el costo del producto.")

    id_tienda = st.session_state.id_tienda
    id_usuario = st.session_state.id_usuario

    if "traslado_ok" in st.session_state:
        st.success(st.session_state.pop("traslado_ok"))
    if "carrito_traslado" not in st.session_state:
        st.session_state.carrito_traslado = []

    tiendas = _consultar(get_connection, "SELECT ID_Tienda, Nombre FROM tienda WHERE ID_Tienda != %s", (id_tienda,))
    if not tiendas:
        st.info("No hay otras tiendas registradas para realizar traslados.")
        return
        
    tiendas_opts = {t["Nombre"]: t["ID_Tienda"] for t in tiendas}
    destino_label = st.selectbox("Tienda Destino (Cliente Interno)", list(tiendas_opts.keys()))
    id_destino = tiendas_opts[destino_label]

    productos_disp = _consultar(
        get_connection,
        """SELECT P.ID_Producto, P.Cod_Producto, P.Nombre, SUM(I.Existencias) as Disp 
           FROM inventario I 
           JOIN producto P ON I.ID_Producto = P.ID_Producto 
           WHERE I.ID_Tienda = %s AND I.Existencias > 0 
           GROUP BY P.ID_Producto""",
        (id_tienda,)
    )

    if not productos_disp:
        st.warning("Tu tienda/CD no tiene productos con existencias para trasladar.")
        return

    st.subheader("Productos a enviar")
    prod_opts = {f"{p['Cod_Producto']} · {p['Nombre']} (Disp: {p['Disp']})": p for p in productos_disp}
    
    col1, col2, col3, col4 = st.columns([3, 1, 2, 2])
    prod_label = col1.selectbox("Producto", list(prod_opts.keys()))
    prod_seleccionado = prod_opts[prod_label]
    
    cantidad = col2.number_input("Cantidad", min_value=1, max_value=int(prod_seleccionado['Disp']), value=1, step=1)
    precio_costo = col3.number_input("Costo Unitario ($)", min_value=0.01, value=1.00, step=0.01)

    if col4.button("➕ Agregar a la nota", use_container_width=True):
        subtotal = float(cantidad) * float(precio_costo)
        linea = {
            "id_producto": prod_seleccionado["ID_Producto"],
            "nombre": prod_seleccionado["Nombre"],
            "cantidad": cantidad,
            "precio": precio_costo,
            "subtotal": subtotal
        }
        st.session_state.carrito_traslado.append(linea)
        st.rerun()

    carrito = st.session_state.carrito_traslado
    if carrito:
        filas = [{"#": i + 1, "Producto": l["nombre"], "Cantidad": l["cantidad"], "Costo Unit.": f"${l['precio']:.2f}", "Subtotal": f"${l['subtotal']:.2f}"} for i, l in enumerate(carrito)]
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
        
        total_traslado = sum(l["subtotal"] for l in carrito)
        st.markdown(f"### Valor Total del Traslado: **${total_traslado:.2f}**")

        if st.button("Vaciar lista"):
            st.session_state.carrito_traslado = []
            st.rerun()

        if st.button("✅ Confirmar Traslado", type="primary"):
            conn = get_connection()
            if conn:
                try:
                    id_traslado = registrar_traslado(conn, id_tienda, id_destino, id_usuario, carrito)
                    st.session_state.carrito_traslado = []
                    st.session_state.traslado_ok = f"Traslado #{id_traslado} enviado con éxito a {destino_label} por un valor de ${total_traslado:.2f}."
                    st.rerun()
                except ErrorNegocio as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error al procesar el traslado: {e}")
                finally:
                    conn.close()
