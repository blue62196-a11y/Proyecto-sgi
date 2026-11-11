import streamlit as st
import mysql.connector
import pandas as pd

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
        # Si usas Streamlit Cloud, los datos se leen de st.secrets. 
        # Si estás en local, puedes cambiar los valores por defecto o usar un archivo .streamlit/secrets.toml
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

if not st.session_state.logged_in:
    st.title("🔐 SGI - Iniciar Sesión")
    st.markdown("Ingrese sus credenciales registradas en el sistema.")
    
    with st.form("login_form"):
        correo = st.text_input("Correo Electrónico")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Ingresar")
        
        if submit:
            query = """
                U.ID_Usuario, U.Nombre, U.ID_Tienda, R.Nombre as Rol 
                FROM usuario U 
                JOIN rol R ON U.ID_Rol = R.ID_Rol 
                WHERE U.Correo = %s AND U.Estado_Usuario = 'ACTIVO'
            """
            # Nota: Para producción recuerda verificar el hash de la contraseña.
            conn = get_connection()
            if conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT U.ID_Usuario, U.Nombre, U.ID_Tienda, R.Nombre as Rol, U.Password_Hash FROM usuario U JOIN rol R ON U.ID_Rol = R.ID_Rol WHERE U.Correo = %s", (correo,))
                user = cursor.fetchone()
                conn.close()
                
                if user:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user["Nombre"]
                    st.session_state.user_role = user["Rol"]
                    st.session_state.id_tienda = user["ID_Tienda"]
                    st.rerun()
                else:
                    st.error("Correo o contraseña incorrectos.")
    st.stop()

# --- 3. MENÚ LATERAL Y NAVEGACIÓN ---
st.sidebar.title(f"Bienvenido, {st.session_state.user_name}")
st.sidebar.caption(f"Rol: {st.session_state.user_role}")

menu = st.sidebar.radio(
    "Navegación",
    ["📊 Inventario Actual", "🚨 Puntos de Reorden", "💰 Ventas Totales", "📦 Compras Totales"]
)

if st.sidebar.button("Cerrar Sesión"):
    st.session_state.logged_in = False
    st.rerun()

# --- 4. VISTAS DE LA APLICACIÓN ---

if menu == "📊 Inventario Actual":
    st.title("📊 Inventario Actual por Tienda")
    st.markdown("Consulta las existencias actuales de productos basadas en la vista `v_inventario_actual`.")
    
    df_inventario = run_query("SELECT * FROM v_inventario_actual;")
    if not df_inventario.empty:
        st.dataframe(df_inventario, use_container_width=True)
    else:
        st.info("No hay registros de inventario disponibles.")

elif menu == "🚨 Puntos de Reorden":
    st.title("🚨 Control de Puntos de Reorden")
    st.markdown("Productos que han alcanzado o bajado de su punto de reorden y requieren reposición.")
    
    df_reorden = run_query("SELECT * FROM v_punto_reorden;")
    if not df_reorden.empty:
        # Filtro visual para destacar los que necesitan compra urgente
        st.dataframe(df_reorden, use_container_width=True)
    else:
        st.info("No hay datos de punto de reorden.")

elif menu == "💰 Ventas Totales":
    st.title("💰 Historial de Ventas")
    df_ventas = run_query("SELECT * FROM v_venta_total ORDER BY Fecha_Venta DESC;")
    if not df_ventas.empty:
        st.dataframe(df_ventas, use_container_width=True)
    else:
        st.info("No hay ventas registradas.")

elif menu == "📦 Compras Totales":
    st.title("📦 Historial de Compras a Proveedores")
    df_compras = run_query("SELECT * FROM v_compra_total ORDER BY Fecha_Compra DESC;")
    if not df_compras.empty:
        st.dataframe(df_compras, use_container_width=True)
    else:
        st.info("No hay compras registradas.")
