if not st.session_state.logged_in:
    # Espaciado superior para centrar verticalmente
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Columnas para centrar la tarjeta de login
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
