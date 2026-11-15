"""
Registro de ventas - SGI Tiendas / Centro de Distribución.

Qué hace una venta, paso a paso (todo dentro de UNA transacción):
  1. Crea el encabezado en `venta` (ID_Venta autoincremental = único en todo el sistema).
  2. Por cada producto del carrito busca los lotes de `inventario` de ESA tienda
     (bloqueándolos con FOR UPDATE para que dos usuarios no vendan lo mismo).
  3. Reparte la cantidad entre los lotes, primero el que vence antes (FEFO).
  4. Inserta una línea en `detalle_venta` por cada lote usado y descuenta `Existencias`.
  5. Si algo falla (por ejemplo, no hay existencias) hace ROLLBACK: no queda nada a medias.

Los totales NO se guardan: salen de la vista v_venta_total.
"""
from decimal import Decimal, ROUND_HALF_UP


class ErrorNegocio(Exception):
    """Error que se le puede mostrar tal cual al usuario (regla de negocio incumplida)."""


def _dec(valor):
    return Decimal(str(valor)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def repartir_en_lotes(lotes, cantidad, nombre_producto=""):
    """
    lotes: lista de dicts con 'ID_Inventario' y 'Existencias', YA ordenados por
           fecha de vencimiento (el que vence primero va primero).
    Devuelve [(id_inventario, cantidad_a_tomar), ...] o lanza ErrorNegocio si no alcanza.
    """
    cantidad = _dec(cantidad)
    if cantidad <= 0:
        raise ErrorNegocio("La cantidad debe ser mayor que cero.")

    disponible = sum((l["Existencias"] for l in lotes), Decimal("0"))
    if disponible < cantidad:
        raise ErrorNegocio(
            f"Existencias insuficientes de {nombre_producto or 'producto'}: "
            f"disponible {disponible}, solicitado {cantidad}."
        )

    reparto, pendiente = [], cantidad
    for lote in lotes:
        if pendiente <= 0:
            break
        tomar = min(lote["Existencias"], pendiente)
        if tomar > 0:
            reparto.append((lote["ID_Inventario"], tomar))
            pendiente -= tomar
    return reparto


def registrar_venta(conn, id_tienda, id_usuario, cliente_nombre, items):
    """
    items: lista de (id_producto, cantidad). Devuelve (id_venta, total).
    Recibe una conexión NUEVA y sin transacción abierta; hace commit o rollback.
    """
    if not items:
        raise ErrorNegocio("El carrito está vacío.")

    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()

        cur.execute(
            "INSERT INTO venta (ID_Tienda, ID_Usuario, Cliente_Nombre) VALUES (%s, %s, %s)",
            (id_tienda, id_usuario, cliente_nombre or None),
        )
        id_venta = cur.lastrowid
        total = Decimal("0")

        for id_producto, cantidad in items:
            # Precio y nombre: el producto debe estar en el catálogo de ESTA tienda
            cur.execute(
                """SELECT p.Nombre, pt.Precio_Venta
                   FROM producto_tienda pt
                   JOIN producto p ON p.ID_Producto = pt.ID_Producto
                   WHERE pt.ID_Tienda = %s AND pt.ID_Producto = %s
                     AND p.Estado_Producto = 'ACTIVO'""",
                (id_tienda, id_producto),
            )
            prod = cur.fetchone()
            if not prod:
                raise ErrorNegocio("Un producto del carrito no está disponible en esta tienda.")

            # Lotes con existencias y no vencidos, el que vence primero va primero (FEFO).
            # Los productos sin vencimiento usan 9999-12-31, así que quedan al final.
            cur.execute(
                """SELECT ID_Inventario, Existencias
                   FROM inventario
                   WHERE ID_Tienda = %s AND ID_Producto = %s
                     AND Existencias > 0 AND Fecha_Vencimiento >= CURDATE()
                   ORDER BY Fecha_Vencimiento ASC, ID_Inventario ASC
                   FOR UPDATE""",
                (id_tienda, id_producto),
            )
            lotes = cur.fetchall()

            for id_inventario, tomar in repartir_en_lotes(lotes, cantidad, prod["Nombre"]):
                cur.execute(
                    """INSERT INTO detalle_venta (ID_Venta, ID_Inventario, Cantidad, Precio_Venta)
                       VALUES (%s, %s, %s, %s)""",
                    (id_venta, id_inventario, tomar, prod["Precio_Venta"]),
                )
                cur.execute(
                    "UPDATE inventario SET Existencias = Existencias - %s WHERE ID_Inventario = %s",
                    (tomar, id_inventario),
                )
                total += tomar * prod["Precio_Venta"]

        conn.commit()
        return id_venta, total
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def _catalogo_con_existencias(get_connection, id_tienda):
    """Productos de la tienda con existencias disponibles (sin contar lotes vencidos)."""
    conn = get_connection()
    if conn is None:
        return []
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(
            """SELECT p.ID_Producto, p.Cod_Producto, p.Nombre, p.Unidad_Medida,
                      pt.Precio_Venta, SUM(i.Existencias) AS Disponible
               FROM producto_tienda pt
               JOIN producto p ON p.ID_Producto = pt.ID_Producto AND p.Estado_Producto = 'ACTIVO'
               JOIN inventario i ON i.ID_Tienda = pt.ID_Tienda AND i.ID_Producto = pt.ID_Producto
                                AND i.Existencias > 0 AND i.Fecha_Vencimiento >= CURDATE()
               WHERE pt.ID_Tienda = %s
               GROUP BY p.ID_Producto, p.Cod_Producto, p.Nombre, p.Unidad_Medida, pt.Precio_Venta
               ORDER BY p.Nombre""",
            (id_tienda,),
        )
        return cur.fetchall()
    finally:
        conn.close()


def pantalla_registrar_venta(get_connection):
    """Pantalla de Streamlit. Se llama desde app.py cuando se elige 'Registrar venta'."""
    import streamlit as st  # se importa aquí para poder probar la lógica sin Streamlit
    import pandas as pd

    st.title("🧾 Registrar venta")

    id_tienda = st.session_state.id_tienda
    id_usuario = st.session_state.id_usuario  # hay que guardarlo al iniciar sesión (ver app.py)

    if "venta_ok" in st.session_state:
        st.success(st.session_state.pop("venta_ok"))
    if "carrito" not in st.session_state:
        st.session_state.carrito = {}  # {id_producto: {nombre, unidad, precio, cantidad, disponible}}

    catalogo = _catalogo_con_existencias(get_connection, id_tienda)
    if not catalogo:
        st.info("No hay productos con existencias disponibles en esta tienda.")
        return

    opciones = {
        f"{c['Cod_Producto']} · {c['Nombre']}  (disponible: {c['Disponible']} {c['Unidad_Medida']}, ${c['Precio_Venta']})": c
        for c in catalogo
    }

    col1, col2, col3 = st.columns([4, 1.5, 1])
    elegido = opciones[col1.selectbox("Producto", list(opciones.keys()))]
    cantidad = col2.number_input("Cantidad", min_value=0.01, value=1.0, step=1.0)
    col3.write("")
    if col3.button("➕ Agregar", use_container_width=True):
        pid = elegido["ID_Producto"]
        ya = st.session_state.carrito.get(pid, {}).get("cantidad", Decimal("0"))
        nueva = ya + _dec(cantidad)
        if nueva > elegido["Disponible"]:
            st.error(f"Solo hay {elegido['Disponible']} {elegido['Unidad_Medida']} disponibles de {elegido['Nombre']}.")
        else:
            st.session_state.carrito[pid] = {
                "nombre": elegido["Nombre"], "unidad": elegido["Unidad_Medida"],
                "precio": elegido["Precio_Venta"], "cantidad": nueva,
                "disponible": elegido["Disponible"],
            }

    carrito = st.session_state.carrito
    st.subheader("Carrito")
    if not carrito:
        st.caption("Aún no hay productos en la venta.")
    else:
        filas = [
            {"Producto": d["nombre"], "Cantidad": float(d["cantidad"]), "Unidad": d["unidad"],
             "Precio": float(d["precio"]), "Subtotal": float(d["cantidad"] * d["precio"])}
            for d in carrito.values()
        ]
        st.dataframe(pd.DataFrame(filas), use_container_width=True, hide_index=True)
        total = sum((d["cantidad"] * d["precio"] for d in carrito.values()), Decimal("0"))
        st.metric("Total de la venta", f"${total:,.2f}")

        quitar_col, vaciar_col = st.columns(2)
        a_quitar = quitar_col.selectbox("Quitar del carrito", ["—"] + [d["nombre"] for d in carrito.values()])
        if quitar_col.button("Quitar") and a_quitar != "—":
            for pid, d in list(carrito.items()):
                if d["nombre"] == a_quitar:
                    del carrito[pid]
            st.rerun()
        if vaciar_col.button("Vaciar carrito"):
            st.session_state.carrito = {}
            st.rerun()

    cliente = st.text_input("Cliente (opcional)")

    if st.button("✅ Registrar venta", type="primary", disabled=not carrito):
        conn = get_connection()
        if conn is None:
            return
        try:
            items = [(pid, d["cantidad"]) for pid, d in carrito.items()]
            id_venta, total = registrar_venta(conn, id_tienda, id_usuario, cliente.strip(), items)
            st.session_state.carrito = {}
            st.session_state.venta_ok = f"Venta #{id_venta} registrada. Total: ${total:,.2f}"
            st.rerun()
        except ErrorNegocio as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"No se pudo registrar la venta y no se guardó nada. Detalle: {e}")
        finally:
            conn.close()
