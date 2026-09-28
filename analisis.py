"""Analisis de rentabilidad de Distribuidora Andina (2024 vs 2025).

Pregunta de negocio: "Vendemos mas que el ano pasado, pero ganamos menos. ¿Por que?"

Pasos:
  1. Limpia los archivos crudos (duplicados, espacios, regiones, fechas y montos como texto)
  2. Une ventas + productos + clientes + vendedores + entregas + pagos
  3. Calcula la ganancia real por pedido (despues del costo de envio)
  4. Explica la caida de la ganancia y genera los graficos del reporte

Salidas: datos_limpios/*.csv, graficos/*.png y resultados.json
"""

import json
import warnings

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

warnings.filterwarnings("ignore", message="Mean of empty slice")  # clientes con un solo pedido

CRUDOS, LIMPIOS, GRAFICOS ="datos_crudos", "datos_limpios", "graficos"
CORTE = pd.Timestamp("2025-12-31")

# Paleta (validada para daltonismo): azul = foco, gris = contexto
AZUL, NARANJA, GRIS = "#2a78d6", "#eb6834", "#b9b8b3"
TEXTO, TEXTO_2, FONDO, REJILLA = "#0b0b0b", "#52514e", "#fcfcfb", "#e6e5e1"

plt.rcParams.update({
    "figure.facecolor": FONDO, "axes.facecolor": FONDO, "savefig.facecolor": FONDO,
    "font.size": 11, "text.color": TEXTO, "axes.labelcolor": TEXTO_2,
    "xtick.color": TEXTO_2, "ytick.color": TEXTO_2, "axes.edgecolor": REJILLA,
    "axes.spines.top": False, "axes.spines.right": False, "axes.titleweight": "bold",
    "axes.titlesize": 14, "axes.titlelocation": "left", "axes.titlepad": 14,
})

REGIONES = {"toluca": "Toluca", "metepec": "Metepec", "lerma": "Lerma", "zinacantepec": "Zinacantepec",
            "tenancingo": "Tenancingo", "valle de bravo": "Valle de Bravo", "cdmx poniente": "CDMX Poniente"}
EXPANSION = {"Tenancingo", "Valle de Bravo", "CDMX Poniente"}


def pesos(x):
    return f"${x / 1e6:,.1f} M"


# ------------------------------------------------------------------ 1. limpieza
ventas = pd.read_csv(f"{CRUDOS}/ventas.csv")
filas_crudas = len(ventas)
# Orden importante: primero quitar espacios, despues duplicados. Si se invierte, las copias
# que solo difieren por un espacio en cliente_id no se detectan como duplicadas.
ventas["cliente_id"] = ventas["cliente_id"].str.strip()
ventas = ventas.drop_duplicates()
duplicados = filas_crudas - len(ventas)
ventas["fecha"] = pd.to_datetime(ventas["fecha"])
ventas["anio"] = ventas["fecha"].dt.year

productos = pd.read_csv(f"{CRUDOS}/productos.csv")
vendedores = pd.read_csv(f"{CRUDOS}/vendedores.csv")
clientes = pd.read_csv(f"{CRUDOS}/clientes.csv")
variantes_region = clientes["region"].nunique()
clientes["region"] = clientes["region"].str.strip().str.lower().str.replace("é", "e").map(REGIONES)
assert clientes["region"].notna().all(), "Hay regiones sin mapear"

entregas = pd.read_csv(f"{CRUDOS}/entregas.csv", parse_dates=["fecha_prometida", "fecha_entrega"])
pagos = pd.read_csv(f"{CRUDOS}/pagos.csv", dtype=str)
for col in ["fecha_factura", "fecha_vencimiento", "fecha_pago"]:
    pagos[col] = pd.to_datetime(pagos[col], format="%d/%m/%Y")
for col in ["monto_facturado", "monto_pagado"]:
    pagos[col] = pagos[col].str.replace(r"[$,]", "", regex=True).astype(float)

# ------------------------------------------------------------------ 2. union y metricas por linea
ventas = ventas.merge(productos, on="producto_id", how="left")
assert ventas["categoria"].notna().all(), "Hay ventas con producto desconocido"
ventas["venta_bruta"] = ventas["cantidad_cajas"] * ventas["precio_unitario"]
ventas["descuento"] = ventas["venta_bruta"] * ventas["descuento_pct"]
ventas["venta_neta"] = ventas["venta_bruta"] - ventas["descuento"]
ventas["costo"] = ventas["cantidad_cajas"] * np.where(ventas["anio"] == 2024, ventas["costo_2024"], ventas["costo_2025"])
ventas["margen_bruto"] = ventas["venta_neta"] - ventas["costo"]

# ------------------------------------------------------------------ 3. nivel pedido (con envio)
pedidos = (ventas.groupby(["pedido_id", "fecha", "anio", "cliente_id", "vendedor_id"], as_index=False)
           [["venta_bruta", "descuento", "venta_neta", "costo", "margen_bruto"]].sum()
           .merge(entregas, on="pedido_id", how="left")
           .merge(clientes, on="cliente_id", how="left")
           .merge(pagos, on="pedido_id", how="left"))
pedidos["ganancia"] = pedidos["margen_bruto"] - pedidos["costo_envio"]
pedidos["entrega_tarde"] = pedidos["fecha_entrega"] > pedidos["fecha_prometida"]

ventas.drop(columns=["precio_lista_2024", "costo_2024", "precio_lista_2025", "costo_2025"]) \
      .to_csv(f"{LIMPIOS}/ventas_limpias.csv", index=False)
pedidos.to_csv(f"{LIMPIOS}/pedidos.csv", index=False)

# ------------------------------------------------------------------ 4. resultados
anual = pedidos.groupby("anio")[["venta_bruta", "descuento", "venta_neta", "costo", "margen_bruto",
                                 "costo_envio", "ganancia"]].sum()
anual["margen_ganancia"] = anual["ganancia"] / anual["venta_neta"]
a24, a25 = anual.loc[2024], anual.loc[2025]

# Puente de ganancia 2024 -> 2025 (suma exacta)
delta_bruta = a25.venta_bruta - a24.venta_bruta
efecto_volumen = delta_bruta * (1 - a24.costo / a24.venta_bruta)
efecto_costo = (delta_bruta - (a25.costo - a24.costo)) - efecto_volumen
efecto_descuento = -(a25.descuento - a24.descuento)
efecto_envio = -(a25.costo_envio - a24.costo_envio)
assert abs(a24.ganancia + efecto_volumen + efecto_costo + efecto_descuento + efecto_envio - a25.ganancia) < 1

desc_vendedor = (ventas.groupby(["vendedor_id", "anio"]).apply(lambda d: d.descuento.sum() / d.venta_bruta.sum())
                 .unstack().join(vendedores.set_index("vendedor_id")[["vendedor", "region"]]))

region = pedidos[pedidos.anio == 2025].groupby("region").agg(
    venta_neta=("venta_neta", "sum"), ganancia=("ganancia", "sum"), pedidos=("pedido_id", "count"),
    ticket_promedio=("venta_neta", "mean"), envio_promedio=("costo_envio", "mean"),
    entregas_tarde=("entrega_tarde", "mean"))
region["margen_ganancia"] = region["ganancia"] / region["venta_neta"]

# Clientes perdidos: >= 3 pedidos y sin comprar en mas de 90 dias (o 3 veces su frecuencia habitual)
g = pedidos.sort_values("fecha").groupby("cliente_id")
cli = pd.DataFrame({"ultimo": g["fecha"].max(), "pedidos": g.size(), "tarde": g["entrega_tarde"].mean(),
                    "gap": g["fecha"].apply(lambda s: s.diff().dt.days.median())})
cli = cli[cli.pedidos >= 3].copy()
cli["perdido"] = (CORTE - cli["ultimo"]).dt.days > np.maximum(90, 3 * cli["gap"])
cli["grupo"] = pd.cut(cli["tarde"], [-0.01, 0.05, 0.15, 0.30, 1],
                      labels=["0-5%", "5-15%", "15-30%", "Más de 30%"])
abandono = cli.groupby("grupo").agg(clientes=("perdido", "size"), perdidos=("perdido", "mean"))

# Cobranza al cierre de 2025: facturas vencidas y sin pagar
vencido = pedidos[(pedidos.fecha_vencimiento < CORTE) & (pedidos.fecha_pago.isna() | (pedidos.fecha_pago > CORTE))]
cartera = vencido.groupby("tipo_cliente")["monto_facturado"].sum().sort_values()
pago_tarde = (pedidos.fecha_pago > pedidos.fecha_vencimiento).groupby(pedidos.tipo_cliente).mean()

# Pareto de clientes 2025
gan_cli = pedidos[pedidos.anio == 2025].groupby("cliente_id")["ganancia"].sum().sort_values(ascending=False)
top20 = gan_cli.head(int(len(gan_cli) * 0.2)).sum() / gan_cli.sum()
clientes_negativos = int((gan_cli < 0).sum())

resultados = {
    "limpieza": {"lineas_crudas": filas_crudas, "duplicados_eliminados": duplicados,
                 "variantes_region": int(variantes_region), "regiones_reales": len(REGIONES)},
    "anual": {int(k): {c: round(float(v), 2) for c, v in row.items()} for k, row in anual.iterrows()},
    "crecimiento_ventas": round(float(a25.venta_neta / a24.venta_neta - 1), 4),
    "cambio_ganancia": round(float(a25.ganancia / a24.ganancia - 1), 4),
    "puente": {"ganancia_2024": round(a24.ganancia), "mas_volumen": round(efecto_volumen),
               "costo_proveedor": round(efecto_costo), "descuentos": round(efecto_descuento),
               "envio": round(efecto_envio), "ganancia_2025": round(a25.ganancia)},
    "descuento_vendedor": {k: {"vendedor": r.vendedor, "region": r.region,
                               "d2024": None if pd.isna(r[2024]) else round(float(r[2024]), 4),
                               "d2025": round(float(r[2025]), 4)} for k, r in desc_vendedor.iterrows()},
    "region_2025": {k: {c: round(float(v), 4) for c, v in r.items()} for k, r in region.iterrows()},
    "entregas_tarde": {int(k): round(float(v), 4) for k, v in pedidos.groupby("anio")["entrega_tarde"].mean().items()},
    "abandono_por_retrasos": {str(k): {"clientes": int(r.clientes), "perdidos": round(float(r.perdidos), 4)}
                              for k, r in abandono.iterrows()},
    "cartera_vencida": {k: round(float(v), 2) for k, v in cartera.items()},
    "pago_tarde_por_tipo": {k: round(float(v), 4) for k, v in pago_tarde.items()},
    "pareto_top20_ganancia": round(float(top20), 4),
    "clientes_con_perdida_2025": clientes_negativos, "clientes_2025": int(len(gan_cli)),
}
with open("resultados.json", "w", encoding="utf-8") as f:
    json.dump(resultados, f, ensure_ascii=False, indent=2)

# ------------------------------------------------------------------ 5. graficos


def guardar(fig, nombre, nota=None):
    if nota:
        fig.text(0.01, 0.01, nota, fontsize=9, color=TEXTO_2, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.04 if nota else 0, 1, 1))
    fig.savefig(f"{GRAFICOS}/{nombre}", dpi=160)
    plt.close(fig)


# 5.1 Puente de ganancia
pasos = [("Ganancia 2024", a24.ganancia, "total"), ("Más volumen", efecto_volumen, "delta"),
         ("Costos de proveedor\nsuben más que precios", efecto_costo, "delta"),
         ("Descuentos", efecto_descuento, "delta"), ("Envío", efecto_envio, "delta"),
         ("Ganancia 2025", a25.ganancia, "total")]
fig, ax = plt.subplots(figsize=(10, 5.6))
acumulado = 0
for i, (etiqueta, valor, tipo) in enumerate(pasos):
    if tipo == "total":
        base, alto, color = 0, valor, GRIS if i == 0 else AZUL
        acumulado = valor
    else:
        base = acumulado if valor >= 0 else acumulado + valor
        alto, color = abs(valor), AZUL if valor >= 0 else NARANJA
        acumulado += valor
    ax.bar(i, alto, bottom=base, color=color, width=0.62)
    texto = pesos(valor) if tipo == "total" else ("+" if valor >= 0 else "−") + pesos(abs(valor))
    ax.text(i, base + alto + 1.2e5, texto, ha="center", va="bottom", fontsize=10.5, color=TEXTO, fontweight="bold")
    if i < len(pasos) - 1:
        ax.plot([i + 0.31, i + 0.69], [acumulado, acumulado], color=TEXTO_2, lw=0.8, ls=":")
ax.set_xticks(range(len(pasos)))
ax.set_xticklabels([p[0] for p in pasos], fontsize=10)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x / 1e6:.0f} M"))
ax.set_ylim(0, a24.ganancia * 1.32)
ax.grid(axis="y", color=REJILLA, lw=0.8)
ax.set_axisbelow(True)
ax.set_title(f"Vendimos {resultados['crecimiento_ventas']:.1%} más, pero ganamos "
             f"{abs(resultados['cambio_ganancia']):.1%} menos")
guardar(fig, "1_puente_ganancia.png", "Ganancia = venta neta − costo de producto − costo de envío. Cifras en MXN sin IVA.")

# 5.2 Descuento promedio por vendedor
d = desc_vendedor.copy()
d["etiqueta"] = d["vendedor"] + " (" + d["region"] + ")"
d = d.sort_values(2025)
fig, ax = plt.subplots(figsize=(10, 5.6))
colores = [NARANJA if x > 0.05 else GRIS for x in d[2025]]
ax.barh(d["etiqueta"], d[2025], color=colores, height=0.62)
for y, (x, x24) in enumerate(zip(d[2025], d[2024])):
    ref = "nuevo en 2025" if pd.isna(x24) else f"2024: {x24:.1%}"
    ax.text(x + 0.002, y, f"{x:.1%}  ({ref})", va="center", fontsize=9.5, color=TEXTO_2)
ax.xaxis.set_major_locator(mticker.MultipleLocator(0.02))
ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
ax.set_xlim(0, d[2025].max() * 1.45)
ax.grid(axis="x", color=REJILLA, lw=0.8)
ax.set_axisbelow(True)
ax.set_title("3 vendedores dan descuentos de ~12%; el resto, menos de 2%")
guardar(fig, "2_descuento_por_vendedor.png", "Descuento promedio sobre la venta a precio de lista, 2025.")

# 5.3 Ganancia por region
r = region.sort_values("margen_ganancia")
fig, ax = plt.subplots(figsize=(10, 5.2))
ax.barh(r.index, r["margen_ganancia"], color=[NARANJA if i in EXPANSION else GRIS for i in r.index], height=0.62)
ax.axvline(0, color=TEXTO_2, lw=1)
for y, (m, t, e) in enumerate(zip(r["margen_ganancia"], r["ticket_promedio"], r["envio_promedio"])):
    x = m + (0.006 if m >= 0 else -0.006)
    ax.text(x, y, f"{m:.0%}   ticket \\${t:,.0f} · envío \\${e:,.0f}", va="center",
            ha="left" if m >= 0 else "right", fontsize=9.5, color=TEXTO_2)
ax.xaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
ax.set_xlim(r["margen_ganancia"].min() - 0.33, r["margen_ganancia"].max() + 0.25)
ax.grid(axis="x", color=REJILLA, lw=0.8)
ax.set_axisbelow(True)
ax.set_title("Las 3 regiones nuevas (en naranja) pierden dinero en cada pedido")
guardar(fig, "3_ganancia_por_region.png", "Margen de ganancia 2025 = ganancia / venta neta. Ticket y envío promedio por pedido.")

# 5.4 Retrasos y abandono
fig, ax = plt.subplots(figsize=(9, 5.2))
colores = [GRIS, NARANJA, NARANJA, NARANJA]
ax.bar(abandono.index.astype(str), abandono["perdidos"], color=colores, width=0.6)
for i, (p, n) in enumerate(zip(abandono["perdidos"], abandono["clientes"])):
    ax.text(i, p + 0.008, f"{p:.0%}", ha="center", fontsize=12, fontweight="bold", color=TEXTO)
    ax.text(i, -0.035, f"{n} clientes", ha="center", fontsize=9, color=TEXTO_2)
ax.yaxis.set_major_formatter(mticker.PercentFormatter(1.0, decimals=0))
ax.set_ylim(-0.06, abandono["perdidos"].max() * 1.3)
ax.set_xlabel("% de sus pedidos entregados tarde", labelpad=18)
ax.set_ylabel("Clientes que dejaron de comprar")
ax.grid(axis="y", color=REJILLA, lw=0.8)
ax.set_axisbelow(True)
ax.set_title("Con más de 5% de entregas tarde, el abandono se duplica")
guardar(fig, "4_retrasos_y_abandono.png", "Cliente perdido: 3+ pedidos y sin comprar en más de 90 días (o 3 veces su frecuencia habitual).")

# 5.5 Cartera vencida
fig, ax = plt.subplots(figsize=(9, 4.6))
ax.barh(cartera.index, cartera.values, color=[NARANJA if k == cartera.idxmax() else GRIS for k in cartera.index],
        height=0.6)
for y, (k, v) in enumerate(cartera.items()):
    ax.text(v + cartera.max() * 0.02, y, f"\\${v:,.0f}  ·  paga tarde {pago_tarde[k]:.0%} de sus facturas",
            va="center", fontsize=9.5, color=TEXTO_2)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"${x / 1e3:,.0f} mil"))
ax.set_xlim(0, cartera.max() * 1.9)
ax.grid(axis="x", color=REJILLA, lw=0.8)
ax.set_axisbelow(True)
ax.set_title("Los minisúpers deben más;\nlos restaurantes pagan tarde más seguido")
guardar(fig, "5_cartera_vencida.png", "Facturas vencidas y sin pagar al 31-dic-2025, con IVA.")

print(json.dumps({k: resultados[k] for k in ["limpieza", "crecimiento_ventas", "cambio_ganancia", "puente",
                                             "pareto_top20_ganancia", "clientes_con_perdida_2025"]},
                 ensure_ascii=False, indent=1))
