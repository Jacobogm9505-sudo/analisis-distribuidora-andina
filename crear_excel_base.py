"""Crea el libro base de Excel con los catalogos como Tablas de Excel.

Las ventas y los clientes NO se cargan aqui: entran por Power Query desde los CSV
crudos, porque son los archivos que hay que limpiar (duplicados, espacios, regiones).
"""

import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

SALIDA = "excel/distribuidora_andina.xlsx"
AZUL = "2A78D6"

wb = Workbook()
leeme = wb.active
leeme.title = "LEEME"
lineas = [
    ("Distribuidora Andina · Análisis de rentabilidad 2024-2025", Font(bold=True, size=16)),
    ("Pregunta de negocio: vendemos más que el año pasado, pero ganamos menos. ¿Por qué?", Font(italic=True, size=12)),
    ("", None),
    ("Cómo está armado este libro", Font(bold=True, size=13, color=AZUL)),
    ("1. Power Query importa ventas.csv y clientes.csv (datos crudos) y los limpia:", None),
    ("   · quita espacios en cliente_id y elimina líneas de venta duplicadas", None),
    ("   · unifica las 27 formas en que estaba escrita la región en solo 7 regiones", None),
    ("2. La tabla 'ventas' trae datos de los catálogos con XLOOKUP (BUSCARX):", None),
    ("   · categoría y costo del producto (costo 2024 o 2025 según el año de la venta)", None),
    ("   · región y tipo de cliente", None),
    ("3. Tablas dinámicas: margen por región y año, descuentos por vendedor y ventas por categoría.", None),
    ("", None),
    ("Para actualizar con datos nuevos: Datos > Actualizar todo.", Font(bold=True)),
    ("Los CSV de origen están en la carpeta datos_crudos del proyecto.", None),
]
for i, (texto, fuente) in enumerate(lineas, start=1):
    celda = leeme.cell(row=i, column=1, value=texto)
    if fuente:
        celda.font = fuente
leeme.column_dimensions["A"].width = 100
leeme.sheet_view.showGridLines = False


def hoja_tabla(nombre, df, formatos=None):
    ws = wb.create_sheet(nombre)
    ws.append(list(df.columns))
    for fila in df.itertuples(index=False):
        ws.append(list(fila))
    ref = f"A1:{get_column_letter(df.shape[1])}{len(df) + 1}"
    tabla = Table(displayName=nombre, ref=ref)
    tabla.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(tabla)
    for i, col in enumerate(df.columns, start=1):
        ws.column_dimensions[get_column_letter(i)].width = max(12, min(40, len(col) + 4))
        if formatos and col in formatos:
            for (c,) in ws.iter_rows(min_row=2, min_col=i, max_col=i):
                c.number_format = formatos[col]
    ws.freeze_panes = "A2"
    return ws


dinero = '"$"#,##0.00'
hoja_tabla("productos", pd.read_csv("datos_crudos/productos.csv"),
           {c: dinero for c in ["precio_lista_2024", "costo_2024", "precio_lista_2025", "costo_2025"]})
hoja_tabla("vendedores", pd.read_csv("datos_crudos/vendedores.csv"))

wb.save(SALIDA)
print(f"Libro base creado: {SALIDA}")
