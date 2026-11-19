"""
Registro de compras - SGI Tiendas / Centro de Distribución.
Incluye Pestaña de Compra Externa y Pestaña de Recepción de Traslados (Venta Interna del CD).
"""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import streamlit as st
import pandas as pd

from form_venta import ErrorNegocio

SIN_VENCIMIENTO = date(9999, 12, 31)

def _dec(valor):
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def validar_linea(linea, hoy=None):
    hoy = hoy or date.today()
    if _dec(linea["cantidad"]) <= 0:
        raise ErrorNegocio("La cantidad debe ser mayor que cero.")
    if _dec(linea["precio_compra"]) < 0:
        raise ErrorNegocio("El precio de compra no puede ser negativo.")
    if linea.get("vencimiento") and linea["vencimiento"] < hoy:
        raise ErrorNegocio("No se puede ingresar un lote que ya está vencido.")
    if linea.get("precio_sugerido") is not None and _dec(linea["precio_sugerido"]) < 0:
        raise ErrorNegocio("El precio de venta sugerido no puede ser negativo.")

def registrar_compra(conn, id_tienda, id_usuario, id_proveedor, lineas, hoy=None):
    if not lineas:
        raise ErrorNegocio("La compra no tiene productos.")
    for l in lineas:
        validar_linea(l, hoy)

    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cur.execute(
            "SELECT ID_Proveedor FROM proveedor WHERE ID_Proveedor = %s AND ID_Tienda = %s AND ID_Tienda_CD IS NULL",
            (id_proveedor, id_tienda),
        )
        if not cur.fetchone():
            raise ErrorNegocio("El proveedor elegido no pertenece a esta tienda.")

        cur.execute(
            "INSERT INTO compra (ID_Tienda, ID_Proveedor, ID_Usuario) VALUES (%s, %s, %s)",
            (id_tienda, id_proveedor, id_usuario),
        )
        id_compra = cur.lastrowid
        total = Decimal("0")

        for l in lineas:
            cantidad, precio = _dec(l["cantidad"]), _dec(l["precio_compra"])
            sugerido = _dec(l["precio_sugerido"]) if l.get("precio_sugerido") else None

            cur.execute("SELECT Nombre FROM producto WHERE ID_Producto = %s AND Estado_Producto = 'ACTIVO'", (l["id_producto"],))
            prod = cur.fetchone()
            if not prod:
                raise ErrorNegocio("Un producto de la compra no existe o está inactivo.")

            cur.execute("SELECT 1 AS ok FROM producto_tienda WHERE ID_Tienda = %s AND ID_Producto = %s", (id_tienda, l["id_producto"]))
            if not cur.fetchone():
                if not sugerido:
                    raise ErrorNegocio(f"{prod['Nombre']} no está en el catálogo de esta tienda: indique un precio sugerido.")
                cur.execute("INSERT INTO producto_tienda (ID_Tienda, ID_Producto, Precio_Venta) VALUES (%s, %s, %s)", (id_tienda, l["id_producto"], sugerido))

            cur.execute(
                """INSERT INTO detalle_compra (ID_Compra, ID_Producto, Cantidad, Precio_Compra, Fecha_Vencimiento, Precio_Venta_Sugerido)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (id_compra, l["id_producto"], cantidad, precio, l.get("vencimiento"), sugerido),
            )

            cur.execute(
                """INSERT INTO inventario (ID_Tienda, ID_Producto, Fecha_Vencimiento, Existencias)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE Existencias = Existencias + VALUES(Existencias)""",
                (id_tienda, l["id_producto"], l.get("vencimiento") or SIN_VENCIMIENTO, cantidad),
            )

            cur.execute(
                """INSERT INTO producto_proveedor (ID_Producto, ID_Proveedor, Ultimo_Costo, Fecha_Ultimo_Costo, Estado)
                   VALUES (%s, %s, %s, CURDATE(), 'ACTIVO')
                   ON DUPLICATE KEY UPDATE Ultimo_Costo = VALUES(Ultimo_Costo), Fecha_Ultimo_Costo = VALUES(Fecha_Ultimo_Costo), Estado = 'ACTIVO'""",
                (l["id_producto"], id_proveedor, precio),
            )
            total += cantidad * precio

        conn.commit()
        return id_compra, total
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def registrar_proveedor(conn, id_tienda, nombre, dui_nit, telefono, correo, direccion):
    nombre = (nombre or "").strip()
    if not nombre:
        raise ErrorNegocio("El nombre del proveedor es obligatorio.")
    def _o_null(txt): return (txt or "").strip() or None
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO proveedor (ID_Tienda, Nombre, DUI_NIT, Telefono, Correo, Direccion) VALUES (%s, %s, %s, %s, %s, %s)",
            (id_tienda, nombre, _o_null(dui_nit), _o_null(telefono), _o_null(correo), _o_null(direccion)),
        )
        conn.commit()
        return cur.lastrowid
    except Exception as e:
        conn.rollback()
        if getattr(e, "errno", None) == 1062:
            raise ErrorNegocio("Ya existe un proveedor con ese DUI/NIT en esta tienda.")
        raise
    finally:
        cur.close()

def _info_tabla_traslado(cur):
    """Detecta nombres exactos de columnas y valores ENUM en la tabla traslado."""
    cur.execute("SHOW COLUMNS FROM traslado")
    cols_info = {row["Field"].upper(): row for row in cur.fetchall()}

    col_estado_row = cols_info.get("ESTADO_TRASLADO") or cols_info.get("ESTADO")
    col_estado = col_estado_row["Field"] if col_estado_row else "Estado"

    val_transito = "EN TRANSITO"
    val_recibido = "RECIBIDO"
    if col_estado_row and str(col_estado_row["Type"]).lower().startswith("enum("):
        opts = [v.strip().strip("'\"") for v in str(col_estado_row["Type"])[5:-1].split(",")]
        val_transito = next((o for o in opts if "TRANSIT" in o.upper() or "PEND" in o.upper()), opts[0])
        val_recibido = next((o for o in opts if "RECIB" in o.upper() or "COMPLET" in o.upper() or "ENTREG" in o.upper()), opts[-1])

    col_fecha_row = cols_info.get("FECHA_TRASLADO") or cols_info.get("FECHA_ENVIO") or cols_info.get("FECHA")
    col_fecha = col_fecha_row["Field"] if col_fecha_row else None

    return cols_info, col_estado, val_transito, val_recibido, col_fecha

def recibir_traslado_bd(conn, id_traslado, id_tienda, id_usuario):
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cols_info, col_estado, _, val_recibido, _ = _info_tabla_traslado(cur)

        # 1. Obtener datos del traslado (incluyendo ID_Venta e ID_Tienda_Origen)
        cur.execute("SELECT * FROM traslado WHERE ID_Traslado = %s FOR UPDATE", (id_traslado,))
        traslado = cur.fetchone()
        if not traslado:
            raise ErrorNegocio("No se encontró el traslado.")

        id_venta = traslado.get("ID_Venta")
        id_origen = traslado.get("ID_Tienda_Origen")

        # 2. Traer los productos, cantidades, costos y vencimientos desde detalle_venta + inventario
        cur.execute("""
            SELECT I.ID_Producto, DV.Cantidad, DV.Precio_Venta AS Costo, I.Fecha_Vencimiento
            FROM detalle_venta DV
            JOIN inventario I ON DV.ID_Inventario = I.ID_Inventario
            WHERE DV.ID_Venta = %s
        """, (id_venta,))
        detalles = cur.fetchall()
        if not detalles:
            raise ErrorNegocio("El traslado no tiene productos asociados en detalle_venta.")

        # 3. Buscar el proveedor interno que representa al CD para esta tienda (si existe)
        cur.execute(
            "SELECT ID_Proveedor FROM proveedor WHERE ID_Tienda = %s AND ID_Tienda_CD = %s LIMIT 1",
            (id_tienda, id_origen)
        )
        prov_cd = cur.fetchone()
        if not prov_cd:
            cur.execute(
                "SELECT ID_Proveedor FROM proveedor WHERE ID_Tienda = %s AND ID_Tienda_CD IS NOT NULL LIMIT 1",
                (id_tienda,)
            )
            prov_cd = cur.fetchone()
        id_proveedor = prov_cd["ID_Proveedor"] if prov_cd else None

        # 4. Registrar la compra interna en la tienda destino
        cur.execute(
            "INSERT INTO compra (ID_Tienda, ID_Proveedor, ID_Usuario) VALUES (%s, %s, %s)",
            (id_tienda, id_proveedor, id_usuario)
        )
        id_compra = cur.lastrowid

        # 5. Insertar detalle_compra y sumar al inventario respetando la fecha de vencimiento original
        for d in detalles:
            venc = d["Fecha_Vencimiento"] or SIN_VENCIMIENTO
            venc_detalle = None if venc == SIN_VENCIMIENTO else venc

            cur.execute(
                """INSERT INTO detalle_compra (ID_Compra, ID_Producto, Cantidad, Precio_Compra, Fecha_Vencimiento)
                   VALUES (%s, %s, %s, %s, %s)""",
                (id_compra, d["ID_Producto"], d["Cantidad"], d["Costo"], venc_detalle)
            )
            cur.execute(
                """INSERT INTO inventario (ID_Tienda, ID_Producto, Fecha_Vencimiento, Existencias)
                   VALUES (%s, %s, %s, %s)
                   ON DUPLICATE KEY UPDATE Existencias = Existencias + VALUES(Existencias)""",
                (id_tienda, d["ID_Producto"], venc, d["Cantidad"])
            )

        # 6. Actualizar el estado del traslado a RECIBIDO (y columnas opcionales si existen)
        sets = [f"{col_estado} = %s"]
        params_upd = [val_recibido]

        if "ID_COMPRA" in cols_info:
            sets.append(f"{cols_info['ID_COMPRA']['Field']} = %s")
            params_upd.append(id_compra)
        if "ID_USUARIO_RECIBE" in cols_info:
            sets.append(f"{cols_info['ID_USUARIO_RECIBE']['Field']} = %s")
            params_upd.append(id_usuario)
        if "FECHA_RECEPCION" in cols_info:
            sets.append(f"{cols_info['FECHA_RECEPCION']['Field']} = CURDATE()")

        params_upd.append(id_traslado)
        cur.execute(f"UPDATE traslado SET {', '.join(sets)} WHERE ID_Traslado = %s", tuple(params_upd))

        conn.commit()
        return id_compra
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def _consultar(get_connection, sql, params=()):
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        conn.close()

def _proveedores_de(get_connection, id_tienda):
    return _consultar(get_connection, "SELECT ID_Proveedor, Nombre, DUI_NIT FROM proveedor WHERE ID_Tienda = %s AND ID_Tienda_CD IS NULL ORDER BY Nombre", (id_tienda,))

def _catalogo_global(get_connection):
    return _consultar(get_connection, "SELECT ID_Producto, Cod_Producto, Nombre, Unidad_Medida FROM producto WHERE Estado_Producto = 'ACTIVO' ORDER BY Nombre")


# ----------------------------------- PANTALLA PRINCIPAL -----------------------------------
def pantalla_registrar_compra(get_connection):
    st.title("🛒 Ingresos al Inventario")

    id_tienda = st.session_state.id_tienda
    id_usuario = st.session_state.id_usuario

    tab_compra, tab_recepcion = st.tabs(["🛒 Compras Externas (Proveedores)", "📥 Recepción de Traslados (CD)"])

    # ------------------ PESTAÑA 1: COMPRAS NORMALES ------------------
    with tab_compra:
        if "compra_ok" in st.session_state:
            st.success(st.session_state.pop("compra_ok"))
        if "carrito_compra" not in st.session_state:
            st.session_state.carrito_compra = []

        proveedores = _proveedores_de(get_connection, id_tienda)
        with st.expander("➕ Registrar proveedor nuevo", expanded=not proveedores):
            c1, c2 = st.columns(2)
            n_nombre = c1.text_input("Nombre del proveedor", key="prov_nombre")
            n_dui = c2.text_input("DUI/NIT (opcional)", key="prov_dui")
            c3, c4 = st.columns(2)
            n_tel = c3.text_input("Teléfono (opcional)", key="prov_tel")
            n_correo = c4.text_input("Correo (opcional)", key="prov_correo")
            n_dir = st.text_input("Dirección (opcional)", key="prov_dir")
            if st.button("Guardar proveedor"):
                conn = get_connection()
                if conn is not None:
                    try:
                        registrar_proveedor(conn, id_tienda, n_nombre, n_dui, n_tel, n_correo, n_dir)
                        st.session_state.compra_ok = f"Proveedor «{n_nombre.strip()}» registrado."
                        st.rerun()
                    except ErrorNegocio as e:
                        st.error(str(e))
                    finally:
                        conn.close()

        if not proveedores:
            st.info("Registre al menos un proveedor para poder ingresar compras.")
        else:
            prov_opts = {f"{p['Nombre']}" + (f" ({p['DUI_NIT']})" if p["DUI_NIT"] else ""): p["ID_Proveedor"] for p in proveedores}
            prov_label = st.selectbox("Proveedor", list(prov_opts.keys()))

            catalogo = _catalogo_global(get_connection)
            if not catalogo:
                st.info("No hay productos activos en el catálogo.")
            else:
                prod_opts = {f"{p['Cod_Producto']} · {p['Nombre']} ({p['Unidad_Medida']})": p for p in catalogo}
                st.subheader("Productos de la compra")
                a1, a2, a3 = st.columns([4, 1.5, 1.5])
                prod = prod_opts[a1.selectbox("Producto", list(prod_opts.keys()))]
                cantidad = a2.number_input("Cantidad", min_value=0.01, value=1.0, step=1.0)
                precio = a3.number_input("Precio de compra", min_value=0.0, value=0.0, step=0.25)

                b1, b2, b3 = st.columns([1.5, 2, 2.5])
                vence = b1.checkbox("Tiene vencimiento")
                fecha_venc = b2.date_input("Fecha de vencimiento", value=date.today(), min_value=date.today(), disabled=not vence)
                sugerido = b3.number_input("Precio sugerido (0 = no definir)", min_value=0.0, value=0.0, step=0.25)

                if st.button("➕ Agregar a la compra"):
                    linea = {"id_producto": prod["ID_Producto"], "nombre": prod["Nombre"], "unidad": prod["Unidad_Medida"], "cantidad": _dec(cantidad), "precio_compra": _dec(precio), "vencimiento": fecha_venc if vence else None, "precio_sugerido": _dec(sugerido) if sugerido > 0 else None}
                    try:
                        validar_linea(linea)
                        st.session_state.carrito_compra.append(linea)
                    except ErrorNegocio as e:
                        st.error(str(e))

                carrito = st.session_state.carrito_compra
                if not carrito:
                    st.caption("Aún no hay productos en la compra.")
                else:
                    filas = [{"#": i + 1, "Producto": l["nombre"], "Cantidad": float(l["cantidad"]), "Unidad": l["unidad"], "Precio compra": float(l["precio_compra"]), "Vence": l["vencimiento"].isoformat() if l["vencimiento"] else "—", "Precio venta sugerido": float(l["precio_sugerido"]) if l["precio_sugerido"] else None, "Subtotal": float(l["cantidad"] * l["precio_compra"])} for i, l in enumerate(carrito)]
                    st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
                    total = sum((l["cantidad"] * l["precio_compra"] for l in carrito), Decimal("0"))
                    st.metric("Total de la compra", f"${total:,.2f}")

                    q1, q2 = st.columns(2)
                    n_quitar = q1.selectbox("Quitar línea", ["—"] + list(range(1, len(carrito) + 1)))
                    if q1.button("Quitar línea") and n_quitar != "—":
                        del carrito[n_quitar - 1]
                        st.rerun()
                    if q2.button("Vaciar compra"):
                        st.session_state.carrito_compra = []
                        st.rerun()

                if st.button("✅ Registrar compra externa", type="primary", disabled=not carrito):
                    conn = get_connection()
                    if conn:
                        try:
                            id_c, total_c = registrar_compra(conn, id_tienda, id_usuario, prov_opts[prov_label], carrito)
                            st.session_state.carrito_compra = []
                            st.session_state.compra_ok = f"Compra #{id_c} registrada. Total: ${total_c:,.2f}. Inventario actualizado."
                            st.rerun()
                        except ErrorNegocio as e:
                            st.error(str(e))
                        finally:
                            conn.close()

    # ------------------ PESTAÑA 2: RECEPCIÓN DE TRASLADOS ------------------
    with tab_recepcion:
        st.subheader("Mercadería en Tránsito (Desde otras sucursales)")
        if "recepcion_ok" in st.session_state:
            st.success(st.session_state.pop("recepcion_ok"))

        pendientes = []
        conn_check = get_connection()
        if conn_check:
            try:
                cur_c = conn_check.cursor(dictionary=True)
                _, col_estado, val_transito, _, col_fecha = _info_tabla_traslado(cur_c)
                sel_fecha = f"T.{col_fecha} AS Fecha_Envio" if col_fecha else "CURDATE() AS Fecha_Envio"
                cur_c.execute(f"""
                    SELECT T.ID_Traslado, T.ID_Venta, {sel_fecha}, Ti.Nombre AS Origen
                    FROM traslado T
                    JOIN tienda Ti ON T.ID_Tienda_Origen = Ti.ID_Tienda
                    WHERE T.ID_Tienda_Destino = %s AND T.{col_estado} = %s
                """, (id_tienda, val_transito))
                pendientes = cur_c.fetchall()
            finally:
                conn_check.close()

        if not pendientes:
            st.success("🎉 No hay envíos pendientes de recepción hacia esta tienda.")
        else:
            for p in pendientes:
                with st.expander(f"📦 Traslado #{p['ID_Traslado']} - Viene de: {p['Origen']} (Despachado: {p['Fecha_Envio']})", expanded=True):
                    detalles = _consultar(get_connection, """
                        SELECT P.Cod_Producto, P.Nombre, DV.Cantidad, DV.Precio_Venta AS Costo, I.Fecha_Vencimiento
                        FROM detalle_venta DV
                        JOIN inventario I ON DV.ID_Inventario = I.ID_Inventario
                        JOIN producto P ON I.ID_Producto = P.ID_Producto
                        WHERE DV.ID_Venta = %s
                    """, (p['ID_Venta'],))

                    st.dataframe(pd.DataFrame(detalles), use_container_width=True, hide_index=True)

                    if st.button("📥 Confirmar Recepción Física (Ingresar a inventario)", key=f"btn_rec_{p['ID_Traslado']}", type="primary"):
                        conn_rec = get_connection()
                        if conn_rec:
                            try:
                                id_c = recibir_traslado_bd(conn_rec, p['ID_Traslado'], id_tienda, id_usuario)
                                st.session_state.recepcion_ok = f"Inventario recibido. Se generó el ingreso #{id_c}."
                                st.rerun()
                            except ErrorNegocio as e:
                                st.error(str(e))
                            except Exception as e:
                                st.error(f"Error al procesar la recepción: {e}")
                            finally:
                                conn_rec.close()
