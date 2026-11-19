import streamlit as st
import mysql.connector
import pandas as pd
import hashlib
import datetime
# Importamos todos los módulos
from form_venta import pantalla_registrar_venta
from form_compra import pantalla_registrar_compra
from form_venta_interna import pantalla_venta_interna
from form_admin import pantalla_admin
from form_merma import pantalla_registrar_merma

# Configuración inicial de la página
st.set_page_config(
    page_title="SGI - Sistema de Gestión de Inventario",
    page_icon="📦",
    layout="wide"
)

# --- 1. CONFIGURACIÓN DE CONEXIÓN A LA BASE DE DATOS ---
def get_connection():
    try:
        return mysql.connector.connect(
            host=st.secrets.get("DB_HOST", "localhost"),
            user=st.secrets.get("DB_USER", "root"),
            password=st.secrets.get("DB_PASSWORD", ""),
            database=st.secrets.get("DB_NAME", "sgi_tiendas"),
            port=int(st.secrets.get("DB_PORT", 3306))
        )
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

def run_query(query, params=None):
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql(query, conn, params=params)
            return df
        except Exception as e:
            st.error(f"Ocurrió un error en la consulta: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

def boton_exportar(df, nombre_archivo):
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Descargar en Excel / CSV",
        data=csv,
        file_name=f"{nombre_archivo}.csv",
        mime='text/csv'
    )

# --- 2. CONTROL DE SESIÓN / LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.user_role = ""
    st.session_state.id_tienda = None
    st.session_state.id_usuario = None

if "vista_actual" not in st.session_state:
    st.session_state.vista_actual = "🏠 Menú Principal"

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col_centro, _ = st.columns([1, 1.4, 1])

    with col_centro:
        with st.container(border=True):
            st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>📦</h1>", unsafe_allow_html=True)
            st.markdown("<h2 style='text-align: center; margin-top: 0; color: #1B365D;'>SGI Inventarios</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: gray; font-size: 14px;'>Inicia sesión para gestionar tus tiendas y el CD</p>", unsafe_allow_html=True)
            st.markdown("---")

            with st.form("login_form", border=False):
                correo = st.text_input("Correo Electrónico", placeholder="ejemplo@sgi.com")
                password = st.text_input("Contraseña", type="password", placeholder="••••••••")
                st.markdown("<br>", unsafe_allow_html=True)
                submit = st.form_submit_button("Ingresar al Sistema", type="primary", use_container_width=True)

                if submit:
                    hashed_input = hashlib.sha256(password.encode()).hexdigest()
                    conn = get_connection()
                    if conn:
                        cursor = conn.cursor(dictionary=True)
                        cursor.execute(
                            "SELECT U.ID_Usuario, U.Nombre, U.ID_Tienda, R.Nombre as Rol, U.Password_Hash "
                            "FROM usuario U JOIN rol R ON U.ID_Rol = R.ID_Rol WHERE U.Correo = %s",
                            (correo,)
                        )
                        user = cursor.fetchone()
                        conn.close()

                        if user and user["Password_Hash"] == hashed_input:
                            st.session_state.logged_in = True
                            st.session_state.user_name = user["Nombre"]
                            st.session_state.user_role = user["Rol"]
                            st.session_state.id_tienda = user["ID_Tienda"]
                            st.session_state.id_usuario = user["ID_Usuario"]
                            st.rerun()
                        else:
                            st.error("Correo o contraseña incorrectos.")
    st.stop()

# --- 3. FUNCIONES DE NAVEGACIÓN Y TARJETAS ---
def cambiar_pantalla(nueva_pantalla):
    st.session_state.vista_actual = nueva_pantalla

def crear_tarjeta(icono, titulo, descripcion, texto_boton, vista_destino):
    with st.container(border=True):
        st.markdown(f"<h1 style='text-align: center; margin-bottom: 0px;'>{icono}</h1>", unsafe_allow_html=True)
        st.markdown(f"<h4 style='text-align: center; margin-bottom: 0px;'>{titulo}</h4>", unsafe_allow_html=True)
        st.markdown(f"<p style='text-align: center; color: gray; font-size: 14px;'>{descripcion}</p>", unsafe_allow_html=True)
        st.button(
            texto_boton,
            use_container_width=True,
            type="primary",
            on_click=cambiar_pantalla,
            args=(vista_destino,),
            key=f"btn_{titulo}"
        )

# --- 4. BARRA DE NAVEGACIÓN SUPERIOR (SIN SIDEBAR) ---
menu = st.session_state.vista_actual
rol = st.session_state.user_role.upper()
id_tienda = st.session_state.id_tienda
hoy = datetime.date.today()
hace_un_mes = hoy - datetime.timedelta(days=30)

opciones = [
    "🏠 Menú Principal",
    "📊 Dashboard de Inventario",
    "🚨 Puntos de Reorden",
    "💰 Análisis de Ventas",
    "📦 Análisis de Compras"
]

if rol != 'ADMINISTRADOR':
    opciones.extend([
        "📥 Gestión de Ingresos",
        "🧾 Venta a Cliente Externo",
        "🚚 Venta Interna (Al Costo)",
        "🗑️ Control de Mermas"
    ])
else:
    opciones.append("⚙️ Panel de Administración")

# Cabecera discreta con usuario y botón de salir
col_user, col_salir = st.columns([6, 1])
with col_user:
    st.caption(f"👤 **{st.session_state.user_name}** · Rol: {st.session_state.user_role}")
with col_salir:
    if st.button("🚪 Salir", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Barra de botones rápidos (solo visible cuando no estamos en el Menú Principal)
if menu != "🏠 Menú Principal":
    cols_nav = st.columns(len(opciones))
    for idx, op in enumerate(opciones):
        tipo_btn = "primary" if op == menu else "secondary"
        etiqueta = (
            op.replace(" de Inventario", "")
            .replace("Análisis de ", "")
            .replace("Panel de ", "")
            .replace("Gestión de ", "")
            .replace("Control de ", "")
            .replace(" a Cliente Externo", " Externa")
            .replace(" (Al Costo)", "")
        )
        cols_nav[idx].button(
            etiqueta,
            key=f"nav_{idx}",
            type=tipo_btn,
            use_container_width=True,
            on_click=cambiar_pantalla,
            args=(op,)
        )
    st.divider()

# --- 5. VISTAS DE LA APLICACIÓN ---
if menu == "🏠 Menú Principal":
    st.markdown("<h2 style='text-align: center;'>Gestiona tu negocio de manera eficiente</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Primera Fila: Reportes y Dashboard
    c1, c2, c3 = st.columns(3)
    with c1:
        crear_tarjeta("📦", "Inventario y Vencimientos", "Existencias y alertas de lotes", "Ver inventario", "📊 Dashboard de Inventario")
    with c2:
        crear_tarjeta("💰", "Finanzas y Ventas", "Análisis de ventas e ingresos", "Ver ventas", "💰 Análisis de Ventas")
    with c3:
        crear_tarjeta("📈", "Pronósticos y Reorden", "Alertas y pedidos sugeridos", "Ver pronósticos", "🚨 Puntos de Reorden")

    st.markdown("<br>", unsafe_allow_html=True)

    # Segunda Fila: Operaciones (Depende del Rol)
    if rol == 'ADMINISTRADOR':
        c4, c5, c6 = st.columns(3)
        with c4:
            crear_tarjeta("📦", "Compras y Costos", "Historial y comparativa de costos", "Ver compras", "📦 Análisis de Compras")
        with c5:
            crear_tarjeta("👑", "Administración", "Gestionar tiendas, usuarios y catálogo", "⚙️ Gestionar", "⚙️ Panel de Administración")
    else:
        c4, c5, c6, c7 = st.columns(4)
        with c4:
            crear_tarjeta("📥", "Ingresos", "Compras y recepción de traslados", "➕ Ingresar", "📥 Gestión de Ingresos")
        with c5:
            crear_tarjeta("🧾", "Venta Externa", "Clientes a precio normal", "💲 Vender", "🧾 Venta a Cliente Externo")
        with c6:
            crear_tarjeta("🚚", "Venta Interna", "A otras tiendas al costo", "📤 Despachar", "🚚 Venta Interna (Al Costo)")
        with c7:
            crear_tarjeta("🗑️", "Mermas", "Baja de inventario dañado", "➖ Registrar Merma", "🗑️ Control de Mermas")

elif menu == "📊 Dashboard de Inventario":
    st.title("📊 Dashboard de Inventario y Vencimientos")
    if rol == 'ADMINISTRADOR':
        st.markdown("Vista global: Existencias en toda la red.")
        df_inventario = run_query("SELECT * FROM v_inventario_actual;")
        df_vencer = run_query("""
            SELECT T.Nombre AS Tienda, P.Cod_Producto, P.Nombre AS Producto,
                   I.Fecha_Vencimiento, I.Existencias,
                   DATEDIFF(I.Fecha_Vencimiento, CURDATE()) AS Dias_Restantes
            FROM inventario I
            JOIN producto P ON I.ID_Producto = P.ID_Producto
            JOIN tienda T ON I.ID_Tienda = T.ID_Tienda
            WHERE I.Existencias > 0
              AND I.Fecha_Vencimiento < '9999-12-31'
              AND I.Fecha_Vencimiento <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            ORDER BY I.Fecha_Vencimiento ASC;
        """)
    else:
        st.markdown(f"Vista local: Existencias de la Tienda {id_tienda}.")
        df_inventario = run_query("SELECT * FROM v_inventario_actual WHERE ID_Tienda = %s;", (id_tienda,))
        df_vencer = run_query("""
            SELECT P.Cod_Producto, P.Nombre AS Producto,
                   I.Fecha_Vencimiento, I.Existencias,
                   DATEDIFF(I.Fecha_Vencimiento, CURDATE()) AS Dias_Restantes
            FROM inventario I
            JOIN producto P ON I.ID_Producto = P.ID_Producto
            WHERE I.ID_Tienda = %s
              AND I.Existencias > 0
              AND I.Fecha_Vencimiento < '9999-12-31'
              AND I.Fecha_Vencimiento <= DATE_ADD(CURDATE(), INTERVAL 30 DAY)
            ORDER BY I.Fecha_Vencimiento ASC;
        """, (id_tienda,))

    # Alertas de productos por vencer (próximos 30 días)
    if not df_vencer.empty:
        st.error(f"⏳ Alerta de Vencimientos: Hay {len(df_vencer)} lote(s) vencidos o por vencer en los próximos 30 días.")
        with st.expander("Ver detalle de lotes por vencer", expanded=True):
            st.dataframe(df_vencer, use_container_width=True, hide_index=True)
            boton_exportar(df_vencer, "Alertas_Vencimiento")
    else:
        st.success("✅ No hay lotes próximos a vencer en los próximos 30 días.")

    if not df_inventario.empty:
        col_nombre = next((col for col in df_inventario.columns if col.upper() in ['NOMBRE', 'PRODUCTO', 'NOMBRE_PRODUCTO']), None)
        col_exist = next((col for col in df_inventario.columns if col.upper() in ['EXISTENCIAS', 'CANTIDAD', 'STOCK']), None)
        if col_nombre and col_exist:
            st.subheader("🏆 Top 10 Productos con Mayor Stock")
            st.bar_chart(df_inventario.groupby(col_nombre)[col_exist].sum().nlargest(10).reset_index(), x=col_nombre, y=col_exist, color=col_nombre)

        st.subheader("📋 Tabla de Existencias")
        st.dataframe(df_inventario, use_container_width=True, hide_index=True)
        boton_exportar(df_inventario, "Inventario_Actual")
    else:
        st.info("No hay registros de inventario disponibles.")

elif menu == "🚨 Puntos de Reorden":
    st.title("🚨 Puntos de Reorden y Sugerencia de Compra")
    df_reorden = (
        run_query("SELECT * FROM v_punto_reorden;")
        if rol == 'ADMINISTRADOR'
        else run_query("SELECT * FROM v_punto_reorden WHERE ID_Tienda = %s;", (id_tienda,))
    )

    # Filtrar solo los productos que realmente están en o por debajo de su punto de reorden
    if not df_reorden.empty:
        col_stock_tmp = next((c for c in df_reorden.columns if c.upper() in ['EXISTENCIAS', 'STOCK', 'STOCK_ACTUAL', 'CANTIDAD']), None)
        col_rop_tmp = next((c for c in df_reorden.columns if 'REORDEN' in c.upper() or 'MINIMO' in c.upper()), None)
        if col_stock_tmp and col_rop_tmp:
            df_reorden = df_reorden[
                pd.to_numeric(df_reorden[col_stock_tmp], errors='coerce').fillna(0)
                <= pd.to_numeric(df_reorden[col_rop_tmp], errors='coerce').fillna(0)
            ].copy()

    if not df_reorden.empty:
        col_alerta, col_btn = st.columns([3, 1])
        with col_alerta:
            st.warning(f"¡Atención! Hay {len(df_reorden)} producto(s) por debajo de su punto de reorden.")
        with col_btn:
            if rol != 'ADMINISTRADOR':
                st.button(
                    "🛒 Reponer Stock",
                    type="primary",
                    use_container_width=True,
                    on_click=cambiar_pantalla,
                    args=("📥 Gestión de Ingresos",)
                )
            else:
                st.button(
                    "📦 Ver Compras",
                    type="primary",
                    use_container_width=True,
                    on_click=cambiar_pantalla,
                    args=("📦 Análisis de Compras",)
                )

        # Parámetro configurable para el cálculo de "Cuánto comprar"
        dias_cobertura = st.slider(
            "📅 Horizonte de cobertura deseado (días de inventario a cubrir con la compra):",
            min_value=7, max_value=60, value=15, step=1
        )

        # Consultar demanda diaria promedio (últimos 30 días) usando ID_Inventario
        if rol == 'ADMINISTRADOR':
            df_demanda = run_query("""
                SELECT V.ID_Tienda, I.ID_Producto,
                       ROUND(SUM(DV.Cantidad) / 30, 2) AS Demanda_Diaria
                FROM detalle_venta DV
                JOIN venta V ON DV.ID_Venta = V.ID_Venta
                JOIN inventario I ON DV.ID_Inventario = I.ID_Inventario
                WHERE V.Fecha_Venta >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY V.ID_Tienda, I.ID_Producto;
            """)
        else:
            df_demanda = run_query("""
                SELECT V.ID_Tienda, I.ID_Producto,
                       ROUND(SUM(DV.Cantidad) / 30, 2) AS Demanda_Diaria
                FROM detalle_venta DV
                JOIN venta V ON DV.ID_Venta = V.ID_Venta
                JOIN inventario I ON DV.ID_Inventario = I.ID_Inventario
                WHERE V.ID_Tienda = %s
                  AND V.Fecha_Venta >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
                GROUP BY V.ID_Tienda, I.ID_Producto;
            """, (id_tienda,))

        df_plan = df_reorden.copy()

        if not df_demanda.empty and {'ID_Tienda', 'ID_Producto'}.issubset(df_plan.columns):
            df_plan = df_plan.drop(columns=['Demanda_Diaria'], errors='ignore')
            df_plan = df_plan.merge(df_demanda, on=['ID_Tienda', 'ID_Producto'], how='left')
            df_plan['Demanda_Diaria'] = df_plan['Demanda_Diaria'].fillna(0.0)
        elif 'Demanda_Diaria' in df_plan.columns:
            df_plan['Demanda_Diaria'] = df_plan['Demanda_Diaria'].fillna(0.0)
        else:
            df_plan['Demanda_Diaria'] = 0.0

        col_stock = next((c for c in df_plan.columns if c.upper() in ['EXISTENCIAS', 'STOCK', 'STOCK_ACTUAL', 'CANTIDAD']), None)
        col_rop = next((c for c in df_plan.columns if 'REORDEN' in c.upper() or 'MINIMO' in c.upper()), None)

        if col_stock:
            def calcular_cuando(row):
                stock = float(row[col_stock])
                dem = float(row['Demanda_Diaria'])
                if stock <= 0:
                    return "🔴 Urgente (Sin stock)"
                if dem > 0:
                    dias_rest = int(stock // dem)
                    fecha_quiebre = hoy + datetime.timedelta(days=dias_rest)
                    return f"🔴 Hoy (Quiebre en ~{dias_rest} días · {fecha_quiebre})"
                return "🟠 Hoy (Bajo punto de reorden)"

            def calcular_cuanto(row):
                stock = float(row[col_stock])
                dem = float(row['Demanda_Diaria'])
                rop = float(row[col_rop]) if col_rop and pd.notnull(row[col_rop]) else 10.0
                if dem > 0:
                    sugerido = int(-(- (dem * dias_cobertura - stock) // 1))
                else:
                    sugerido = int(max(rop * 2 - stock, rop))
                return max(sugerido, 1)

            df_plan['Cuándo Comprar'] = df_plan.apply(calcular_cuando, axis=1)
            df_plan['Cantidad Sugerida'] = df_plan.apply(calcular_cuanto, axis=1)

        st.subheader("📋 Plan de Reposición Sugerido")
        st.dataframe(df_plan, use_container_width=True, hide_index=True)

        c_exp, c_ped = st.columns(2)
        with c_exp:
            boton_exportar(df_plan, "Sugerencia_Compra")
        with c_ped:
            pedido_txt = f"PEDIDO DE COMPRA SUGERIDO - FECHA: {hoy}\n"
            pedido_txt += f"Cobertura proyectada: {dias_cobertura} días\n" + "=" * 55 + "\n"
            pedido_txt += df_plan.to_string(index=False)
            st.download_button(
                label="📄 Generar Pedido de Compra (.txt)",
                data=pedido_txt.encode("utf-8"),
                file_name=f"Pedido_Compra_{hoy}.txt",
                mime="text/plain"
            )
    else:
        st.success("Todos los productos están por encima de su punto de reorden. ¡Excelente!")

elif menu == "💰 Análisis de Ventas":
    st.title("💰 Análisis de Ventas")
    df_ventas = run_query("SELECT * FROM v_venta_total ORDER BY Fecha_Venta DESC;") if rol == 'ADMINISTRADOR' else run_query("SELECT * FROM v_venta_total WHERE ID_Tienda = %s ORDER BY Fecha_Venta DESC;", (id_tienda,))
    if not df_ventas.empty:
        col_fecha = next((col for col in df_ventas.columns if 'FECHA' in col.upper()), None)
        col_total = next((col for col in df_ventas.columns if col.upper() in ['TOTAL', 'MONTO', 'TOTAL_VENTA']), None)
        if col_fecha:
            df_ventas[col_fecha] = pd.to_datetime(df_ventas[col_fecha])
            with st.form("form_filtro_ventas"):
                c1, c2 = st.columns(2)
                inicio = c1.date_input("Fecha de Inicio", value=hace_un_mes)
                fin = c2.date_input("Fecha de Fin", value=hoy)
                st.form_submit_button("Aplicar Filtro")

            if inicio > fin:
                st.error("La fecha de inicio no puede ser mayor a la fecha de fin.")
            else:
                mask = (df_ventas[col_fecha].dt.date >= inicio) & (df_ventas[col_fecha].dt.date <= fin)
                df_ventas = df_ventas.loc[mask]

        if df_ventas.empty:
            st.warning("No hay ventas registradas en este rango de fechas.")
        else:
            if col_fecha and col_total:
                st.subheader("📈 Tendencia de Ingresos")
                st.line_chart(df_ventas.groupby(col_fecha)[col_total].sum().reset_index(), x=col_fecha, y=col_total)
                st.metric("Total Acumulado", f"${df_ventas[col_total].sum():,.2f}")
            st.dataframe(df_ventas, use_container_width=True, hide_index=True)
            boton_exportar(df_ventas, "Reporte_Ventas")
    else:
        st.info("No hay ventas registradas.")

elif menu == "📦 Análisis de Compras":
    st.title("📦 Análisis de Compras")
    df_compras = run_query("SELECT * FROM v_compra_total ORDER BY Fecha_Compra DESC;") if rol == 'ADMINISTRADOR' else run_query("SELECT * FROM v_compra_total WHERE ID_Tienda = %s ORDER BY Fecha_Compra DESC;", (id_tienda,))
    if not df_compras.empty:
        col_fecha = next((col for col in df_compras.columns if 'FECHA' in col.upper()), None)
        col_total = next((col for col in df_compras.columns if col.upper() in ['TOTAL', 'MONTO', 'TOTAL_COMPRA']), None)
        if col_fecha:
            df_compras[col_fecha] = pd.to_datetime(df_compras[col_fecha])
            with st.form("form_filtro_compras"):
                c1, c2 = st.columns(2)
                inicio = c1.date_input("Fecha de Inicio", value=hace_un_mes)
                fin = c2.date_input("Fecha de Fin", value=hoy)
                st.form_submit_button("Aplicar Filtro")

            if inicio > fin:
                st.error("La fecha de inicio no puede ser mayor a la fecha de fin.")
            else:
                mask = (df_compras[col_fecha].dt.date >= inicio) & (df_compras[col_fecha].dt.date <= fin)
                df_compras = df_compras.loc[mask]

        if df_compras.empty:
            st.warning("No hay compras registradas en este rango.")
        else:
            if col_fecha and col_total:
                st.subheader("📉 Inversión en Compras")
                st.bar_chart(df_compras.groupby(col_fecha)[col_total].sum().reset_index(), x=col_fecha, y=col_total)
            st.dataframe(df_compras, use_container_width=True, hide_index=True)
            boton_exportar(df_compras, "Reporte_Compras")
    else:
        st.info("No hay compras registradas.")

    # Comparación de costos CD vs. Proveedores
    if rol == 'ADMINISTRADOR':
        st.divider()
        st.subheader("⚖️ Comparación de Costos (CD vs. Proveedores)")
        df_costos = run_query("""
            SELECT P.Cod_Producto, P.Nombre AS Producto,
                   T.Nombre AS Tienda,
                   PR.Nombre AS Proveedor,
                   PP.Ultimo_Costo,
                   PP.Fecha_Ultimo_Costo
            FROM producto_proveedor PP
            JOIN producto P ON PP.ID_Producto = P.ID_Producto
            JOIN proveedor PR ON PP.ID_Proveedor = PR.ID_Proveedor
            JOIN tienda T ON PR.ID_Tienda = T.ID_Tienda
            WHERE PP.Estado = 'ACTIVO'
            ORDER BY P.Nombre, PP.Ultimo_Costo ASC;
        """)
        if not df_costos.empty:
            st.dataframe(df_costos, use_container_width=True, hide_index=True)
            boton_exportar(df_costos, "Comparacion_Costos")
        else:
            st.info("Aún no hay suficientes registros de costos por proveedor para comparar.")

# --- ENRUTAMIENTO DE MÓDULOS ---
elif menu == "📥 Gestión de Ingresos":
    pantalla_registrar_compra(get_connection)
elif menu == "🧾 Venta a Cliente Externo":
    pantalla_registrar_venta(get_connection)
elif menu == "🚚 Venta Interna (Al Costo)":
    pantalla_venta_interna(get_connection)
elif menu == "🗑️ Control de Mermas":
    pantalla_registrar_merma(get_connection)
elif menu == "⚙️ Panel de Administración":
    pantalla_admin(get_connection)
