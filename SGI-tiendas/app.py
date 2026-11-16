import streamlit as st
import mysql.connector
import pandas as pd
import hashlib
from form_venta import pantalla_registrar_venta
from form_compra import pantalla_registrar_compra
from form_traslado import pantalla_registrar_traslado

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
            # 1. Encriptamos la contraseña que el usuario escribe en la pantalla
            hashed_input = hashlib.sha256(password.encode()).hexdigest()

            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT U.ID_Usuario, U.Nombre, U.ID_Tienda, R.Nombre as Rol, U.Password_Hash FROM usuario U JOIN rol R ON U.ID_Rol = R.ID_Rol WHERE U.Correo = %s", (correo,))
                user = cursor.fetchone()
                conn.close()
                
                # 2. Comparamos de forma segura: Hash contra Hash
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

opciones = ["📊 Inventario Actual", "🚨 Puntos de Reorden", "💰 Ventas Totales", "📦 Compras Totales"]

# Si NO es administrador, le agregamos los 3 formularios de registro a la vez
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

if menu == "📊 Inventario Actual":
    st.title("📊 Inventario Actual")
    
    if rol == 'ADMINISTRADOR':
        st.markdown("Vista global: Existencias de todas las tiendas y el Centro de Distribución.")
        df_inventario = run_query("SELECT * FROM v_inventario_actual;")
    else:
        st.markdown(f"Vista local: Existencias de la Tienda {id_tienda}.")
        df_inventario = run_query("SELECT * FROM v_inventario_actual WHERE ID_Tienda = %s;", (id_tienda,))
        
    if not df_inventario.empty:
        st.dataframe(df_inventario, use_container_width=True)
    else:
        st.info("No hay registros de inventario disponibles.")

elif menu == "🚨 Puntos de Reorden":
    st.title("🚨 Control de Puntos de Reorden")
    
    if rol == 'ADMINISTRADOR':
        st.markdown("Vista global: Productos que requieren reposición en toda la red.")
        df_reorden = run_query("SELECT * FROM v_punto_reorden;")
    else:
        st.markdown(f"Vista local: Productos que requieren reposición en la Tienda {id_tienda}.")
        df_reorden = run_query("SELECT * FROM v_punto_reorden WHERE ID_Tienda = %s;", (id_tienda,))
        
    if not df_reorden.empty:
        st.dataframe(df_reorden, use_container_width=True)
    else:
        st.info("No hay datos de punto de reorden.")

elif menu == "💰 Ventas Totales":
    st.title("💰 Historial de Ventas")
    
    if rol == 'ADMINISTRADOR':
        df_ventas = run_query("SELECT * FROM v_venta_total ORDER BY Fecha_Venta DESC;")
    else:
        df_ventas = run_query("SELECT * FROM v_venta_total WHERE ID_Tienda = %s ORDER BY Fecha_Venta DESC;", (id_tienda,))
        
    if not df_ventas.empty:
        st.dataframe(df_ventas, use_container_width=True)
    else:
        st.info("No hay ventas registradas.")

elif menu == "📦 Compras Totales":
    st.title("📦 Historial de Compras")
    
    if rol == 'ADMINISTRADOR':
        df_compras = run_query("SELECT * FROM v_compra_total ORDER BY Fecha_Compra DESC;")
    else:
        df_compras = run_query("SELECT * FROM v_compra_total WHERE ID_Tienda = %s ORDER BY Fecha_Compra DESC;", (id_tienda,))
        
    if not df_compras.empty:
        st.dataframe(df_compras, use_container_width=True)
    else:
        st.info("No hay compras registradas.")

elif menu == "🛒 Registrar compra":
    pantalla_registrar_compra(get_connection)

elif menu == "🧾 Registrar venta":
    pantalla_registrar_venta(get_connection)
    
elif menu == "🚚 Registrar traslado": 
    pantalla_registrar_traslado(get_connection)
