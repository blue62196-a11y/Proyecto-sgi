import streamlit as st
import hashlib

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

def ejecutar_insert(get_connection, sql, params):
    conn = get_connection()
    if conn:
        try:
            cur = conn.cursor()
            cur.execute(sql, params)
            conn.commit()
            return True
        except Exception as e:
            st.error(f"Error en la base de datos: {e}")
            return False
        finally:
            conn.close()
    return False

def pantalla_admin(get_connection):
    st.title("⚙️ Panel de Administración")
    st.markdown("Gestión de catálogos, usuarios y sucursales.")

    # Creamos 3 pestañas para organizar los formularios
    tab_prod, tab_user, tab_tienda = st.tabs(["📦 Productos", "👥 Usuarios", "🏪 Tiendas"])

    # ----------------- CRUD PRODUCTOS -----------------
    with tab_prod:
        st.subheader("Registrar Nuevo Producto")
        with st.form("form_prod"):
            c1, c2 = st.columns(2)
            cod = c1.text_input("Código de Producto (Ej: PROD-001)")
            nom = c2.text_input("Nombre del Producto")
            uni = st.selectbox("Unidad de Medida", ["Unidad", "Caja", "Galon", "Paquete", "Libra", "Kilogramo"])
            
            if st.form_submit_button("Guardar Producto"):
                if cod and nom:
                    sql = "INSERT INTO producto (Cod_Producto, Nombre, Unidad_Medida, Estado_Producto) VALUES (%s, %s, %s, 'ACTIVO')"
                    if ejecutar_insert(get_connection, sql, (cod, nom, uni)):
                        st.success(f"Producto '{nom}' agregado al catálogo global.")
                else:
                    st.warning("El código y nombre son obligatorios.")

    # ----------------- CRUD USUARIOS -----------------
    with tab_user:
        st.subheader("Crear Nuevo Usuario")
        roles = _consultar(get_connection, "SELECT ID_Rol, Nombre FROM rol")
        tiendas = _consultar(get_connection, "SELECT ID_Tienda, Nombre FROM tienda")
        
        with st.form("form_user"):
            c1, c2 = st.columns(2)
            nom_u = c1.text_input("Nombre Completo")
            correo_u = c2.text_input("Correo Electrónico")
            
            c3, c4 = st.columns(2)
            pass_u = c3.text_input("Contraseña (se guardará encriptada)", type="password")
            
            rol_opts = {r['Nombre']: r['ID_Rol'] for r in roles}
            tienda_opts = {t['Nombre']: t['ID_Tienda'] for t in tiendas}
            
            sel_rol = c4.selectbox("Rol del Usuario", list(rol_opts.keys()))
            sel_tienda = st.selectbox("Asignar a Tienda/CD", list(tienda_opts.keys()))
            
            if st.form_submit_button("Crear Usuario"):
                if nom_u and correo_u and pass_u:
                    # Encriptamos la contraseña con SHA-256 antes de guardarla
                    pass_hash = hashlib.sha256(pass_u.encode()).hexdigest()
                    sql = "INSERT INTO usuario (Nombre, Correo, Password_Hash, ID_Rol, ID_Tienda) VALUES (%s, %s, %s, %s, %s)"
                    if ejecutar_insert(get_connection, sql, (nom_u, correo_u, pass_hash, rol_opts[sel_rol], tienda_opts[sel_tienda])):
                        st.success(f"Usuario {nom_u} creado exitosamente. Ya puede iniciar sesión.")
                else:
                    st.warning("Completa todos los datos del usuario.")

    # ----------------- CRUD TIENDAS -----------------
    with tab_tienda:
        st.subheader("Registrar Nueva Tienda / Sucursal")
        with st.form("form_tienda"):
            nom_t = st.text_input("Nombre de la Tienda (Ej: Tienda Santa Ana)")
            
            if st.form_submit_button("Crear Tienda"):
                if nom_t:
                    sql = "INSERT INTO tienda (Nombre) VALUES (%s)"
                    if ejecutar_insert(get_connection, sql, (nom_t,)):
                        st.success(f"Sucursal '{nom_t}' habilitada en la red.")
                else:
                    st.warning("El nombre de la tienda es obligatorio.")
