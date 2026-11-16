import streamlit as st
import pandas as pd
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


def _ejecutar(get_connection, sql, params=()):
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


def _tab_productos(get_connection):
    st.subheader("Catálogo de Productos")
    categorias = _consultar(get_connection, "SELECT ID_Categoria, Nombre FROM categoria ORDER BY Nombre")
    cat_opts = {c["Nombre"]: c["ID_Categoria"] for c in categorias}

    productos = _consultar(
        get_connection,
        """
        SELECT P.ID_Producto, P.Cod_Producto, P.Nombre, P.Descripcion,
               P.Unidad_Medida, C.Nombre AS Categoria, P.Estado_Producto
        FROM producto P
        JOIN categoria C ON C.ID_Categoria = P.ID_Categoria
        ORDER BY P.ID_Producto DESC
        """,
    )
    if productos:
        st.dataframe(pd.DataFrame(productos), use_container_width=True)

    c_crear, c_editar = st.columns(2)
    with c_crear:
        st.markdown("#### Registrar Nuevo Producto")
        if not cat_opts:
            st.warning("Primero debes crear al menos una categoría.")
        else:
            with st.form("form_prod_crear"):
                c1, c2 = st.columns(2)
                cod = c1.text_input("Código de Producto (Ej: PROD-001)")
                nom = c2.text_input("Nombre del Producto")
                c3, c4 = st.columns(2)
                uni = c3.selectbox("Unidad de Medida", ["Unidad", "Frasco", "Caja", "Galon", "Paquete", "Libra", "Kilogramo"])
                sel_cat = c4.selectbox("Categoría", list(cat_opts.keys()))
                desc = st.text_input("Descripción (opcional)")

                if st.form_submit_button("Guardar Producto"):
                    if cod and nom:
                        sql = """
                            INSERT INTO producto (Cod_Producto, Nombre, Descripcion, Unidad_Medida, Estado_Producto, ID_Categoria)
                            VALUES (%s, %s, %s, %s, 'ACTIVO', %s)
                        """
                        if _ejecutar(get_connection, sql, (cod.strip(), nom.strip(), desc.strip() or None, uni, cat_opts[sel_cat])):
                            st.success(f"Producto '{nom}' agregado al catálogo global.")
                            st.rerun()
                    else:
                        st.warning("El código y nombre son obligatorios.")

    with c_editar:
        st.markdown("#### Editar / Cambiar Estado")
        if productos and cat_opts:
            prod_opts = {f"{p['Cod_Producto']} - {p['Nombre']}": p for p in productos}
            sel_p_label = st.selectbox("Seleccionar Producto", list(prod_opts.keys()), key="edit_prod_sel")
            p_actual = prod_opts[sel_p_label]

            with st.form("form_prod_editar"):
                nom_e = st.text_input("Nombre", value=p_actual["Nombre"])
                desc_e = st.text_input("Descripción", value=p_actual["Descripcion"] or "")
                unidades = ["Unidad", "Frasco", "Caja", "Galon", "Paquete", "Libra", "Kilogramo"]
                idx_u = unidades.index(p_actual["Unidad_Medida"]) if p_actual["Unidad_Medida"] in unidades else 0
                c1, c2 = st.columns(2)
                uni_e = c1.selectbox("Unidad de Medida", unidades, index=idx_u)
                cat_names = list(cat_opts.keys())
                idx_c = cat_names.index(p_actual["Categoria"]) if p_actual["Categoria"] in cat_names else 0
                cat_e = c2.selectbox("Categoría", cat_names, index=idx_c)
                estado_e = st.selectbox("Estado", ["ACTIVO", "INACTIVO"], index=0 if p_actual["Estado_Producto"] == "ACTIVO" else 1)

                if st.form_submit_button("Actualizar Producto"):
                    if nom_e:
                        sql = """
                            UPDATE producto
                            SET Nombre = %s, Descripcion = %s, Unidad_Medida = %s, ID_Categoria = %s, Estado_Producto = %s
                            WHERE ID_Producto = %s
                        """
                        if _ejecutar(get_connection, sql, (nom_e.strip(), desc_e.strip() or None, uni_e, cat_opts[cat_e], estado_e, p_actual["ID_Producto"])):
                            st.success("Producto actualizado.")
                            st.rerun()
                    else:
                        st.warning("El nombre es obligatorio.")


def _tab_categorias(get_connection):
    st.subheader("Gestión de Categorías")
    categorias = _consultar(get_connection, "SELECT ID_Categoria, Nombre, Descripcion FROM categoria ORDER BY ID_Categoria")
    if categorias:
        st.dataframe(pd.DataFrame(categorias), use_container_width=True)

    c_crear, c_editar = st.columns(2)
    with c_crear:
        st.markdown("#### Nueva Categoría")
        with st.form("form_cat_crear"):
            nom_c = st.text_input("Nombre de la Categoría")
            desc_c = st.text_input("Descripción (opcional)")
            if st.form_submit_button("Guardar Categoría"):
                if nom_c:
                    sql = "INSERT INTO categoria (Nombre, Descripcion) VALUES (%s, %s)"
                    if _ejecutar(get_connection, sql, (nom_c.strip(), desc_c.strip() or None)):
                        st.success(f"Categoría '{nom_c}' creada.")
                        st.rerun()
                else:
                    st.warning("El nombre de la categoría es obligatorio.")

    with c_editar:
        st.markdown("#### Editar Categoría")
        if categorias:
            cat_opts = {c["Nombre"]: c for c in categorias}
            sel_c = st.selectbox("Seleccionar Categoría", list(cat_opts.keys()), key="edit_cat_sel")
            c_actual = cat_opts[sel_c]
            with st.form("form_cat_editar"):
                nom_ce = st.text_input("Nombre", value=c_actual["Nombre"])
                desc_ce = st.text_input("Descripción", value=c_actual["Descripcion"] or "")
                if st.form_submit_button("Actualizar Categoría"):
                    if nom_ce:
                        sql = "UPDATE categoria SET Nombre = %s, Descripcion = %s WHERE ID_Categoria = %s"
                        if _ejecutar(get_connection, sql, (nom_ce.strip(), desc_ce.strip() or None, c_actual["ID_Categoria"])):
                            st.success("Categoría actualizada.")
                            st.rerun()
                    else:
                        st.warning("El nombre es obligatorio.")


def _tab_proveedores(get_connection):
    st.subheader("Gestión de Proveedores")
    tiendas = _consultar(get_connection, "SELECT ID_Tienda, Nombre FROM tienda ORDER BY ID_Tienda")
    tienda_opts = {t["Nombre"]: t["ID_Tienda"] for t in tiendas}

    proveedores = _consultar(
        get_connection,
        """
        SELECT PR.ID_Proveedor, T.Nombre AS Tienda, PR.Nombre, PR.DUI_NIT,
               PR.Telefono, PR.Correo, PR.Direccion
        FROM proveedor PR
        JOIN tienda T ON T.ID_Tienda = PR.ID_Tienda
        ORDER BY PR.ID_Proveedor DESC
        """,
    )
    if proveedores:
        st.dataframe(pd.DataFrame(proveedores), use_container_width=True)

    c_crear, c_editar = st.columns(2)
    with c_crear:
        st.markdown("#### Registrar Proveedor")
        if not tienda_opts:
            st.warning("No hay tiendas registradas.")
        else:
            with st.form("form_prov_crear"):
                sel_t = st.selectbox("Tienda / CD al que suple", list(tienda_opts.keys()))
                nom_pr = st.text_input("Nombre o Razón Social")
                c1, c2 = st.columns(2)
                nit_pr = c1.text_input("DUI / NIT (opcional)")
                tel_pr = c2.text_input("Teléfono (opcional)")
                cor_pr = st.text_input("Correo (opcional)")
                dir_pr = st.text_input("Dirección (opcional)")

                if st.form_submit_button("Guardar Proveedor"):
                    if nom_pr:
                        sql = """
                            INSERT INTO proveedor (ID_Tienda, Nombre, DUI_NIT, Telefono, Correo, Direccion)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """
                        params = (
                            tienda_opts[sel_t],
                            nom_pr.strip(),
                            nit_pr.strip() or None,
                            tel_pr.strip() or None,
                            cor_pr.strip() or None,
                            dir_pr.strip() or None,
                        )
                        if _ejecutar(get_connection, sql, params):
                            st.success(f"Proveedor '{nom_pr}' registrado.")
                            st.rerun()
                    else:
                        st.warning("El nombre del proveedor es obligatorio.")

    with c_editar:
        st.markdown("#### Editar Proveedor")
        if proveedores:
            prov_opts = {f"{pr['ID_Proveedor']} - {pr['Nombre']} ({pr['Tienda']})": pr for pr in proveedores}
            sel_pr = st.selectbox("Seleccionar Proveedor", list(prov_opts.keys()), key="edit_prov_sel")
            pr_actual = prov_opts[sel_pr]

            with st.form("form_prov_editar"):
                nom_pre = st.text_input("Nombre o Razón Social", value=pr_actual["Nombre"])
                c1, c2 = st.columns(2)
                nit_pre = c1.text_input("DUI / NIT", value=pr_actual["DUI_NIT"] or "")
                tel_pre = c2.text_input("Teléfono", value=pr_actual["Telefono"] or "")
                cor_pre = st.text_input("Correo", value=pr_actual["Correo"] or "")
                dir_pre = st.text_input("Dirección", value=pr_actual["Direccion"] or "")

                if st.form_submit_button("Actualizar Proveedor"):
                    if nom_pre:
                        sql = """
                            UPDATE proveedor
                            SET Nombre = %s, DUI_NIT = %s, Telefono = %s, Correo = %s, Direccion = %s
                            WHERE ID_Proveedor = %s
                        """
                        params = (
                            nom_pre.strip(),
                            nit_pre.strip() or None,
                            tel_pre.strip() or None,
                            cor_pre.strip() or None,
                            dir_pre.strip() or None,
                            pr_actual["ID_Proveedor"],
                        )
                        if _ejecutar(get_connection, sql, params):
                            st.success("Proveedor actualizado.")
                            st.rerun()
                    else:
                        st.warning("El nombre es obligatorio.")


def _tab_usuarios(get_connection):
    st.subheader("Gestión de Usuarios")
    roles = _consultar(get_connection, "SELECT ID_Rol, Nombre FROM rol")
    tiendas = _consultar(get_connection, "SELECT ID_Tienda, Nombre FROM tienda")
    usuarios = _consultar(
        get_connection,
        """
        SELECT U.ID_Usuario, U.Nombre, U.Correo, R.Nombre AS Rol,
               T.Nombre AS Tienda, U.Estado_Usuario
        FROM usuario U
        JOIN rol R ON R.ID_Rol = U.ID_Rol
        JOIN tienda T ON T.ID_Tienda = U.ID_Tienda
        ORDER BY U.ID_Usuario
        """,
    )
    if usuarios:
        st.dataframe(pd.DataFrame(usuarios), use_container_width=True)

    c_crear, c_editar = st.columns(2)
    with c_crear:
        st.markdown("#### Crear Nuevo Usuario")
        rol_opts = {r["Nombre"]: r["ID_Rol"] for r in roles}
        tienda_opts = {t["Nombre"]: t["ID_Tienda"] for t in tiendas}

        with st.form("form_user_crear"):
            c1, c2 = st.columns(2)
            nom_u = c1.text_input("Nombre Completo")
            correo_u = c2.text_input("Correo Electrónico")
            c3, c4 = st.columns(2)
            pass_u = c3.text_input("Contraseña (se guardará encriptada)", type="password")
            sel_rol = c4.selectbox("Rol del Usuario", list(rol_opts.keys()))
            sel_tienda = st.selectbox("Asignar a Tienda/CD", list(tienda_opts.keys()))

            if st.form_submit_button("Crear Usuario"):
                if nom_u and correo_u and pass_u:
                    pass_hash = hashlib.sha256(pass_u.encode()).hexdigest()
                    sql = "INSERT INTO usuario (Nombre, Correo, Password_Hash, ID_Rol, ID_Tienda) VALUES (%s, %s, %s, %s, %s)"
                    if _ejecutar(get_connection, sql, (nom_u.strip(), correo_u.strip(), pass_hash, rol_opts[sel_rol], tienda_opts[sel_tienda])):
                        st.success(f"Usuario {nom_u} creado exitosamente. Ya puede iniciar sesión.")
                        st.rerun()
                else:
                    st.warning("Completa todos los datos del usuario.")

    with c_editar:
        st.markdown("#### Editar Estado / Asignación")
        if usuarios and rol_opts and tienda_opts:
            user_opts = {f"{u['Nombre']} ({u['Correo']})": u for u in usuarios}
            sel_u = st.selectbox("Seleccionar Usuario", list(user_opts.keys()), key="edit_user_sel")
            u_actual = user_opts[sel_u]

            with st.form("form_user_editar"):
                rol_names = list(rol_opts.keys())
                tienda_names = list(tienda_opts.keys())
                idx_r = rol_names.index(u_actual["Rol"]) if u_actual["Rol"] in rol_names else 0
                idx_t = tienda_names.index(u_actual["Tienda"]) if u_actual["Tienda"] in tienda_names else 0
                rol_ue = st.selectbox("Rol", rol_names, index=idx_r)
                tienda_ue = st.selectbox("Tienda/CD", tienda_names, index=idx_t)
                estado_ue = st.selectbox("Estado", ["ACTIVO", "INACTIVO"], index=0 if u_actual["Estado_Usuario"] == "ACTIVO" else 1)

                if st.form_submit_button("Actualizar Usuario"):
                    sql = "UPDATE usuario SET ID_Rol = %s, ID_Tienda = %s, Estado_Usuario = %s WHERE ID_Usuario = %s"
                    if _ejecutar(get_connection, sql, (rol_opts[rol_ue], tienda_opts[tienda_ue], estado_ue, u_actual["ID_Usuario"])):
                        st.success("Usuario actualizado.")
                        st.rerun()


def _tab_tiendas(get_connection):
    st.subheader("Gestión de Tiendas / Sucursales")
    tiendas = _consultar(get_connection, "SELECT ID_Tienda, Nombre, Tipo, Direccion, Telefono FROM tienda ORDER BY ID_Tienda")
    if tiendas:
        st.dataframe(pd.DataFrame(tiendas), use_container_width=True)

    c_crear, c_editar = st.columns(2)
    with c_crear:
        st.markdown("#### Registrar Nueva Tienda / Sucursal")
        with st.form("form_tienda_crear"):
            c1, c2 = st.columns(2)
            nom_t = c1.text_input("Nombre de la Tienda (Ej: Tienda Santa Ana)")
            tipo_t = c2.selectbox("Tipo", ["TIENDA", "CD"])
            dir_t = st.text_input("Dirección (opcional)")
            tel_t = st.text_input("Teléfono (opcional)")

            if st.form_submit_button("Crear Tienda"):
                if nom_t:
                    sql = "INSERT INTO tienda (Nombre, Tipo, Direccion, Telefono) VALUES (%s, %s, %s, %s)"
                    if _ejecutar(get_connection, sql, (nom_t.strip(), tipo_t, dir_t.strip() or None, tel_t.strip() or None)):
                        st.success(f"Sucursal '{nom_t}' habilitada en la red.")
                        st.rerun()
                else:
                    st.warning("El nombre de la tienda es obligatorio.")

    with c_editar:
        st.markdown("#### Editar Tienda")
        if tiendas:
            t_opts = {f"{t['Nombre']} ({t['Tipo']})": t for t in tiendas}
            sel_t = st.selectbox("Seleccionar Tienda", list(t_opts.keys()), key="edit_tienda_sel")
            t_actual = t_opts[sel_t]

            with st.form("form_tienda_editar"):
                nom_te = st.text_input("Nombre", value=t_actual["Nombre"])
                dir_te = st.text_input("Dirección", value=t_actual["Direccion"] or "")
                tel_te = st.text_input("Teléfono", value=t_actual["Telefono"] or "")

                if st.form_submit_button("Actualizar Tienda"):
                    if nom_te:
                        sql = "UPDATE tienda SET Nombre = %s, Direccion = %s, Telefono = %s WHERE ID_Tienda = %s"
                        if _ejecutar(get_connection, sql, (nom_te.strip(), dir_te.strip() or None, tel_te.strip() or None, t_actual["ID_Tienda"])):
                            st.success("Tienda actualizada.")
                            st.rerun()
                    else:
                        st.warning("El nombre es obligatorio.")


def pantalla_admin(get_connection):
    st.title("⚙️ Panel de Administración")
    st.markdown("Gestión de catálogos, proveedores, usuarios y sucursales.")

    tab_prod, tab_cat, tab_prov, tab_user, tab_tienda = st.tabs(
        ["📦 Productos", "🏷️ Categorías", "🚚 Proveedores", "👥 Usuarios", "🏪 Tiendas"]
    )

    with tab_prod:
        _tab_productos(get_connection)
    with tab_cat:
        _tab_categorias(get_connection)
    with tab_prov:
        _tab_proveedores(get_connection)
    with tab_user:
        _tab_usuarios(get_connection)
    with tab_tienda:
        _tab_tiendas(get_connection)
