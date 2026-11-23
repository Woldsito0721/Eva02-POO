# Python
from datetime import date, datetime
from decimal import Decimal


class Informe():
    """ Datos de un reporte ya armado: título, columnas y filas. No sabe de PDF ni de Excel """

    def __init__(self, titulo: str, columnas: list, filas: list, generado_por: str,
                 nombre_archivo: str, subtitulo: str = None):
        if not isinstance(titulo, str) or not titulo.strip():
            raise ValueError("El informe necesita un título")
        if not columnas:
            raise ValueError("El informe necesita al menos una columna")
        if any(len(fila) != len(columnas) for fila in filas):
            raise ValueError("Cada fila debe tener un valor por columna")
        # El nombre del archivo lo fija el sistema (nunca lo escribe el usuario):
        # solo letras minúsculas, números y guion bajo, para no salir de la carpeta reportes/
        if not nombre_archivo or not all(c.islower() or c.isdigit() or c == "_" for c in nombre_archivo):
            raise ValueError("Nombre de archivo de informe inválido")

        self.__titulo = titulo.strip()
        self.__subtitulo = subtitulo
        self.__columnas = tuple(columnas)
        self.__filas = tuple(tuple(fila) for fila in filas)  # inmutable: el exportador solo lee
        self.__generado_por = generado_por
        self.__fecha_generacion = datetime.now()
        self.__nombre_archivo = nombre_archivo

    @property
    def titulo(self):
        return self.__titulo

    @property
    def subtitulo(self):
        return self.__subtitulo

    @property
    def columnas(self):
        return self.__columnas

    @property
    def filas(self):
        return self.__filas

    @property
    def generado_por(self):
        return self.__generado_por

    @property
    def fecha_generacion(self):
        return self.__fecha_generacion

    @property
    def nombre_archivo(self):
        return self.__nombre_archivo

    def esta_vacio(self) -> bool:
        return len(self.__filas) == 0

    @staticmethod
    def formatear(valor) -> str:
        """ Texto de una celda: fechas dd-mm-aaaa, números con 2 decimales, None vacío """
        if valor is None:
            return ""
        if isinstance(valor, datetime):
            return f"{valor:%d-%m-%Y %H:%M}"
        if isinstance(valor, date):
            return f"{valor:%d-%m-%Y}"
        if isinstance(valor, (float, Decimal)):
            return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")  # 1.234,50
        return str(valor)

    def filas_como_texto(self) -> list:
        return [[self.formatear(valor) for valor in fila] for fila in self.__filas]

    def encabezado(self) -> str:
        return f"Generado por {self.__generado_por} el {self.__fecha_generacion:%d-%m-%Y %H:%M}"

    def __str__(self):
        return f"Informe {self.__titulo} ({len(self.__filas)} filas)"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase Informe con título, columnas, filas, usuario que lo
  generó y fecha, más formatear() para mostrar fechas y números al estilo chileno.
- ¿Qué se adoptó?: Separar los DATOS del reporte (Informe) del FORMATO de salida (Exportador),
  como en el diagrama de la Unidad 1: el mismo Informe se exporta a PDF o a Excel.
- ¿Qué se modificó?: Las filas se guardan como tuplas (solo lectura) y el nombre del archivo
  se valida (solo minúsculas, números y _): lo define el sistema y no puede contener rutas
  como "../" que escriban fuera de la carpeta reportes/.
- ¿Qué se descartó?: Que cada reporte escribiera su propio PDF (ver abajo).

Código propuesto por la IA y DESCARTADO:

    def reporte_horas_pdf(self):
        pdf = FPDF(); pdf.add_page()
        for fila in repositorio.horas_por_proyecto():
            pdf.cell(text=str(fila))
        pdf.output("reporte.pdf")

Por qué se descartó: mezcla la consulta, el formato y el archivo en una sola función; para
tener 6 reportes en 2 formatos habría que escribir 12 funciones casi iguales. Con Informe +
Exportador son 6 informes y 2 exportadores.
"""
