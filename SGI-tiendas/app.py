import streamlit as st
import mysql.connector
import pandas as pd
import hashlib
import datetime 
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

def boton_exportar(df, nombre_archivo):
    """Genera un botón estandarizado para descargar DataFrames en CSV."""
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

# Calculamos los últimos 30 días para que el calendario no empiece vacío
hoy = datetime.date.today()
hace_un_mes = hoy - datetime.timedelta(days=30)

if menu == "📊 Dashboard de Inventario":
    st.title("📊 Dashboard de Inventario")
    
    if rol == 'ADMINISTRADOR':
        st.markdown("Vista global: Existencias en toda la red.")
        df_inventario = run_query("SELECT * FROM v_inventario_actual;")
    else:
        st.markdown(
