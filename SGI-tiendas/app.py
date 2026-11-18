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

# --- 3. FUNCIÓN PARA NAVEGAR Y DIBUJAR TARJETAS ---
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

# --- 4. MENÚ LATERAL ---
st.sidebar.title(f"Bienvenido, {st.session_state.user_name}")
st.sidebar.caption(f"Rol: {st.session_state.user_role}")

opciones = [
    "🏠 Menú Principal",
    "📊 Dashboard de Inventario",
    "🚨 Puntos de Reorden",
    "💰 Análisis de Ventas",
    "📦 Análisis de Compras"
]

if st.session_state.user_role.upper() != 'ADMINISTRADOR':
    opciones.extend([
        "📥 Gestión de Ingresos",
        "🧾 Venta a Cliente Externo",
        "🚚 Venta Interna (Despacho)",
        "🗑️ Control de Mermas"
    ])
else:
    opciones.append("⚙️ Panel de Administración")

menu = st.sidebar.radio("Navegación", opciones, key="vista_actual")

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

# --- 5. VISTAS DE LA APLICACIÓN ---
rol = st.session_state.user_role.upper()
id_tienda = st.session_state.id_tienda
hoy = datetime.date.today()
hace_un_mes = hoy - datetime.timedelta(days=30)

if menu == "🏠 Menú Principal":
    st.markdown("<h2 style='text-align: center;'>Gestiona tu negocio de manera eficiente</h2>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    # Primera Fila: Reportes y Dashboard
    c1, c2, c3 = st.columns(3)
    with c1:
        crear_tarjeta("📦", "Inventario Global", "Ver existencias y stock de productos", "Ver inventario", "📊 Dashboard de Inventario")
    with c2:
        crear_tarjeta("💰", "Finanzas y Ventas", "Análisis de ventas e ingresos", "Ver ventas", "💰 Análisis de Ventas")
    with c3:
        crear_tarjeta("📈", "Pronósticos y Reorden", "Alertas y compras sugeridas", "Ver pronósticos", "🚨 Puntos de Reorden")

    st.markdown("<br>", unsafe_allow_html=True)

    # Segunda Fila: Operaciones (Depende del Rol)
    if rol == 'ADMINISTRADOR':
        c4, c5, c6 = st.columns(3)
        with c4:
            crear_tarjeta("📦", "Análisis de Compras", "Historial de compras registradas", "Ver compras", "📦 Análisis de Compras")
        with c5:
            crear_tarjeta("👑", "Administración", "Gestionar tiendas, usuarios y catálogo", "⚙️ Gestionar", "⚙️ Panel de Administración")
    else:
        c4, c5, c6, c7 = st.columns(4)
        with c4:
            crear_tarjeta("📥", "Ingresos", "Recibe compras y traslados", "➕ Ingresar", "📥 Gestión de Ingresos")
        with c5:
            crear_tarjeta("🧾", "Ventas Externas", "Factura productos a clientes", "💲 Vender", "🧾 Venta a Cliente Externo")
        with c6:
            crear_tarjeta("🚚", "Despachos CD", "Traslada inventario al costo", "📤 Despachar", "🚚 Venta Interna (Despacho)")
        with c7:
            crear_tarjeta("🗑️", "Mermas", "Da de baja inventario dañado", "➖ Registrar Merma", "🗑️ Control de Mermas")

elif menu == "📊 Dashboard de Inventario":
    st.title("📊 Dashboard de Inventario")
    if rol == 'ADMINISTRADOR':
        st.markdown("Vista global: Existencias en toda la red.")
        df_inventario = run_query("SELECT * FROM v_inventario_actual;")
    else:
        st.markdown(f"Vista local: Existencias de la Tienda {id_tienda}.")
        df_inventario = run_query("SELECT * FROM v_inventario_actual WHERE ID_Tienda = %s;", (id_tienda,))

    if not df_inventario.empty:
        col_nombre = next((col for col in df_inventario.columns if col.upper() in ['NOMBRE', 'PRODUCTO', 'NOMBRE_PRODUCTO']), None)
        col_exist = next((col for col in df_inventario.columns if col.upper() in ['EXISTENCIAS', 'CANTIDAD', 'STOCK']), None)
        if col_nombre and col_exist:
            st.subheader("🏆 Top 10 Productos con Mayor Stock")
            st.bar_chart(df_inventario.groupby(col_nombre)[col_exist].sum().nlargest(10).reset_index(), x=col_nombre, y=col_exist, color=col_nombre)

        st.subheader("📋 Tabla de Existencias")
        st.dataframe(df_inventario, use_container_width=True)
        boton_exportar(df_inventario, "Inventario_Actual")
    else:
        st.info("No hay registros de inventario disponibles.")

elif menu == "🚨 Puntos de Reorden":
    st.title("🚨 Control de Puntos de Reorden")
    df_reorden = run_query("SELECT * FROM v_punto_reorden;") if rol == 'ADMINISTRADOR' else run_query("SELECT * FROM v_punto_reorden WHERE ID_Tienda = %s;", (id_tienda,))
    if not df_reorden.empty:
        st.warning(f"¡Atención! Hay {len(df_reorden)} productos que necesitan reposición.")
        st.dataframe(df_reorden, use_container_width=True)
        boton_exportar(df_reorden, "Puntos_Reorden")
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
            st.dataframe(df_ventas, use_container_width=True)
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
            st.dataframe(df_compras, use_container_width=True)
            boton_exportar(df_compras, "Reporte_Compras")
    else:
        st.info("No hay compras registradas.")

# --- ENRUTAMIENTO DE MÓDULOS ---
elif menu == "📥 Gestión de Ingresos":
    pantalla_registrar_compra(get_connection)
elif menu == "🧾 Venta a Cliente Externo":
    pantalla_registrar_venta(get_connection)
elif menu == "🚚 Venta Interna (Despacho)":
    pantalla_venta_interna(get_connection)
elif menu == "🗑️ Control de Mermas":
    pantalla_registrar_merma(get_connection)
elif menu == "⚙️ Panel de Administración":
    pantalla_admin(get_connection)
