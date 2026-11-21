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
        cur.execute(
            "UPDATE inventario SET Existencias = Existencias - %s "
            "WHERE ID_Tienda = %s AND ID_Producto = %s AND Existencias >= %s",
            (cantidad, id_tienda, id_producto, cantidad)
        )
        if cur.rowcount == 0:
            raise ValueError("Existencias insuficientes.")

        # Si tienes tabla de mermas/movimientos, registra aquí motivo y usuario:
        # cur.execute(
        #     "INSERT INTO merma (ID_Tienda, ID_Producto, Cantidad, Motivo, ID_Usuario, Fecha) "
        #     "VALUES (%s, %s, %s, %s, %s, NOW())",
        #     (id_tienda, id_producto, cantidad, motivo, id_usuario)
        # )

        conn.commit()
        return True
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def pantalla_registrar_merma(get_connection):
    st.title("🗑️ Ajustes y Mermas de Inventario")
    st.markdown("Registro de salidas por daños, vencimientos o discrepancias de auditoría.")

    id_tienda = st.session_state.id_tienda
    id_usuario = st.session_state.id_usuario

    # Mensaje de éxito que sobrevive a la recarga
    if "merma_ok" in st.session_state:
        st.success(st.session_state.pop("merma_ok"))

    productos = _consultar(
        get_connection,
        "SELECT P.ID_Producto, P.Cod_Producto, P.Nombre, I.Existencias "
        "FROM inventario I JOIN producto P ON I.ID_Producto = P.ID_Producto "
        "WHERE I.ID_Tienda = %s AND I.Existencias > 0",
        (id_tienda,)
    )

    if not productos:
        st.warning("No hay productos con existencias en esta tienda para registrar mermas.")
        return

    por_id = {p["ID_Producto"]: p for p in productos}

    with st.form("form_merma"):
        id_sel = st.selectbox(
            "Seleccionar Producto Dañado/Perdido",
            options=list(por_id.keys()),
            format_func=lambda i: f"{por_id[i]['Cod_Producto']} - {por_id[i]['Nombre']} (Disp: {por_id[i]['Existencias']})",
            key="merma_producto",
        )

        col1, col2 = st.columns(2)
        cantidad = col1.number_input(
            "Cantidad a dar de baja", min_value=1, step=1, value=1, key="merma_cantidad"
        )
        motivo = col2.selectbox(
            "Motivo del Ajuste",
            ["Producto Defectuoso", "Vencimiento", "Daño en Almacén", "Extravío / Discrepancia"],
            key="merma_motivo",
        )

        enviado = st.form_submit_button("Confirmar Merma", type="primary")

    if enviado:
        prod = por_id[id_sel]
        if cantidad > int(prod["Existencias"]):
            st.error(f"La cantidad supera las existencias disponibles ({prod['Existencias']}).")
            return
        conn = get_connection()
        if conn:
            try:
                registrar_merma(conn, id_tienda, prod["ID_Producto"], cantidad, motivo, id_usuario)
                st.session_state["merma_ok"] = (
                    f"Se dieron de baja {cantidad} unidades de {prod['Nombre']} por {motivo}."
                )
            except Exception as e:
                st.error(f"Error al procesar el ajuste: {e}")
            else:
                conn.close()
                st.rerun()  # recarga para que el "Disp:" se actualice
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
