import streamlit as st
import mysql.connector
import pandas as pd
import hashlib
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
def get_connection():
    """Establece la conexión con la base de datos MySQL."""
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

opciones = ["📊 Dashboard de Inventario", "🚨 Puntos de Reorden", "💰 Análisis de Ventas", "📦 Análisis de Compras"]

if st.session_state.user_role.upper() != 'ADMINISTRADOR':
    opciones.append("🛒 Registrar compra")
    opciones.append("🧾 Registrar venta")
    opciones.append("🚚 Registrar traslado")

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
            
            # CORRECCIÓN: Agregamos el parámetro color=col_nombre para que Streamlit asigne colores distintos
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
        st.warning(f"¡Atención! Hay {len(df_reorden)} productos que necesitan reposición.")
        st.dataframe(df_reorden, use_container_width=True)
    else:
        st.success("Todos los productos están por encima de su punto de reorden. ¡Excelente!")

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
