import streamlit as st

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

def registrar_merma(conn, id_tienda, id_producto, cantidad, motivo, id_usuario):
    cur = conn.cursor()
    try:
        conn.start_transaction()
        # Restamos del inventario
        cur.execute(
            "UPDATE inventario SET Existencias = Existencias - %s WHERE ID_Tienda = %s AND ID_Producto = %s",
            (cantidad, id_tienda, id_producto)
        )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()

def pantalla_registrar_merma(get_connection):
    st.title("🗑️ Ajustes y Mermas de Inventario")
    st.markdown("Registro de salidas por daños, vencimientos o discrepancias de auditoría.")

    id_tienda = st.session_state.id_tienda
    id_usuario = st.session_state.id_usuario

    productos = _consultar(
        get_connection,
        "SELECT P.ID_Producto, P.Cod_Producto, P.Nombre, I.Existencias FROM inventario I JOIN producto P ON I.ID_Producto = P.ID_Producto WHERE I.ID_Tienda = %s AND I.Existencias > 0",
        (id_tienda,)
    )

    if not productos:
        st.warning("No hay productos con existencias en esta tienda para registrar mermas.")
        return

    with st.form("form_merma"):
        prod_opts = {f"{p['Cod_Producto']} - {p['Nombre']} (Disp: {p['Existencias']})": p for p in productos}
        prod_label = st.selectbox("Seleccionar Producto Dañado/Perdido", list(prod_opts.keys()))
        prod_seleccionado = prod_opts[prod_label]

        col1, col2 = st.columns(2)
        cantidad = col1.number_input("Cantidad a dar de baja", min_value=1, max_value=int(prod_seleccionado['Existencias']), step=1)
        motivo = col2.selectbox("Motivo del Ajuste", ["Producto Defectuoso", "Vencimiento", "Daño en Almacén", "Extravío / Discrepancia"])

        if st.form_submit_button("Confirmar Merma", type="primary"):
            conn = get_connection()
            if conn:
                try:
                    registrar_merma(conn, id_tienda, prod_seleccionado["ID_Producto"], cantidad, motivo, id_usuario)
                    st.success(f"Se dieron de baja {cantidad} unidades de {prod_seleccionado['Nombre']} por {motivo}.")
                except Exception as e:
                    st.error(f"Error al procesar el ajuste: {e}")
                finally:
                    conn.close()
