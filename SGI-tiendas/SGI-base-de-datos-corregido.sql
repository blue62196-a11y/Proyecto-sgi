-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 08-11-2026 a las 20:06:31
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `sgi_tiendas`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `categoria`
--

CREATE TABLE `categoria` (
  `ID_Categoria` int(11) NOT NULL,
  `Nombre` varchar(100) NOT NULL,
  `Descripcion` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `categoria`
--

INSERT INTO `categoria` (`ID_Categoria`, `Nombre`, `Descripcion`) VALUES
(1, 'Cuidado personal', 'Jabones, cremas y productos de higiene y cuidado'),
(2, 'Maquillaje', 'Productos de maquillaje para rostro, ojos y labios'),
(3, 'Perfumes', 'Fragancias y perfumes');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `compra`
--

CREATE TABLE `compra` (
  `ID_Compra` int(11) NOT NULL,
  `ID_Tienda` int(11) NOT NULL,
  `ID_Proveedor` int(11) NOT NULL,
  `ID_Usuario` int(11) NOT NULL,
  `Fecha_Compra` datetime NOT NULL DEFAULT current_timestamp(),
  `Estado_Compra` enum('REGISTRADA','CANCELADA') NOT NULL DEFAULT 'REGISTRADA'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `compra`
--

INSERT INTO `compra` (`ID_Compra`, `ID_Tienda`, `ID_Proveedor`, `ID_Usuario`, `Fecha_Compra`, `Estado_Compra`) VALUES
(1, 1, 4, 2, '2026-11-08 00:22:18', 'REGISTRADA'),
(2, 2, 1, 3, '2026-11-08 10:24:46', 'REGISTRADA');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_compra`
--

CREATE TABLE `detalle_compra` (
  `ID_Detalle_Compra` int(11) NOT NULL,
  `ID_Compra` int(11) NOT NULL,
  `ID_Producto` int(11) NOT NULL,
  `Cantidad` decimal(12,2) NOT NULL,
  `Precio_Compra` decimal(10,2) NOT NULL,
  `Fecha_Vencimiento` date DEFAULT NULL,
  `Precio_Venta_Sugerido` decimal(10,2) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `detalle_compra`
--

INSERT INTO `detalle_compra` (`ID_Detalle_Compra`, `ID_Compra`, `ID_Producto`, `Cantidad`, `Precio_Compra`, `Fecha_Vencimiento`, `Precio_Venta_Sugerido`) VALUES
(1, 1, 1, 50.00, 1.50, '2027-06-30', 2.75),
(2, 1, 3, 40.00, 3.50, '2027-03-31', 6.50),
(3, 1, 6, 20.00, 14.00, NULL, 25.00),
(4, 2, 1, 10.00, 2.00, '2027-06-30', NULL),
(5, 2, 3, 5.00, 4.50, '2027-03-31', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `detalle_venta`
--

CREATE TABLE `detalle_venta` (
  `ID_Detalle_Venta` int(11) NOT NULL,
  `ID_Venta` int(11) NOT NULL,
  `ID_Inventario` int(11) NOT NULL,
  `Cantidad` decimal(12,2) NOT NULL,
  `Precio_Venta` decimal(10,2) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `detalle_venta`
--

INSERT INTO `detalle_venta` (`ID_Detalle_Venta`, `ID_Venta`, `ID_Inventario`, `Cantidad`, `Precio_Venta`) VALUES
(1, 1, 1, 5.00, 2.75),
(2, 1, 3, 2.00, 25.00),
(4, 2, 1, 10.00, 2.00),
(5, 2, 2, 5.00, 4.50);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `inventario`
--

CREATE TABLE `inventario` (
  `ID_Inventario` int(11) NOT NULL,
  `ID_Tienda` int(11) NOT NULL,
  `ID_Producto` int(11) NOT NULL,
  `Fecha_Vencimiento` date NOT NULL DEFAULT '9999-12-31',
  `Existencias` decimal(12,2) NOT NULL DEFAULT 0.00
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `inventario`
--

INSERT INTO `inventario` (`ID_Inventario`, `ID_Tienda`, `ID_Producto`, `Fecha_Vencimiento`, `Existencias`) VALUES
(1, 1, 1, '2027-06-30', 35.00),
(2, 1, 3, '2027-03-31', 35.00),
(3, 1, 6, '9999-12-31', 18.00),
(4, 2, 1, '2027-06-30', 10.00),
(5, 2, 3, '2027-03-31', 5.00);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `producto`
--

CREATE TABLE `producto` (
  `ID_Producto` int(11) NOT NULL,
  `Cod_Producto` varchar(30) NOT NULL,
  `Nombre` varchar(120) NOT NULL,
  `Descripcion` varchar(255) DEFAULT NULL,
  `Unidad_Medida` varchar(20) NOT NULL,
  `Estado_Producto` enum('ACTIVO','INACTIVO') NOT NULL DEFAULT 'ACTIVO',
  `ID_Categoria` int(11) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `producto`
--

INSERT INTO `producto` (`ID_Producto`, `Cod_Producto`, `Nombre`, `Descripcion`, `Unidad_Medida`, `Estado_Producto`, `ID_Categoria`) VALUES
(1, 'CUI-001', 'Jabón de sábila', 'Jabón artesanal de sábila', 'Unidad', 'ACTIVO', 1),
(2, 'CUI-002', 'Crema de concha nacar', 'Crema natural para la piel', 'Frasco', 'ACTIVO', 1),
(3, 'MAQ-001', 'Labial mate', 'Labial de larga duración', 'Unidad', 'ACTIVO', 2),
(4, 'MAQ-002', 'Base líquida', 'Base de maquillaje para el rostro', 'Frasco', 'ACTIVO', 2),
(5, 'MAQ-003', 'Sombras de ojos', 'Paleta de sombras', 'Unidad', 'ACTIVO', 2),
(6, 'PER-001', 'Perfume floral', 'Fragancia floral para dama', 'Frasco', 'ACTIVO', 3),
(7, 'PER-002', 'Colonia fresca', 'Colonia de notas cítricas', 'Frasco', 'ACTIVO', 3),
(8, 'PER-003', 'Perfume aquatico', 'Fragancia acuatica para caballero', 'Frasco', 'ACTIVO', 3);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `producto_proveedor`
--

CREATE TABLE `producto_proveedor` (
  `ID_Producto_Proveedor` int(11) NOT NULL,
  `ID_Producto` int(11) NOT NULL,
  `ID_Proveedor` int(11) NOT NULL,
  `Ultimo_Costo` decimal(10,2) NOT NULL,
  `Fecha_Ultimo_Costo` date NOT NULL,
  `Estado` enum('ACTIVO','INACTIVO') NOT NULL DEFAULT 'ACTIVO'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `producto_proveedor`
--

INSERT INTO `producto_proveedor` (`ID_Producto_Proveedor`, `ID_Producto`, `ID_Proveedor`, `Ultimo_Costo`, `Fecha_Ultimo_Costo`, `Estado`) VALUES
(1, 1, 4, 1.50, '2026-11-08', 'ACTIVO'),
(2, 3, 4, 3.50, '2026-11-08', 'ACTIVO'),
(3, 6, 4, 14.00, '2026-11-08', 'ACTIVO'),
(4, 1, 1, 2.00, '2026-11-08', 'ACTIVO'),
(5, 3, 1, 4.50, '2026-11-08', 'ACTIVO'),
(7, 1, 5, 1.80, '2026-11-08', 'ACTIVO'),
(8, 3, 5, 3.20, '2026-11-08', 'ACTIVO');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `producto_tienda`
--

CREATE TABLE `producto_tienda` (
  `ID_Tienda` int(11) NOT NULL,
  `ID_Producto` int(11) NOT NULL,
  `Precio_Venta` decimal(10,2) NOT NULL,
  `Stock_Minimo` decimal(12,2) NOT NULL DEFAULT 0.00,
  `Stock_Seguridad` decimal(12,2) NOT NULL DEFAULT 0.00,
  `Dias_Entrega` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `producto_tienda`
--

INSERT INTO `producto_tienda` (`ID_Tienda`, `ID_Producto`, `Precio_Venta`, `Stock_Minimo`, `Stock_Seguridad`, `Dias_Entrega`) VALUES
(1, 1, 2.75, 10.00, 5.00, 3),
(1, 2, 5.00, 10.00, 5.00, 3),
(1, 3, 6.50, 10.00, 5.00, 3),
(1, 4, 12.00, 10.00, 5.00, 3),
(1, 5, 9.00, 10.00, 5.00, 3),
(1, 6, 25.00, 10.00, 5.00, 3),
(1, 7, 20.00, 10.00, 5.00, 3),
(1, 8, 22.00, 10.00, 5.00, 3),
(2, 1, 2.75, 10.00, 5.00, 3),
(2, 2, 5.00, 10.00, 5.00, 3),
(2, 3, 6.50, 10.00, 5.00, 3),
(2, 4, 12.00, 10.00, 5.00, 3),
(2, 5, 9.00, 10.00, 5.00, 3),
(2, 6, 25.00, 10.00, 5.00, 3),
(2, 7, 20.00, 10.00, 5.00, 3),
(2, 8, 22.00, 10.00, 5.00, 3),
(3, 1, 2.75, 10.00, 5.00, 3),
(3, 2, 5.00, 10.00, 5.00, 3),
(3, 3, 7.00, 10.00, 5.00, 3),
(3, 4, 12.00, 10.00, 5.00, 3),
(3, 5, 9.00, 10.00, 5.00, 3),
(3, 6, 25.00, 10.00, 5.00, 3),
(3, 7, 20.00, 10.00, 5.00, 3),
(3, 8, 22.00, 10.00, 5.00, 3);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `proveedor`
--

CREATE TABLE `proveedor` (
  `ID_Proveedor` int(11) NOT NULL,
  `ID_Tienda` int(11) NOT NULL,
  `Nombre` varchar(120) NOT NULL,
  `DUI_NIT` varchar(20) DEFAULT NULL,
  `Telefono` varchar(20) DEFAULT NULL,
  `Correo` varchar(100) DEFAULT NULL,
  `Direccion` varchar(200) DEFAULT NULL,
  `ID_Tienda_CD` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `proveedor`
--

INSERT INTO `proveedor` (`ID_Proveedor`, `ID_Tienda`, `Nombre`, `DUI_NIT`, `Telefono`, `Correo`, `Direccion`, `ID_Tienda_CD`) VALUES
(1, 2, 'Centro de Distribución', NULL, NULL, NULL, NULL, 1),
(2, 3, 'Centro de Distribución', NULL, NULL, NULL, NULL, 1),
(4, 1, 'Distribuidora Belleza S.A.', '0614-010190-101-2', '2222-3333', 'ventas@belleza.com', 'San Salvador', NULL),
(5, 2, 'Cosmeticos del Sur', NULL, NULL, NULL, NULL, NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `rol`
--

CREATE TABLE `rol` (
  `ID_Rol` int(11) NOT NULL,
  `Nombre` varchar(50) NOT NULL,
  `Descripcion` varchar(200) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `rol`
--

INSERT INTO `rol` (`ID_Rol`, `Nombre`, `Descripcion`) VALUES
(1, 'Administrador', 'Visión global; gestiona usuarios, tiendas y categorías'),
(2, 'Encargado', 'Opera una tienda o el Centro de Distribución');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tienda`
--

CREATE TABLE `tienda` (
  `ID_Tienda` int(11) NOT NULL,
  `Nombre` varchar(100) NOT NULL,
  `Tipo` enum('TIENDA','CD') NOT NULL DEFAULT 'TIENDA',
  `Direccion` varchar(200) DEFAULT NULL,
  `Telefono` varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `tienda`
--

INSERT INTO `tienda` (`ID_Tienda`, `Nombre`, `Tipo`, `Direccion`, `Telefono`) VALUES
(1, 'Centro de Distribución', 'CD', 'Por definir', NULL),
(2, 'Tienda 1', 'TIENDA', 'Por definir', NULL),
(3, 'Tienda 2', 'TIENDA', 'Por definir', NULL);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `traslado`
--

CREATE TABLE `traslado` (
  `ID_Traslado` int(11) NOT NULL,
  `ID_Venta` int(11) NOT NULL,
  `ID_Tienda_Origen` int(11) NOT NULL,
  `ID_Tienda_Destino` int(11) NOT NULL,
  `ID_Compra` int(11) DEFAULT NULL,
  `Estado` enum('ENVIADO','RECIBIDO','CANCELADO') NOT NULL DEFAULT 'ENVIADO',
  `Fecha_Envio` datetime NOT NULL DEFAULT current_timestamp(),
  `Fecha_Recepcion` datetime DEFAULT NULL,
  `ID_Usuario_Envia` int(11) NOT NULL,
  `ID_Usuario_Recibe` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `traslado`
--

INSERT INTO `traslado` (`ID_Traslado`, `ID_Venta`, `ID_Tienda_Origen`, `ID_Tienda_Destino`, `ID_Compra`, `Estado`, `Fecha_Envio`, `Fecha_Recepcion`, `ID_Usuario_Envia`, `ID_Usuario_Recibe`) VALUES
(1, 2, 1, 2, 2, 'RECIBIDO', '2026-11-08 10:22:54', '2026-11-08 10:40:11', 2, 3);

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `usuario`
--

CREATE TABLE `usuario` (
  `ID_Usuario` int(11) NOT NULL,
  `Nombre` varchar(100) NOT NULL,
  `Correo` varchar(100) NOT NULL,
  `Password_Hash` varchar(255) NOT NULL,
  `ID_Rol` int(11) NOT NULL,
  `ID_Tienda` int(11) NOT NULL,
  `Estado_Usuario` enum('ACTIVO','INACTIVO') NOT NULL DEFAULT 'ACTIVO'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `usuario`
--

INSERT INTO `usuario` (`ID_Usuario`, `Nombre`, `Correo`, `Password_Hash`, `ID_Rol`, `ID_Tienda`, `Estado_Usuario`) VALUES
(1, 'Administrador', 'admin@sgi.local', 'REEMPLAZAR_CON_HASH', 1, 1, 'ACTIVO'),
(2, 'Encargado CD', 'encargado.cd@sgi.local', 'REEMPLAZAR_CON_HASH', 2, 1, 'ACTIVO'),
(3, 'Encargado Tienda 1', 'tienda1@sgi.local', 'REEMPLAZAR_CON_HASH', 2, 2, 'ACTIVO'),
(4, 'Encargado Tienda 2', 'tienda2@sgi.local', 'REEMPLAZAR_CON_HASH', 2, 3, 'ACTIVO');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `venta`
--

CREATE TABLE `venta` (
  `ID_Venta` int(11) NOT NULL,
  `ID_Tienda` int(11) NOT NULL,
  `ID_Usuario` int(11) NOT NULL,
  `Fecha_Venta` datetime NOT NULL DEFAULT current_timestamp(),
  `Cliente_Nombre` varchar(100) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Volcado de datos para la tabla `venta`
--

INSERT INTO `venta` (`ID_Venta`, `ID_Tienda`, `ID_Usuario`, `Fecha_Venta`, `Cliente_Nombre`) VALUES
(1, 1, 2, '2026-11-08 10:12:39', 'Cliente de prueba'),
(2, 1, 2, '2026-11-08 10:22:07', 'Traslado a Tienda 1');

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_compra_total`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_compra_total` (
`ID_Compra` int(11)
,`ID_Tienda` int(11)
,`Tienda` varchar(100)
,`Proveedor` varchar(120)
,`Fecha_Compra` datetime
,`Estado_Compra` enum('REGISTRADA','CANCELADA')
,`Total` decimal(44,4)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_costo_cd`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_costo_cd` (
`ID_Tienda` int(11)
,`Tienda` varchar(100)
,`ID_Producto` int(11)
,`Producto` varchar(120)
,`Costo_CD` decimal(10,2)
,`Costo_Otros` decimal(10,2)
,`Decision` varchar(21)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_inventario_actual`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_inventario_actual` (
`ID_Tienda` int(11)
,`Tienda` varchar(100)
,`ID_Producto` int(11)
,`Cod_Producto` varchar(30)
,`Producto` varchar(120)
,`Existencias` decimal(34,2)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_proximos_vencer`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_proximos_vencer` (
`ID_Tienda` int(11)
,`Tienda` varchar(100)
,`Producto` varchar(120)
,`Fecha_Vencimiento` date
,`Existencias` decimal(12,2)
,`Dias_Restantes` int(7)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_punto_reorden`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_punto_reorden` (
`ID_Tienda` int(11)
,`Tienda` varchar(100)
,`ID_Producto` int(11)
,`Producto` varchar(120)
,`Existencias` decimal(34,2)
,`Demanda_Diaria` decimal(35,2)
,`Dias_Entrega` int(11)
,`Stock_Seguridad` decimal(12,2)
,`Punto_Reorden` decimal(46,2)
,`Estado` varchar(7)
);

-- --------------------------------------------------------

--
-- Estructura Stand-in para la vista `v_venta_total`
-- (Véase abajo para la vista actual)
--
CREATE TABLE `v_venta_total` (
`ID_Venta` int(11)
,`ID_Tienda` int(11)
,`Tienda` varchar(100)
,`Fecha_Venta` datetime
,`Cliente_Nombre` varchar(100)
,`Total` decimal(44,4)
);

-- --------------------------------------------------------

--
-- Estructura para la vista `v_compra_total`
--
DROP TABLE IF EXISTS `v_compra_total`;

CREATE ALGORITHM=UNDEFINED SQL SECURITY INVOKER VIEW `v_compra_total`  AS SELECT `c`.`ID_Compra` AS `ID_Compra`, `c`.`ID_Tienda` AS `ID_Tienda`, `t`.`Nombre` AS `Tienda`, `pr`.`Nombre` AS `Proveedor`, `c`.`Fecha_Compra` AS `Fecha_Compra`, `c`.`Estado_Compra` AS `Estado_Compra`, sum(`dc`.`Cantidad` * `dc`.`Precio_Compra`) AS `Total` FROM (((`compra` `c` join `tienda` `t` on(`t`.`ID_Tienda` = `c`.`ID_Tienda`)) join `proveedor` `pr` on(`pr`.`ID_Proveedor` = `c`.`ID_Proveedor`)) join `detalle_compra` `dc` on(`dc`.`ID_Compra` = `c`.`ID_Compra`)) GROUP BY `c`.`ID_Compra`, `c`.`ID_Tienda`, `t`.`Nombre`, `pr`.`Nombre`, `c`.`Fecha_Compra`, `c`.`Estado_Compra` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_costo_cd`
--
DROP TABLE IF EXISTS `v_costo_cd`;

CREATE ALGORITHM=UNDEFINED SQL SECURITY INVOKER VIEW `v_costo_cd`  AS SELECT `t`.`ID_Tienda` AS `ID_Tienda`, `t`.`Nombre` AS `Tienda`, `p`.`ID_Producto` AS `ID_Producto`, `p`.`Nombre` AS `Producto`, `cd`.`Costo_CD` AS `Costo_CD`, `ot`.`Costo_Otros` AS `Costo_Otros`, CASE WHEN `cd`.`Costo_CD` is null THEN 'CD sin costo' WHEN `ot`.`Costo_Otros` is null THEN 'Sin otros proveedores' WHEN `cd`.`Costo_CD` < `ot`.`Costo_Otros` THEN 'CD conviene' ELSE 'CD no conviene' END AS `Decision` FROM (((`tienda` `t` join `producto` `p`) left join (select `pp`.`ID_Producto` AS `ID_Producto`,min(`pp`.`Ultimo_Costo`) AS `Costo_CD` from ((`producto_proveedor` `pp` join `proveedor` `pr` on(`pr`.`ID_Proveedor` = `pp`.`ID_Proveedor`)) join `tienda` `tcd` on(`tcd`.`ID_Tienda` = `pr`.`ID_Tienda` and `tcd`.`Tipo` = 'CD')) where `pr`.`ID_Tienda_CD` is null and `pp`.`Estado` = 'ACTIVO' group by `pp`.`ID_Producto`) `cd` on(`cd`.`ID_Producto` = `p`.`ID_Producto`)) left join (select `pr`.`ID_Tienda` AS `ID_Tienda`,`pp`.`ID_Producto` AS `ID_Producto`,min(`pp`.`Ultimo_Costo`) AS `Costo_Otros` from (`producto_proveedor` `pp` join `proveedor` `pr` on(`pr`.`ID_Proveedor` = `pp`.`ID_Proveedor`)) where `pr`.`ID_Tienda_CD` is null and `pp`.`Estado` = 'ACTIVO' group by `pr`.`ID_Tienda`,`pp`.`ID_Producto`) `ot` on(`ot`.`ID_Tienda` = `t`.`ID_Tienda` and `ot`.`ID_Producto` = `p`.`ID_Producto`)) WHERE `t`.`Tipo` = 'TIENDA' ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_inventario_actual`
--
DROP TABLE IF EXISTS `v_inventario_actual`;

CREATE ALGORITHM=UNDEFINED SQL SECURITY INVOKER VIEW `v_inventario_actual`  AS SELECT `i`.`ID_Tienda` AS `ID_Tienda`, `t`.`Nombre` AS `Tienda`, `i`.`ID_Producto` AS `ID_Producto`, `p`.`Cod_Producto` AS `Cod_Producto`, `p`.`Nombre` AS `Producto`, sum(`i`.`Existencias`) AS `Existencias` FROM ((`inventario` `i` join `tienda` `t` on(`t`.`ID_Tienda` = `i`.`ID_Tienda`)) join `producto` `p` on(`p`.`ID_Producto` = `i`.`ID_Producto`)) GROUP BY `i`.`ID_Tienda`, `t`.`Nombre`, `i`.`ID_Producto`, `p`.`Cod_Producto`, `p`.`Nombre` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_proximos_vencer`
--
DROP TABLE IF EXISTS `v_proximos_vencer`;

CREATE ALGORITHM=UNDEFINED SQL SECURITY INVOKER VIEW `v_proximos_vencer`  AS SELECT `i`.`ID_Tienda` AS `ID_Tienda`, `t`.`Nombre` AS `Tienda`, `p`.`Nombre` AS `Producto`, `i`.`Fecha_Vencimiento` AS `Fecha_Vencimiento`, `i`.`Existencias` AS `Existencias`, to_days(`i`.`Fecha_Vencimiento`) - to_days(curdate()) AS `Dias_Restantes` FROM ((`inventario` `i` join `tienda` `t` on(`t`.`ID_Tienda` = `i`.`ID_Tienda`)) join `producto` `p` on(`p`.`ID_Producto` = `i`.`ID_Producto`)) WHERE `i`.`Fecha_Vencimiento` <> '9999-12-31' AND `i`.`Existencias` > 0 ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_punto_reorden`
--
DROP TABLE IF EXISTS `v_punto_reorden`;

CREATE ALGORITHM=UNDEFINED SQL SECURITY INVOKER VIEW `v_punto_reorden`  AS SELECT `x`.`ID_Tienda` AS `ID_Tienda`, `x`.`Tienda` AS `Tienda`, `x`.`ID_Producto` AS `ID_Producto`, `x`.`Producto` AS `Producto`, `x`.`Existencias` AS `Existencias`, `x`.`Demanda_Diaria` AS `Demanda_Diaria`, `x`.`Dias_Entrega` AS `Dias_Entrega`, `x`.`Stock_Seguridad` AS `Stock_Seguridad`, `x`.`Punto_Reorden` AS `Punto_Reorden`, CASE WHEN `x`.`Existencias` <= `x`.`Punto_Reorden` THEN 'COMPRAR' ELSE 'OK' END AS `Estado` FROM (select `pt`.`ID_Tienda` AS `ID_Tienda`,`t`.`Nombre` AS `Tienda`,`pt`.`ID_Producto` AS `ID_Producto`,`p`.`Nombre` AS `Producto`,coalesce(`inv`.`Existencias`,0) AS `Existencias`,round(coalesce(`ven`.`Total_Vendido`,0) / 30,2) AS `Demanda_Diaria`,`pt`.`Dias_Entrega` AS `Dias_Entrega`,`pt`.`Stock_Seguridad` AS `Stock_Seguridad`,round(coalesce(`ven`.`Total_Vendido`,0) / 30 * `pt`.`Dias_Entrega` + `pt`.`Stock_Seguridad`,2) AS `Punto_Reorden` from ((((`producto_tienda` `pt` join `tienda` `t` on(`t`.`ID_Tienda` = `pt`.`ID_Tienda`)) join `producto` `p` on(`p`.`ID_Producto` = `pt`.`ID_Producto`)) left join (select `inventario`.`ID_Tienda` AS `ID_Tienda`,`inventario`.`ID_Producto` AS `ID_Producto`,sum(`inventario`.`Existencias`) AS `Existencias` from `inventario` group by `inventario`.`ID_Tienda`,`inventario`.`ID_Producto`) `inv` on(`inv`.`ID_Tienda` = `pt`.`ID_Tienda` and `inv`.`ID_Producto` = `pt`.`ID_Producto`)) left join (select `v`.`ID_Tienda` AS `ID_Tienda`,`i`.`ID_Producto` AS `ID_Producto`,sum(`dv`.`Cantidad`) AS `Total_Vendido` from ((`venta` `v` join `detalle_venta` `dv` on(`dv`.`ID_Venta` = `v`.`ID_Venta`)) join `inventario` `i` on(`i`.`ID_Inventario` = `dv`.`ID_Inventario`)) where `v`.`Fecha_Venta` >= curdate() - interval 30 day group by `v`.`ID_Tienda`,`i`.`ID_Producto`) `ven` on(`ven`.`ID_Tienda` = `pt`.`ID_Tienda` and `ven`.`ID_Producto` = `pt`.`ID_Producto`)) where `p`.`Estado_Producto` = 'ACTIVO') AS `x` ;

-- --------------------------------------------------------

--
-- Estructura para la vista `v_venta_total`
--
DROP TABLE IF EXISTS `v_venta_total`;

CREATE ALGORITHM=UNDEFINED SQL SECURITY INVOKER VIEW `v_venta_total`  AS SELECT `v`.`ID_Venta` AS `ID_Venta`, `v`.`ID_Tienda` AS `ID_Tienda`, `t`.`Nombre` AS `Tienda`, `v`.`Fecha_Venta` AS `Fecha_Venta`, `v`.`Cliente_Nombre` AS `Cliente_Nombre`, sum(`dv`.`Cantidad` * `dv`.`Precio_Venta`) AS `Total` FROM ((`venta` `v` join `tienda` `t` on(`t`.`ID_Tienda` = `v`.`ID_Tienda`)) join `detalle_venta` `dv` on(`dv`.`ID_Venta` = `v`.`ID_Venta`)) GROUP BY `v`.`ID_Venta`, `v`.`ID_Tienda`, `t`.`Nombre`, `v`.`Fecha_Venta`, `v`.`Cliente_Nombre` ;

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `categoria`
--
ALTER TABLE `categoria`
  ADD PRIMARY KEY (`ID_Categoria`),
  ADD UNIQUE KEY `Nombre` (`Nombre`);

--
-- Indices de la tabla `compra`
--
ALTER TABLE `compra`
  ADD PRIMARY KEY (`ID_Compra`),
  ADD KEY `fk_compra_tienda` (`ID_Tienda`),
  ADD KEY `fk_compra_proveedor` (`ID_Proveedor`),
  ADD KEY `fk_compra_usuario` (`ID_Usuario`);

--
-- Indices de la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  ADD PRIMARY KEY (`ID_Detalle_Compra`),
  ADD KEY `fk_dc_compra` (`ID_Compra`),
  ADD KEY `fk_dc_producto` (`ID_Producto`);

--
-- Indices de la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD PRIMARY KEY (`ID_Detalle_Venta`),
  ADD KEY `fk_dv_venta` (`ID_Venta`),
  ADD KEY `fk_dv_inventario` (`ID_Inventario`);

--
-- Indices de la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD PRIMARY KEY (`ID_Inventario`),
  ADD UNIQUE KEY `uq_inv_lote` (`ID_Tienda`,`ID_Producto`,`Fecha_Vencimiento`),
  ADD KEY `fk_inv_producto` (`ID_Producto`);

--
-- Indices de la tabla `producto`
--
ALTER TABLE `producto`
  ADD PRIMARY KEY (`ID_Producto`),
  ADD UNIQUE KEY `Cod_Producto` (`Cod_Producto`),
  ADD KEY `fk_producto_categoria` (`ID_Categoria`);

--
-- Indices de la tabla `producto_proveedor`
--
ALTER TABLE `producto_proveedor`
  ADD PRIMARY KEY (`ID_Producto_Proveedor`),
  ADD UNIQUE KEY `uq_pp` (`ID_Producto`,`ID_Proveedor`),
  ADD KEY `fk_pp_proveedor` (`ID_Proveedor`);

--
-- Indices de la tabla `producto_tienda`
--
ALTER TABLE `producto_tienda`
  ADD PRIMARY KEY (`ID_Tienda`,`ID_Producto`),
  ADD KEY `fk_pt_producto` (`ID_Producto`);

--
-- Indices de la tabla `proveedor`
--
ALTER TABLE `proveedor`
  ADD PRIMARY KEY (`ID_Proveedor`),
  ADD UNIQUE KEY `uq_prov_dui_tienda` (`ID_Tienda`,`DUI_NIT`),
  ADD UNIQUE KEY `uq_prov_cd_tienda` (`ID_Tienda`,`ID_Tienda_CD`),
  ADD KEY `fk_prov_cd` (`ID_Tienda_CD`);

--
-- Indices de la tabla `rol`
--
ALTER TABLE `rol`
  ADD PRIMARY KEY (`ID_Rol`),
  ADD UNIQUE KEY `Nombre` (`Nombre`);

--
-- Indices de la tabla `tienda`
--
ALTER TABLE `tienda`
  ADD PRIMARY KEY (`ID_Tienda`),
  ADD UNIQUE KEY `Nombre` (`Nombre`);

--
-- Indices de la tabla `traslado`
--
ALTER TABLE `traslado`
  ADD PRIMARY KEY (`ID_Traslado`),
  ADD UNIQUE KEY `ID_Venta` (`ID_Venta`),
  ADD UNIQUE KEY `ID_Compra` (`ID_Compra`),
  ADD KEY `fk_tras_origen` (`ID_Tienda_Origen`),
  ADD KEY `fk_tras_destino` (`ID_Tienda_Destino`),
  ADD KEY `fk_tras_envia` (`ID_Usuario_Envia`),
  ADD KEY `fk_tras_recibe` (`ID_Usuario_Recibe`);

--
-- Indices de la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD PRIMARY KEY (`ID_Usuario`),
  ADD UNIQUE KEY `Correo` (`Correo`),
  ADD KEY `fk_usuario_rol` (`ID_Rol`),
  ADD KEY `fk_usuario_tienda` (`ID_Tienda`);

--
-- Indices de la tabla `venta`
--
ALTER TABLE `venta`
  ADD PRIMARY KEY (`ID_Venta`),
  ADD KEY `fk_venta_tienda` (`ID_Tienda`),
  ADD KEY `fk_venta_usuario` (`ID_Usuario`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `categoria`
--
ALTER TABLE `categoria`
  MODIFY `ID_Categoria` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `compra`
--
ALTER TABLE `compra`
  MODIFY `ID_Compra` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  MODIFY `ID_Detalle_Compra` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  MODIFY `ID_Detalle_Venta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `inventario`
--
ALTER TABLE `inventario`
  MODIFY `ID_Inventario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=7;

--
-- AUTO_INCREMENT de la tabla `producto`
--
ALTER TABLE `producto`
  MODIFY `ID_Producto` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT de la tabla `producto_proveedor`
--
ALTER TABLE `producto_proveedor`
  MODIFY `ID_Producto_Proveedor` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT de la tabla `proveedor`
--
ALTER TABLE `proveedor`
  MODIFY `ID_Proveedor` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT de la tabla `rol`
--
ALTER TABLE `rol`
  MODIFY `ID_Rol` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- AUTO_INCREMENT de la tabla `tienda`
--
ALTER TABLE `tienda`
  MODIFY `ID_Tienda` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT de la tabla `traslado`
--
ALTER TABLE `traslado`
  MODIFY `ID_Traslado` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT de la tabla `usuario`
--
ALTER TABLE `usuario`
  MODIFY `ID_Usuario` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT de la tabla `venta`
--
ALTER TABLE `venta`
  MODIFY `ID_Venta` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `compra`
--
ALTER TABLE `compra`
  ADD CONSTRAINT `fk_compra_proveedor` FOREIGN KEY (`ID_Proveedor`) REFERENCES `proveedor` (`ID_Proveedor`),
  ADD CONSTRAINT `fk_compra_tienda` FOREIGN KEY (`ID_Tienda`) REFERENCES `tienda` (`ID_Tienda`),
  ADD CONSTRAINT `fk_compra_usuario` FOREIGN KEY (`ID_Usuario`) REFERENCES `usuario` (`ID_Usuario`);

--
-- Filtros para la tabla `detalle_compra`
--
ALTER TABLE `detalle_compra`
  ADD CONSTRAINT `fk_dc_compra` FOREIGN KEY (`ID_Compra`) REFERENCES `compra` (`ID_Compra`),
  ADD CONSTRAINT `fk_dc_producto` FOREIGN KEY (`ID_Producto`) REFERENCES `producto` (`ID_Producto`);

--
-- Filtros para la tabla `detalle_venta`
--
ALTER TABLE `detalle_venta`
  ADD CONSTRAINT `fk_dv_inventario` FOREIGN KEY (`ID_Inventario`) REFERENCES `inventario` (`ID_Inventario`),
  ADD CONSTRAINT `fk_dv_venta` FOREIGN KEY (`ID_Venta`) REFERENCES `venta` (`ID_Venta`);

--
-- Filtros para la tabla `inventario`
--
ALTER TABLE `inventario`
  ADD CONSTRAINT `fk_inv_producto` FOREIGN KEY (`ID_Producto`) REFERENCES `producto` (`ID_Producto`),
  ADD CONSTRAINT `fk_inv_tienda` FOREIGN KEY (`ID_Tienda`) REFERENCES `tienda` (`ID_Tienda`);

--
-- Filtros para la tabla `producto`
--
ALTER TABLE `producto`
  ADD CONSTRAINT `fk_producto_categoria` FOREIGN KEY (`ID_Categoria`) REFERENCES `categoria` (`ID_Categoria`);

--
-- Filtros para la tabla `producto_proveedor`
--
ALTER TABLE `producto_proveedor`
  ADD CONSTRAINT `fk_pp_producto` FOREIGN KEY (`ID_Producto`) REFERENCES `producto` (`ID_Producto`),
  ADD CONSTRAINT `fk_pp_proveedor` FOREIGN KEY (`ID_Proveedor`) REFERENCES `proveedor` (`ID_Proveedor`);

--
-- Filtros para la tabla `producto_tienda`
--
ALTER TABLE `producto_tienda`
  ADD CONSTRAINT `fk_pt_producto` FOREIGN KEY (`ID_Producto`) REFERENCES `producto` (`ID_Producto`),
  ADD CONSTRAINT `fk_pt_tienda` FOREIGN KEY (`ID_Tienda`) REFERENCES `tienda` (`ID_Tienda`);

--
-- Filtros para la tabla `proveedor`
--
ALTER TABLE `proveedor`
  ADD CONSTRAINT `fk_prov_cd` FOREIGN KEY (`ID_Tienda_CD`) REFERENCES `tienda` (`ID_Tienda`),
  ADD CONSTRAINT `fk_prov_tienda` FOREIGN KEY (`ID_Tienda`) REFERENCES `tienda` (`ID_Tienda`);

--
-- Filtros para la tabla `traslado`
--
ALTER TABLE `traslado`
  ADD CONSTRAINT `fk_tras_compra` FOREIGN KEY (`ID_Compra`) REFERENCES `compra` (`ID_Compra`),
  ADD CONSTRAINT `fk_tras_destino` FOREIGN KEY (`ID_Tienda_Destino`) REFERENCES `tienda` (`ID_Tienda`),
  ADD CONSTRAINT `fk_tras_envia` FOREIGN KEY (`ID_Usuario_Envia`) REFERENCES `usuario` (`ID_Usuario`),
  ADD CONSTRAINT `fk_tras_origen` FOREIGN KEY (`ID_Tienda_Origen`) REFERENCES `tienda` (`ID_Tienda`),
  ADD CONSTRAINT `fk_tras_recibe` FOREIGN KEY (`ID_Usuario_Recibe`) REFERENCES `usuario` (`ID_Usuario`),
  ADD CONSTRAINT `fk_tras_venta` FOREIGN KEY (`ID_Venta`) REFERENCES `venta` (`ID_Venta`);

--
-- Filtros para la tabla `usuario`
--
ALTER TABLE `usuario`
  ADD CONSTRAINT `fk_usuario_rol` FOREIGN KEY (`ID_Rol`) REFERENCES `rol` (`ID_Rol`),
  ADD CONSTRAINT `fk_usuario_tienda` FOREIGN KEY (`ID_Tienda`) REFERENCES `tienda` (`ID_Tienda`);

--
-- Filtros para la tabla `venta`
--
ALTER TABLE `venta`
  ADD CONSTRAINT `fk_venta_tienda` FOREIGN KEY (`ID_Tienda`) REFERENCES `tienda` (`ID_Tienda`),
  ADD CONSTRAINT `fk_venta_usuario` FOREIGN KEY (`ID_Usuario`) REFERENCES `usuario` (`ID_Usuario`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
