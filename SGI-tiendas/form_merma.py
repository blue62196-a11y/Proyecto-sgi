import streamlit as st
from datetime import date

SIN_VENCIMIENTO = date(9999, 12, 31)


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


def registrar_merma(conn, id_inventario, id_tienda, cantidad, motivo):
    cur = conn.cursor()
    try:
        conn.start_transaction()
        cur.execute(
            """UPDATE inventario
               SET Existencias = Existencias - %s,
                   Cantidad_Merma = COALESCE(Cantidad_Merma, 0) + %s,
                   Motivo_Merma = %s,
                   Fecha_Ultima_Merma = NOW()
               WHERE ID_Inventario = %s
                 AND ID_Tienda = %s
                 AND Existencias >= %s""",
            (cantidad, cantidad, motivo, id_inventario, id_tienda, cantidad)
        )
        if cur.rowcount == 0:
            raise ValueError("Existencias insuficientes en el lote seleccionado.")

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

    if "merma_ok" in st.session_state:
        st.success(st.session_state.pop("merma_ok"))

    lotes = _consultar(
        get_connection,
        """SELECT I.ID_Inventario, P.ID_Producto, P.Cod_Producto, P.Nombre,
                  I.Fecha_Vencimiento, I.Existencias
           FROM inventario I
           JOIN producto P ON I.ID_Producto = P.ID_Producto
           WHERE I.ID_Tienda = %s AND I.Existencias > 0
           ORDER BY P.Nombre ASC, I.Fecha_Vencimiento ASC""",
        (id_tienda,)
    )

    if not lotes:
        st.warning("No hay productos con existencias en esta tienda para registrar mermas.")
        return

    por_lote = {l["ID_Inventario"]: l for l in lotes}

    def _etiqueta_lote(id_inv):
        l = por_lote[id_inv]
        venc = "Sin vencimiento" if l["Fecha_Vencimiento"] == SIN_VENCIMIENTO else str(l["Fecha_Vencimiento"])
        return f"{l['Cod_Producto']} - {l['Nombre']} (Lote vence: {venc})"

    id_sel = st.selectbox(
        "Seleccionar Lote / Producto Dañado o Perdido",
        options=list(por_lote.keys()),
        format_func=_etiqueta_lote,
        key="merma_lote",
    )
    lote = por_lote[id_sel]
    st.caption(f"Existencias disponibles en este lote: {lote['Existencias']}")

    with st.form("form_merma"):
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
        if cantidad > float(lote["Existencias"]):
            st.error(f"La cantidad supera las existencias disponibles ({lote['Existencias']}).")
            return
        conn = get_connection()
        if conn:
            try:
                registrar_merma(conn, lote["ID_Inventario"], id_tienda, cantidad, motivo)
                st.cache_data.clear()
                st.session_state["merma_ok"] = (
                    f"Se dieron de baja {cantidad} unidad(es) de {lote['Nombre']} por {motivo}."
                )
                exito = True
            except Exception as e:
                exito = False
                st.error(f"Error al procesar el ajuste: {e}")
            finally:
                conn.close()
            if exito:
                st.rerun()
