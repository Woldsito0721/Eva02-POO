# Python
from abc import ABC, abstractmethod
from pathlib import Path

# Proyecto
from report.informe import Informe

# Carpeta reportes/ en la raíz del proyecto (sin importar desde dónde se ejecute main.py)
CARPETA_REPORTES = Path(__file__).resolve().parent.parent / "reportes"


class Exportador(ABC):
    """ Convierte un Informe en un archivo. Cada formato (PDF, Excel) es una clase hija """

    def __init__(self, carpeta: Path = CARPETA_REPORTES):
        self._carpeta = Path(carpeta)

    @property
    @abstractmethod
    def extension(self) -> str:
        """ Extensión del archivo, ej. 'pdf' o 'xlsx' """

    @property
    @abstractmethod
    def nombre_formato(self) -> str:
        """ Nombre para mostrar en el menú, ej. 'PDF' o 'Excel' """

    @abstractmethod
    def _escribir(self, informe: Informe, ruta: Path) -> None:
        """ Cada formato escribe el archivo a su manera (polimorfismo) """

    def exportar(self, informe: Informe) -> Path:
        """ Crea la carpeta si no existe, arma el nombre con fecha y hora y escribe el archivo """
        if informe.esta_vacio():
            raise ValueError("El informe no tiene datos para exportar")

        self._carpeta.mkdir(parents=True, exist_ok=True)
        nombre = f"{informe.nombre_archivo}_{informe.fecha_generacion:%Y-%m-%d_%H%M%S}.{self.extension}"
        ruta = self._carpeta / nombre
        try:
            self._escribir(informe, ruta)
        except OSError as e:
            # Ej.: el archivo está abierto en Excel o no hay permiso de escritura
            raise ValueError(f"No se pudo guardar el archivo ({type(e).__name__})") from e
        return ruta


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase abstracta Exportador con exportar() y el método
  abstracto _escribir() que implementan ExportadorPDF y ExportadorExcel.
- ¿Qué se adoptó?: Patrón "método plantilla": exportar() hace lo común (carpeta, nombre con
  fecha, manejo de errores) y cada hija solo escribe su formato. main.py llama a
  exportador.exportar(informe) sin saber si es PDF o Excel (polimorfismo, como ServicioAPI).
- ¿Qué se modificó?: La carpeta se calcula desde la ubicación del archivo, así el reporte
  queda en Eva02-POO/reportes/ aunque se ejecute desde otra carpeta; el nombre lleva
  fecha, hora y segundos para no sobrescribir reportes anteriores; los errores de disco se
  convierten en ValueError con un mensaje corto (sin rutas internas).
- ¿Qué se descartó?: Pedirle al usuario el nombre o la ruta del archivo (ver abajo).

Código propuesto por la IA y DESCARTADO:

    ruta = input("Nombre del archivo: ")
    self._escribir(informe, ruta)

Por qué se descartó: el usuario podría escribir "../../config/configuracion_app.py" y
sobrescribir archivos del sistema (path traversal). El nombre lo arma el programa.
"""
