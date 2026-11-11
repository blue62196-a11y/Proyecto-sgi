SGI-Tiendas

Sistema de Gestión de Inventarios

Descripción

SGI-Tiendas es un sistema de gestión de inventarios desarrollado para administrar y controlar las operaciones de productos, compras, ventas, proveedores e inventarios de diferentes tiendas.

El sistema utiliza una base de datos MySQL para almacenar y gestionar la información, mientras que Streamlit permite desarrollar una interfaz gráfica para interactuar con los datos.

Tecnologías utilizadas

Python

Streamlit

MySQL

Pandas

GitHub

Funcionalidades

Gestión de productos.

Gestión de categorías.

Gestión de proveedores.

Control de inventario.

Registro de compras.

Registro de ventas.

Gestión de tiendas.

Control de traslados.

Administración de usuarios.

Estructura del proyecto

SGI-Tiendas/
│
├── app.py
├── SGI-base-de-datos-corregido.sql
├── requirements.txt
├── README.md
└── .gitignore

Instalación y ejecución

Clonar el repositorio:
git clone URL_DEL_REPOSITORIO

Instalar las dependencias:
pip install -r requirements.txt

Configurar las credenciales de conexión a MySQL.

Ejecutar la aplicación:
streamlit run app.py

Base de datos

El proyecto utiliza MySQL. El archivo SGI-base-de-datos-corregido.sql contiene la estructura de la base de datos, sus relaciones, vistas y datos de ejemplo.

Estado del proyecto

En desarrollo.
