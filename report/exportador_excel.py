# Python
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

# Librerías
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

# Proyecto
from report.exportador import Exportador
from report.informe import Informe


class ExportadorExcel(Exportador):
    """ Exporta un Informe a Excel (.xlsx) usando openpyxl """

    FILA_ENCABEZADO = 4  # filas 1-2: título y quién lo generó; fila 3 en blanco

    @property
    def extension(self) -> str:
        return "xlsx"

    @property
    def nombre_formato(self) -> str:
        return "Excel"

    @staticmethod
    def _valor_celda(valor):
        """ Fechas y números se guardan con su tipo real para poder ordenar y sumar en Excel """
        if isinstance(valor, Decimal):
            return float(valor)
        if isinstance(valor, (int, float, date, datetime)) or valor is None:
            return valor
        texto = str(valor)
        # Un texto que empieza con = + - @ Excel lo trataría como fórmula (inyección de fórmulas)
        return "'" + texto if texto[:1] in ("=", "+", "-", "@") else texto

    def _escribir(self, informe: Informe, ruta: Path) -> None:
        libro = Workbook()
        hoja = libro.active
        hoja.title = informe.titulo[:31]  # Excel limita el nombre de la hoja a 31 caracteres

        hoja["A1"] = f"EcoTech Solutions - {informe.titulo}"
        hoja["A1"].font = Font(bold=True, size=14)
        hoja["A2"] = (informe.subtitulo + " | " if informe.subtitulo else "") + informe.encabezado()
        hoja["A2"].font = Font(italic=True, size=9)

        # Encabezados de la tabla
        relleno = PatternFill("solid", fgColor="2E7D32")
        for numero, columna in enumerate(informe.columnas, start=1):
            celda = hoja.cell(row=self.FILA_ENCABEZADO, column=numero, value=columna)
            celda.font = Font(bold=True, color="FFFFFF")
            celda.fill = relleno

        # Datos (con formato de fecha y de número)
        for desplazamiento, fila in enumerate(informe.filas, start=1):
            for numero, valor in enumerate(fila, start=1):
                celda = hoja.cell(row=self.FILA_ENCABEZADO + desplazamiento, column=numero,
                                  value=self._valor_celda(valor))
                if isinstance(valor, datetime):
                    celda.number_format = "DD-MM-YYYY HH:MM"
                elif isinstance(valor, date):
                    celda.number_format = "DD-MM-YYYY"
                elif isinstance(valor, (float, Decimal)):
                    celda.number_format = "#,##0.00"

        # Ancho de cada columna según el texto más largo (máximo 60)
        textos = [informe.columnas] + informe.filas_como_texto()
        for numero in range(1, len(informe.columnas) + 1):
            largo = max(len(str(fila[numero - 1])) for fila in textos)
            hoja.column_dimensions[get_column_letter(numero)].width = min(max(largo + 2, 10), 60)

        hoja.freeze_panes = hoja.cell(row=self.FILA_ENCABEZADO + 1, column=1)  # encabezado fijo al bajar
        libro.save(ruta)


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: ExportadorExcel con openpyxl: título, encabezados en negrita
  con color, ancho de columnas automático y encabezado fijo al desplazarse.
- ¿Qué se adoptó?: Guardar fechas y números con su tipo real (no como texto), para que en
  Excel se puedan ordenar, filtrar y sumar.
- ¿Qué se modificó?: _valor_celda() antepone un apóstrofe a los textos que empiezan con
  = + - @ : una descripción de horas escrita como "=HYPERLINK(...)" se ejecutaría como
  fórmula al abrir el archivo (inyección de fórmulas / CSV injection).
- ¿Qué se descartó?: Exportar a CSV (ver abajo).

Código propuesto por la IA y DESCARTADO:

    with open(ruta, "w") as archivo:
        csv.writer(archivo).writerows(informe.filas)

Por qué se descartó: el CSV no guarda formato (negrita, anchos, fechas) y Excel en español
lo abre mal porque espera ";" como separador y otra codificación para las tildes.
"""
