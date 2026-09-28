"""Genera los datos simulados de Distribuidora Andina (2024-2025).

Distribuidora mayorista de abarrotes, bebidas y limpieza en el Valle de Toluca
que vende a tiendas, minisupers, restaurantes y cafeterias, con flotilla propia.

Los archivos salen "sucios" a proposito (como llegan en la vida real) para
practicar la limpieza en Power Query y pandas:
  - regiones escritas de varias formas (mayusculas, espacios, sin acento)
  - cliente_id con espacios al final en algunas lineas de venta
  - lineas de venta duplicadas
  - fechas de pagos como texto dd/mm/aaaa y montos como texto "$1,234.50"
"""

import numpy as np
import pandas as pd

SEMILLA = 7
rng = np.random.default_rng(SEMILLA)
SALIDA = "datos_crudos"

INICIO, FIN = pd.Timestamp("2024-01-01"), pd.Timestamp("2025-12-31")

# ---------------------------------------------------------------- productos
CATEGORIAS = {
    # categoria: (n_productos, rango precio caja, rango margen bruto)
    "Abarrotes": (26, (180, 650), (0.16, 0.24)),
    "Bebidas": (20, (150, 480), (0.20, 0.28)),
    "Limpieza": (16, (200, 700), (0.26, 0.36)),
    "Higiene personal": (14, (250, 800), (0.28, 0.38)),
    "Botanas y dulces": (14, (160, 520), (0.24, 0.32)),
}
MARCAS = ["Del Valle Andino", "Sierra", "Montealto", "Brisa", "Nevado", "La Hacienda", "Clarito", "Toltec"]
NOMBRES_PROD = {
    "Abarrotes": ["Arroz 1kg", "Frijol negro 1kg", "Aceite 900ml", "Azucar 2kg", "Atun en agua", "Pasta fideo",
                  "Harina de maiz 1kg", "Lentejas 500g", "Sal 1kg", "Chiles en lata", "Mayonesa 390g", "Cafe soluble",
                  "Avena 800g", "Leche en polvo", "Consome de pollo", "Pure de tomate", "Galletas marias",
                  "Cereal hojuelas", "Mermelada fresa", "Sardina en tomate", "Elote en lata", "Harina de trigo",
                  "Frijol bayo 1kg", "Arroz integral", "Salsa picante", "Vinagre blanco"],
    "Bebidas": ["Agua 1.5L", "Agua 600ml", "Refresco cola 2L", "Refresco naranja 2L", "Jugo mango 1L", "Jugo manzana 1L",
                "Bebida isotonica", "Te helado", "Agua mineral", "Refresco lima 600ml", "Nectar durazno",
                "Bebida de soya", "Energetica 473ml", "Cafe frio lata", "Agua saborizada", "Leche UHT 1L",
                "Leche deslactosada", "Yogur bebible", "Refresco cola 600ml", "Jugo naranja 1L"],
    "Limpieza": ["Detergente 1kg", "Cloro 1L", "Suavizante 850ml", "Lavatrastes 750ml", "Limpiador pisos 1L",
                 "Jabon de barra", "Fibra verde", "Bolsas basura", "Desengrasante", "Limpiavidrios",
                 "Detergente liquido 3L", "Aromatizante", "Cloro 4L", "Esponja doble", "Guantes latex", "Trapeador"],
    "Higiene personal": ["Papel higienico 12r", "Shampoo 750ml", "Jabon tocador", "Pasta dental", "Desodorante",
                         "Toallas femeninas", "Panales etapa 3", "Crema corporal", "Cepillo dental",
                         "Gel antibacterial", "Rastrillos", "Enjuague bucal", "Toallitas humedas", "Acondicionador"],
    "Botanas y dulces": ["Papas fritas 45g", "Cacahuate japones", "Chicharron de harina", "Palomitas",
                         "Chocolate barra", "Caramelo suave", "Paleta de dulce", "Gomitas", "Galleta rellena",
                         "Pan dulce empacado", "Tostadas", "Nachos", "Mazapan", "Chicle"],
}

productos = []
pid = 1
for cat, (n, (pmin, pmax), (mmin, mmax)) in CATEGORIAS.items():
    for nombre in NOMBRES_PROD[cat][:n]:
        precio_2024 = round(rng.uniform(pmin, pmax), 2)
        margen = rng.uniform(mmin, mmax)
        costo_2024 = round(precio_2024 * (1 - margen), 2)
        # 2025: los proveedores suben costos mas rapido de lo que la empresa sube precios
        precio_2025 = round(precio_2024 * rng.uniform(1.03, 1.05), 2)
        costo_2025 = round(costo_2024 * rng.uniform(1.06, 1.09), 2)
        productos.append(dict(producto_id=f"P{pid:03d}", producto=f"{nombre} (caja)", categoria=cat,
                              marca=rng.choice(MARCAS), precio_lista_2024=precio_2024, costo_2024=costo_2024,
                              precio_lista_2025=precio_2025, costo_2025=costo_2025))
        pid += 1
productos = pd.DataFrame(productos)

# ---------------------------------------------------------------- vendedores
REGIONES = {
    # region: (distancia km min, max, dias de entrega prometidos, es_expansion_2025)
    "Toluca": (4, 18, 1, False),
    "Metepec": (6, 16, 1, False),
    "Lerma": (18, 32, 1, False),
    "Zinacantepec": (12, 26, 1, False),
    "Tenancingo": (48, 66, 2, True),
    "Valle de Bravo": (78, 102, 2, True),
    "CDMX Poniente": (58, 85, 2, True),
}
vendedores = pd.DataFrame([
    ("V01", "Laura Mendoza", "Toluca", "2019-03-01"),
    ("V02", "Jorge Castillo", "Toluca", "2020-07-15"),
    ("V03", "Andres Ruiz", "Metepec", "2021-02-01"),
    ("V04", "Sofia Herrera", "Metepec", "2018-09-10"),
    ("V05", "Miguel Torres", "Lerma", "2022-01-17"),
    ("V06", "Paola Jimenez", "Zinacantepec", "2020-11-03"),
    ("V07", "Ricardo Navarro", "Tenancingo", "2025-01-06"),
    ("V08", "Daniela Ortega", "Valle de Bravo", "2025-01-06"),
    ("V09", "Hector Vargas", "CDMX Poniente", "2025-02-03"),
    ("V10", "Fernanda Rojas", "Lerma", "2023-05-22"),
], columns=["vendedor_id", "vendedor", "region", "fecha_ingreso"])
# Vendedores que en 2025 compiten con descuentos agresivos para crecer volumen
VENDEDORES_DESCUENTO = {"V03", "V07", "V09"}

# ---------------------------------------------------------------- clientes
TIPOS = {
    # tipo: (probabilidad, pedidos por mes, lineas por pedido, cajas por linea, dias credito, prob pago tardio)
    "Tienda de abarrotes": (0.46, (0.8, 2.2), (3, 7), (1, 6), [0, 15], 0.12),
    "Minisuper": (0.24, (1.5, 3.5), (5, 10), (3, 12), [15, 30], 0.15),
    "Restaurante": (0.18, (1.0, 2.5), (3, 6), (2, 10), [30], 0.38),
    "Cafeteria": (0.12, (0.8, 2.0), (2, 5), (1, 5), [15], 0.20),
}
PREFIJOS = {"Tienda de abarrotes": ["Abarrotes", "Tienda", "Miscelanea"], "Minisuper": ["Minisuper", "Super"],
            "Restaurante": ["Restaurante", "Fonda", "Cocina"], "Cafeteria": ["Cafeteria", "Cafe"]}
APELLIDOS = ["Lupita", "Don Pepe", "El Sol", "La Esquina", "San Juan", "Los Arcos", "El Roble", "Santa Fe",
             "La Palma", "Las Flores", "El Centro", "Guadalupe", "La Joya", "El Faro", "Morelos", "Hidalgo",
             "La Estrella", "El Buen Gusto", "Dona Mari", "Juarez", "La Loma", "El Pino", "Aurora", "Del Lago"]


def variante_sucia(region):
    """Escribe la region como la capturaria una persona apurada."""
    r = rng.random()
    if r < 0.10:
        return region.upper()
    if r < 0.18:
        return region.lower()
    if r < 0.26:
        return f" {region}  "
    if r < 0.30:
        return region.replace("Mexico", "México").replace("CDMX", "Cdmx")
    return region


clientes = []
cid = 1
for region, (dmin, dmax, _, expansion) in REGIONES.items():
    n = rng.integers(14, 22) if expansion else rng.integers(38, 56)
    for _ in range(n):
        tipo = rng.choice(list(TIPOS), p=[t[0] for t in TIPOS.values()])
        if expansion:  # la expansion 2025 captura sobre todo negocios chicos
            alta = INICIO + pd.Timedelta(days=int(rng.integers(366, 560)))
        else:
            alta = INICIO + pd.Timedelta(days=int(rng.integers(0, 120))) if rng.random() < 0.85 \
                else INICIO + pd.Timedelta(days=int(rng.integers(120, 640)))
        clientes.append(dict(
            cliente_id=f"C{cid:04d}",
            nombre_negocio=f"{rng.choice(PREFIJOS[tipo])} {rng.choice(APELLIDOS)} {cid}",
            tipo_cliente=tipo, region=variante_sucia(region), region_limpia=region,
            distancia_km=int(rng.integers(dmin, dmax + 1)), dias_credito=int(rng.choice(TIPOS[tipo][4])),
            fecha_alta=alta.date().isoformat(),
        ))
        cid += 1
clientes = pd.DataFrame(clientes)

# ---------------------------------------------------------------- pedidos, entregas, pagos
vend_por_region = vendedores.groupby("region")["vendedor_id"].apply(list).to_dict()
precios = productos.set_index("producto_id")
prod_ids = productos["producto_id"].to_numpy()
# productos populares se piden mas (distribucion tipo Pareto)
peso_prod = rng.pareto(1.3, len(prod_ids)) + 0.2
peso_prod = peso_prod / peso_prod.sum()

lineas, entregas, pagos = [], [], []
pedido_n = 1
for c in clientes.itertuples():
    tipo = TIPOS[c.tipo_cliente]
    region = c.region_limpia
    dmin, dmax, dias_prom, expansion = REGIONES[region]
    freq = rng.uniform(*tipo[1]) * (0.55 if expansion else 1.0)  # clientes lejanos piden menos...
    escala = 0.55 if expansion else 1.0                          # ...y pedidos mas chicos
    vendedor = rng.choice(vend_por_region[region])
    fecha = pd.Timestamp(c.fecha_alta)
    tardes_recientes = []
    while True:
        fecha = fecha + pd.Timedelta(days=max(2, int(rng.exponential(30 / freq))))
        if fecha > FIN:
            break
        anio = fecha.year
        pedido_id = f"PED{pedido_n:06d}"
        pedido_n += 1

        # lineas del pedido
        n_lineas = max(1, int(rng.integers(*tipo[2]) * escala + 0.5))
        subtotal = 0.0
        for prod in rng.choice(prod_ids, size=n_lineas, replace=False, p=peso_prod):
            cajas = max(1, int(rng.integers(tipo[3][0], tipo[3][1] + 1) * escala + 0.5))
            precio = precios.at[prod, f"precio_lista_{anio}"]
            desc = rng.choice([0, 0, 0, 0.02, 0.03, 0.05])
            if anio == 2025 and vendedor in VENDEDORES_DESCUENTO:
                desc = rng.choice([0.08, 0.10, 0.12, 0.15, 0.18])
            lineas.append(dict(pedido_id=pedido_id, fecha=fecha.date().isoformat(), cliente_id=c.cliente_id,
                               vendedor_id=vendedor, producto_id=prod, cantidad_cajas=cajas,
                               precio_unitario=precio, descuento_pct=desc))
            subtotal += cajas * precio * (1 - desc)

        # entrega: en 2025 la flotilla no crecio al ritmo de la expansion -> mas retrasos
        prometida = fecha + pd.Timedelta(days=dias_prom)
        p_tarde = (0.07 if not expansion else 0.22) + (0.08 if anio == 2025 else 0)
        retraso = int(rng.integers(1, 4)) if rng.random() < p_tarde else 0
        entrega = prometida + pd.Timedelta(days=retraso)
        costo_km = 8.5 if anio == 2024 else 9.8  # diesel mas caro en 2025
        costo_envio = round(160 + costo_km * c.distancia_km * rng.uniform(0.9, 1.1), 2)
        entregas.append(dict(pedido_id=pedido_id, ruta=f"R-{region[:3].upper()}",
                             fecha_prometida=prometida.date().isoformat(),
                             fecha_entrega=entrega.date().isoformat(), costo_envio=costo_envio))

        # pago
        total = round(subtotal * 1.16, 2)  # con IVA
        vence = entrega + pd.Timedelta(days=c.dias_credito)
        if rng.random() < tipo[5]:
            fecha_pago = vence + pd.Timedelta(days=int(rng.integers(8, 75)))
        else:
            fecha_pago = vence - pd.Timedelta(days=int(rng.integers(0, min(c.dias_credito, 10) + 1)))
        pagado = fecha_pago <= FIN
        pagos.append(dict(pedido_id=pedido_id, fecha_factura=entrega.strftime("%d/%m/%Y"),
                          fecha_vencimiento=vence.strftime("%d/%m/%Y"),
                          fecha_pago=fecha_pago.strftime("%d/%m/%Y") if pagado else "",
                          monto_facturado=f"${total:,.2f}", monto_pagado=f"${total:,.2f}" if pagado else "$0.00"))

        # abandono: los retrasos recientes empujan al cliente a irse con otro proveedor
        tardes_recientes = (tardes_recientes + [retraso > 0])[-5:]
        p_abandono = 0.002 + 0.30 * (sum(tardes_recientes) / 5) ** 2
        if rng.random() < p_abandono:
            break

ventas = pd.DataFrame(lineas)
entregas = pd.DataFrame(entregas)
pagos = pd.DataFrame(pagos)

# ---------------------------------------------------------------- suciedad controlada
ventas.insert(0, "linea_id", [f"L{i:07d}" for i in range(1, len(ventas) + 1)])
dup = ventas.sample(frac=0.006, random_state=SEMILLA)  # lineas capturadas dos veces
ventas = pd.concat([ventas, dup]).sort_values(["fecha", "linea_id"]).reset_index(drop=True)
espacios = ventas.sample(frac=0.015, random_state=SEMILLA + 1).index
ventas.loc[espacios, "cliente_id"] = ventas.loc[espacios, "cliente_id"] + " "

productos.to_csv(f"{SALIDA}/productos.csv", index=False)
clientes.drop(columns="region_limpia").to_csv(f"{SALIDA}/clientes.csv", index=False)
vendedores.to_csv(f"{SALIDA}/vendedores.csv", index=False)
ventas.to_csv(f"{SALIDA}/ventas.csv", index=False)
entregas.to_csv(f"{SALIDA}/entregas.csv", index=False)
pagos.to_csv(f"{SALIDA}/pagos.csv", index=False)

print(f"productos: {len(productos)} | clientes: {len(clientes)} | vendedores: {len(vendedores)}")
print(f"ventas: {len(ventas)} lineas ({len(dup)} duplicadas) | pedidos: {len(entregas)} | pagos: {len(pagos)}")
