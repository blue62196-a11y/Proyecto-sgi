import streamlit as st
import mysql.connector
import pandas as pd
import hashlib

# Importamos todos los módulos de registro y administración
from form_venta import pantalla_registrar_venta
from form_compra import pantalla_registrar_compra
from form_traslado import pantalla_registrar_traslado
from form_admin import pantalla_admin

# Configuración inicial de la página
st.set_page_config(
    page_title="SGI - Sistema de Gestión de Inventario",
    page_icon="📦",
    layout="wide"
)

# --- 1. CONFIGURACIÓN DE CONEXIÓN A LA BASE DE DATOS ---
def _get_secret(key, default):
    """Obtiene un secreto de Streamlit o devuelve el valor por defecto si no existe secrets.toml."""
    try:
        return st.secrets.get(key, default)
    except Exception:
        return default

def get_connection():
    """Establece la conexión con la base de datos MySQL."""
    try:
        return mysql.connector.connect(
            host=_get_secret("DB_HOST", "localhost"),
            user=_get_secret("DB_USER", "root"),
            password=_get_secret("DB_PASSWORD", ""),
            database=_get_secret("DB_NAME", "sgi_tiendas"),
            port=int(_get_secret("DB_PORT", 3306))
        )
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return None

def run_query(query, params=None):
    """Ejecuta una consulta SQL y devuelve un DataFrame de Pandas."""
    conn = get_connection()
    if conn:
        try:
            df = pd.read_sql(query, conn, params=params)
            conn.close()
            return df
        except Exception as e:
            st.error(f"Ocurrió un error en la consulta: {e}")
            conn.close()
            return pd.DataFrame()
    return pd.DataFrame()

# --- 2. CONTROL DE SESIÓN / LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_name = ""
    st.session_state.user_role = ""
    st.session_state.id_tienda = None
    st.session_state.id_usuario = None

if not st.session_state.logged_in:
    st.title("🔐 SGI - Iniciar Sesión")
    st.markdown("Ingrese sus credenciales registradas en el sistema.")
    
    with st.form("login_form"):
        correo = st.text_input("Correo Electrónico")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Ingresar")
        
        if submit:
            hashed_input = hashlib.sha256(password.encode()).hexdigest()

            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT U.ID_Usuario, U.Nombre, U.ID_Tienda, R.Nombre as Rol, U.Password_Hash FROM usuario U JOIN rol R ON U.ID_Rol = R.ID_Rol WHERE U.Correo = %s", (correo,))
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

# --- 3. MENÚ LATERAL Y NAVEGACIÓN ---
st.sidebar.title(f"Bienvenido, {st.session_state.user_name}")
st.sidebar.caption(f"Rol: {st.session_state.user_role}")

opciones = [
    "📊 Dashboard de Inventario",
    "🚨 Puntos de Reorden",
    "⏳ Próximos a Vencer",
    "⚖️ Comparativa Costo CD",
    "💰 Análisis de Ventas",
    "📦 Análisis de Compras",
]

# Distribuimos los accesos según el rol
if st.session_state.user_role.upper() != 'ADMINISTRADOR':
    opciones.append("🛒 Registrar compra")
    opciones.append("🧾 Registrar venta")
    opciones.append("🚚 Registrar traslado")
else:
    opciones.append("⚙️ Panel de Administración")

menu = st.sidebar.radio("Navegación", opciones)

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

# --- 4. VISTAS DE LA APLICACIÓN ---
rol = st.session_state.user_role.upper()
id_tienda = st.session_state.id_tienda

if menu == "📊 Dashboard de Inventario":
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
            df_chart = df_inventario.groupby(col_nombre)[col_exist].sum().nlargest(10).reset_index()
            st.bar_chart(df_chart, x=col_nombre, y=col_exist, color=col_nombre)
            
        st.subheader("📋 Tabla de Existencias")
        st.dataframe(df_inventario, use_container_width=True)
    else:
        st.info("No hay registros de inventario disponibles.")

elif menu == "🚨 Puntos de Reorden":
    st.title("🚨 Control de Puntos de Reorden")
    
    if rol == 'ADMINISTRADOR':
        df_reorden = run_query("SELECT * FROM v_punto_reorden;")
    else:
        df_reorden = run_query("SELECT * FROM v_punto_reorden WHERE ID_Tienda = %s;", (id_tienda,))
        
    if not df_reorden.empty:
        df_reorden["Cantidad_A_Comprar"] = (
            df_reorden["Punto_Reorden"] - df_reorden["Existencias"]
        ).clip(lower=0).round(2)

        necesitan_compra = df_reorden[df_reorden["Estado"] == "COMPRAR"]
        if not necesitan_compra.empty:
            st.warning(f"¡Atención! Hay {len(necesitan_compra)} productos que necesitan reposición.")
        else:
            st.success("Todos los productos están por encima de su punto de reorden. ¡Excelente!")

        st.dataframe(df_reorden, use_container_width=True)
    else:
        st.info("No hay productos configurados con punto de reorden.")

elif menu == "⏳ Próximos a Vencer":
    st.title("⏳ Productos Próximos a Vencer")
    dias_limite = st.slider("Mostrar lotes que vencen dentro de los próximos (días):", min_value=7, max_value=365, value=90)

    if rol == 'ADMINISTRADOR':
        df_vencer = run_query("SELECT * FROM v_proximos_vencer ORDER BY Dias_Restantes ASC;")
    else:
        df_vencer = run_query("SELECT * FROM v_proximos_vencer WHERE ID_Tienda = %s ORDER BY Dias_Restantes ASC;", (id_tienda,))

    if not df_vencer.empty:
        df_filtrado = df_vencer[df_vencer["Dias_Restantes"] <= dias_limite]
        vencidos = df_filtrado[df_filtrado["Dias_Restantes"] <= 0]
        por_vencer = df_filtrado[(df_filtrado["Dias_Restantes"] > 0) & (df_filtrado["Dias_Restantes"] <= 30)]

        c1, c2, c3 = st.columns(3)
        c1.metric("Lotes en el rango", len(df_filtrado))
        c2.metric("Vencen en ≤ 30 días", len(por_vencer))
        c3.metric("Ya vencidos", len(vencidos))

        if not df_filtrado.empty:
            st.dataframe(df_filtrado, use_container_width=True)
        else:
            st.success(f"No hay lotes con vencimiento dentro de los próximos {dias_limite} días.")
    else:
        st.info("No hay productos con fecha de vencimiento registrada.")

elif menu == "⚖️ Comparativa Costo CD":
    st.title("⚖️ Comparativa de Costos: CD vs Otros Proveedores")

    if rol == 'ADMINISTRADOR':
        df_costo = run_query("SELECT * FROM v_costo_cd;")
    else:
        df_costo = run_query("SELECT * FROM v_costo_cd WHERE ID_Tienda = %s;", (id_tienda,))

    if not df_costo.empty:
        conviene_cd = len(df_costo[df_costo["Decision"] == "CD conviene"])
        no_conviene_cd = len(df_costo[df_costo["Decision"] == "CD no conviene"])

        c1, c2 = st.columns(2)
        c1.metric("Conviene comprar al CD", conviene_cd)
        c2.metric("Conviene otro proveedor", no_conviene_cd)

        st.dataframe(df_costo, use_container_width=True)
    else:
        st.info("No hay datos de costos comparativos disponibles.")

elif menu == "💰 Análisis de Ventas":
    st.title("💰 Análisis de Ventas")
    
    if rol == 'ADMINISTRADOR':
        df_ventas = run_query("SELECT * FROM v_venta_total ORDER BY Fecha_Venta DESC;")
    else:
        df_ventas = run_query("SELECT * FROM v_venta_total WHERE ID_Tienda = %s ORDER BY Fecha_Venta DESC;", (id_tienda,))
        
    if not df_ventas.empty:
        col_fecha = next((col for col in df_ventas.columns if 'FECHA' in col.upper()), None)
        col_total = next((col for col in df_ventas.columns if col.upper() in ['TOTAL', 'MONTO', 'TOTAL_VENTA']), None)
        
        if col_fecha and col_total:
            st.subheader("📈 Tendencia de Ingresos en el Tiempo")
            df_ventas[col_fecha] = pd.to_datetime(df_ventas[col_fecha])
            tendencia = df_ventas.groupby(col_fecha)[col_total].sum().reset_index()
            st.line_chart(tendencia, x=col_fecha, y=col_total)
            st.metric("Total Acumulado (Registros mostrados)", f"${tendencia[col_total].sum():,.2f}")

        st.subheader("📋 Historial de Registros")
        st.dataframe(df_ventas, use_container_width=True)
    else:
        st.info("No hay ventas registradas.")

elif menu == "📦 Análisis de Compras":
    st.title("📦 Análisis de Compras")
    
    if rol == 'ADMINISTRADOR':
        df_compras = run_query("SELECT * FROM v_compra_total ORDER BY Fecha_Compra DESC;")
    else:
        df_compras = run_query("SELECT * FROM v_compra_total WHERE ID_Tienda = %s ORDER BY Fecha_Compra DESC;", (id_tienda,))
        
    if not df_compras.empty:
        col_fecha = next((col for col in df_compras.columns if 'FECHA' in col.upper()), None)
        col_total = next((col for col in df_compras.columns if col.upper() in ['TOTAL', 'MONTO', 'TOTAL_COMPRA']), None)
        
        if col_fecha and col_total:
            st.subheader("📉 Inversión en Compras en el Tiempo")
            df_compras[col_fecha] = pd.to_datetime(df_compras[col_fecha])
            tendencia = df_compras.groupby(col_fecha)[col_total].sum().reset_index()
            st.bar_chart(tendencia, x=col_fecha, y=col_total)

        st.subheader("📋 Historial de Registros")
        st.dataframe(df_compras, use_container_width=True)
    else:
        st.info("No hay compras registradas.")

elif menu == "🛒 Registrar compra":
    pantalla_registrar_compra(get_connection)

elif menu == "🧾 Registrar venta":
    pantalla_registrar_venta(get_connection)
    
elif menu == "🚚 Registrar traslado": 
    pantalla_registrar_traslado(get_connection)

elif menu == "⚙️ Panel de Administración":
    pantalla_admin(get_connection)
