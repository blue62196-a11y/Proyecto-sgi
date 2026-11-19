import streamlit as st
import pandas as pd
from decimal import Decimal, ROUND_HALF_UP

class ErrorNegocio(Exception):
    pass

def _dec(valor):
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def registrar_venta_interna(conn, id_cd, id_tienda_destino, id_usuario, lineas):
    if not lineas:
        raise ErrorNegocio("No hay productos en la nota.")

    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        # 1. Registrar PRIMERO la venta interna para obtener el ID_Venta
        cur.execute(
            "INSERT INTO venta (ID_Tienda, ID_Usuario, Cliente_Nombre) VALUES (%s, %s, %s)",
            (id_cd, id_usuario, f"Traslado a Tienda #{id_tienda_destino}")
        )
        id_venta = cur.lastrowid

        # 2. Crear el traslado pasándole ID_Venta y adaptándose a las columnas/ENUM reales
        cur.execute("SHOW COLUMNS FROM traslado")
        cols_info = {row["Field"].upper(): row for row in cur.fetchall()}

        campos = []
        valores = []
        placeholders = []

        if "ID_VENTA" in cols_info:
            campos.append(cols_info["ID_VENTA"]["Field"])
            valores.append(id_venta)
            placeholders.append("%s")
        if "ID_TIENDA_ORIGEN" in cols_info:
            campos.append(cols_info["ID_TIENDA_ORIGEN"]["Field"])
            valores.append(id_cd)
            placeholders.append("%s")
        if "ID_TIENDA_DESTINO" in cols_info:
            campos.append(cols_info["ID_TIENDA_DESTINO"]["Field"])
            valores.append(id_tienda_destino)
            placeholders.append("%s")
        if "ID_USUARIO_ENVIA" in cols_info:
            campos.append(cols_info["ID_USUARIO_ENVIA"]["Field"])
            valores.append(id_usuario)
            placeholders.append("%s")
        elif "ID_USUARIO" in cols_info:
            campos.append(cols_info["ID_USUARIO"]["Field"])
            valores.append(id_usuario)
            placeholders.append("%s")
        if "FECHA_TRASLADO" in cols_info:
            campos.append(cols_info["FECHA_TRASLADO"]["Field"])
            placeholders.append("CURDATE()")
        elif "FECHA_ENVIO" in cols_info:
            campos.append(cols_info["FECHA_ENVIO"]["Field"])
            placeholders.append("CURDATE()")

        col_estado = cols_info.get("ESTADO_TRASLADO") or cols_info.get("ESTADO")
        if col_estado:
            tipo = str(col_estado["Type"])
            estado_val = "EN TRANSITO"
            if tipo.lower().startswith("enum("):
                opciones_enum = [v.strip().strip("'\"") for v in tipo[5:-1].split(",")]
                estado_val = next(
                    (o for o in opciones_enum if "TRANSIT" in o.upper() or "PEND" in o.upper()),
                    opciones_enum[0]
                )
            campos.append(col_estado["Field"])
            valores.append(estado_val)
            placeholders.append("%s")

        sql_traslado = f"INSERT INTO traslado ({', '.join(campos)}) VALUES ({', '.join(placeholders)})"
        cur.execute(sql_traslado, tuple(valores))
        id_traslado = cur.lastrowid

        for l in lineas:
            cantidad = _dec(l["cantidad"])
            costo = _dec(l["costo"])
            id_prod = l["id_producto"]

            # Traer lotes disponibles ordenados por fecha de vencimiento (FEFO)
            cur.execute(
                "SELECT ID_Inventario, Existencias FROM inventario "
                "WHERE ID_Tienda = %s AND ID_Producto = %s AND Existencias > 0 "
                "ORDER BY Fecha_Vencimiento ASC, ID_Inventario ASC FOR UPDATE",
                (id_cd, id_prod)
            )
            lotes = cur.fetchall()
            disp_total = sum(_dec(lote["Existencias"]) for lote in lotes)

            if disp_total < cantidad:
                raise ErrorNegocio(f"Stock insuficiente para {l['nombre']}. Hay {disp_total}.")

            # Descontar lote por lote y registrar en detalle_venta con ID_Inventario y Precio_Venta
            restante = cantidad
            for lote in lotes:
                if restante <= 0:
                    break
                disp_lote = _dec(lote["Existencias"])
                tomar = min(restante, disp_lote)

                cur.execute(
                    "UPDATE inventario SET Existencias = Existencias - %s WHERE ID_Inventario = %s",
                    (tomar, lote["ID_Inventario"])
                )
                cur.execute(
                    "INSERT INTO detalle_venta (ID_Venta, ID_Inventario, Cantidad, Precio_Venta) "
                    "VALUES (%s, %s, %s, %s)",
                    (id_venta, lote["ID_Inventario"], tomar, costo)
                )
                restante -= tomar

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
    st.title("🚚 Despacho a Tiendas (Venta Interna)")
    st.markdown("Registra la salida del inventario al costo y lo envía en estado 'En Tránsito'.")

    id_tienda = st.session_state.id_tienda

    tiendas = _consultar(get_connection, "SELECT ID_Tienda, Nombre FROM tienda WHERE ID_Tienda != %s", (id_tienda,))
    if not tiendas:
        st.warning("No hay otras sucursales destino registradas.")
        return

    tiendas_opts = {t["Nombre"]: t["ID_Tienda"] for t in tiendas}
    id_destino = tiendas_opts[st.selectbox("Tienda Destino (Cliente Interno)", list(tiendas_opts.keys()))]

    productos = _consultar(
        get_connection,
        "SELECT P.ID_Producto, P.Cod_Producto, P.Nombre, SUM(I.Existencias) as Disp "
        "FROM inventario I JOIN producto P ON I.ID_Producto = P.ID_Producto "
        "WHERE I.ID_Tienda = %s AND I.Existencias > 0 GROUP BY P.ID_Producto",
        (id_tienda,)
    )

    if not productos:
        st.info("No hay inventario disponible para despachar.")
        return

    if "carrito_vi" not in st.session_state:
        st.session_state.carrito_vi = []

    prod_opts = {f"{p['Cod_Producto']} - {p['Nombre']} (Disp: {p['Disp']})": p for p in productos}

    st.subheader("Agregar Productos")
    c1, c2, c3, c4 = st.columns([3, 1, 1, 2])
    prod_sel = prod_opts[c1.selectbox("Producto", list(prod_opts.keys()))]

    cantidad = c2.number_input("Cant.", min_value=1, value=1)
    costo = c3.number_input("Costo $", min_value=0.01, value=1.00)

    if c4.button("➕ Agregar al despacho", use_container_width=True):
        if cantidad > int(prod_sel['Disp']):
            st.error(f"⚠️ Error: Excede el stock disponible. Solo hay {prod_sel['Disp']}.")
        else:
            st.session_state.carrito_vi.append({
                "id_producto": prod_sel["ID_Producto"],
                "nombre": prod_sel["Nombre"],
                "cantidad": cantidad,
                "costo": costo,
                "subtotal": float(cantidad) * float(costo)
            })
            st.rerun()

    carrito = st.session_state.carrito_vi
    if carrito:
        st.dataframe(pd.DataFrame(carrito), use_container_width=True, hide_index=True)

        total = sum(l["subtotal"] for l in carrito)
        st.markdown(f"### Valor del Despacho: **${total:,.2f}**")

        if st.button("Vaciar lista"):
            st.session_state.carrito_vi = []
            st.rerun()

        if st.button("✅ Confirmar Salida de CD", type="primary"):
            conn = get_connection()
            if conn:
                try:
                    id_t, id_v = registrar_venta_interna(conn, id_tienda, id_destino, st.session_state.id_usuario, carrito)
                    st.success(f"Despacho exitoso. Traslado #{id_t} en tránsito (Venta interna #{id_v}).")
                    st.session_state.carrito_vi = []
                except ErrorNegocio as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Error procesando la salida: {e}")
                finally:
                    conn.close()
