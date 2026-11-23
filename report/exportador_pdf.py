# Python
from pathlib import Path

# Librerías
from fpdf import FPDF
from fpdf.fonts import FontFace

# Proyecto
from report.exportador import Exportador
from report.informe import Informe


class ExportadorPDF(Exportador):
    """ Exporta un Informe a PDF (hoja A4 horizontal, con tabla) usando fpdf2 """

    @property
    def extension(self) -> str:
        return "pdf"

    @property
    def nombre_formato(self) -> str:
        return "PDF"

    @staticmethod
    def _texto(valor: str) -> str:
        # Las fuentes base del PDF usan latin-1: tildes, ñ y ° sí; otros símbolos se reemplazan
        return valor.encode("latin-1", "replace").decode("latin-1")

    def _escribir(self, informe: Informe, ruta: Path) -> None:
        pdf = FPDF(orientation="L", format="A4")
        pdf.set_title(self._texto(informe.titulo))
        pdf.set_author("EcoTech Solutions")
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Encabezado
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 10, self._texto(f"EcoTech Solutions - {informe.titulo}"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 10)
        if informe.subtitulo:
            pdf.cell(0, 6, self._texto(informe.subtitulo), new_x="LMARGIN", new_y="NEXT")
        pdf.cell(0, 6, self._texto(informe.encabezado()), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

        # Tabla: la primera fila son los encabezados (en negrita y con fondo)
        pdf.set_font("Helvetica", "", 9)
        estilo_encabezado = FontFace(emphasis="BOLD", fill_color=(46, 125, 50), color=(255, 255, 255))
        with pdf.table(headings_style=estilo_encabezado, line_height=6,
                       cell_fill_color=(240, 247, 240), cell_fill_mode="ROWS") as tabla:
            fila_pdf = tabla.row()
            for columna in informe.columnas:
                fila_pdf.cell(self._texto(columna))
            for fila in informe.filas_como_texto():
                fila_pdf = tabla.row()
                for valor in fila:
                    fila_pdf.cell(self._texto(valor))

        pdf.ln(4)
        pdf.set_font("Helvetica", "I", 8)
        pdf.cell(0, 5, self._texto(f"Total de filas: {len(informe.filas)}"))
        pdf.output(str(ruta))


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: ExportadorPDF con fpdf2: hoja horizontal, título, usuario
  y fecha de generación, y una tabla con encabezado de color y filas alternadas.
- ¿Qué se adoptó?: pdf.table() de fpdf2, que ajusta el alto de cada fila al texto y
  repite el encabezado de la tabla en cada página nueva.
- ¿Qué se modificó?: Se agregó _texto() porque las fuentes base del PDF usan latin-1: un
  carácter fuera de esa tabla detenía la exportación con un error; ahora se reemplaza por "?".
- ¿Qué se descartó?: reportlab (ver abajo).

Código propuesto por la IA y DESCARTADO:

    from reportlab.platypus import SimpleDocTemplate, Table
    doc = SimpleDocTemplate(str(ruta)); doc.build([Table(datos)])

Por qué se descartó: reportlab es más pesado y su API (platypus, estilos por coordenadas)
es más difícil de explicar en la defensa; fpdf2 genera la misma tabla en menos líneas.
"""
