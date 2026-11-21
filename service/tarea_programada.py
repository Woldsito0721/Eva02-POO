from __future__ import annotations
from datetime import datetime
import threading
import time
from typing import TYPE_CHECKING

from service.servicio_api import ErrorServicioExterno
from service.servicio_clima import ServicioClima
from service.servicio_indicadores import ServicioIndicadores

if TYPE_CHECKING:
    from model.proyecto import Proyecto
    from database.repositorios import RepositorioDatoExterno

"""
REGISTRO DE USO DE IA:
- ¿Qué se solicitó?: Implementar TareaProgramada en Python para ejecutar automáticamente a las 08:00 horas la consulta de clima e indicadores económicos según los proyectos activos.
- ¿Qué generó la herramienta?: Un bucle infinito while True en el hilo principal con listas de ciudades y monedas escritas en duro (hardcoded) y sin manejo de errores individuales.
- ¿Qué se adoptó?: La composición con ServicioClima, ServicioIndicadores y RepositorioDatoExterno definida en el diagrama UML.
- ¿Qué se modificó?: Se ejecutó la espera horaria (08:00) en un hilo daemon (threading.Thread) para no bloquear el menú de consola, se cargaron ciudades/monedas dinámicamente desde los proyectos activos y se aislaron los errores por ítem.
  Tras la auditoría: se lee ciudad/moneda/id_proyecto tanto de objetos Proyecto como de diccionarios (se quitó el truco "_Proyecto__ciudad"), los errores se informan con mensaje_seguro() en vez de "pass", el hilo captura cualquier excepción para no morir en silencio, y el parámetro "repo" pasó a llamarse "repositorio".
- ¿Qué se descartó?: El bloqueo del hilo principal y el uso de ciudades o monedas estáticas.
- Justificación: Garantiza la continuidad operativa del menú interactivo y permite escalar automáticamente al registrar nuevos proyectos internacionales.
"""


def leer_dato(proyecto, campo: str):
    """ Lee un campo de un objeto Proyecto (property) o de un diccionario del repositorio """
    if isinstance(proyecto, dict):
        return proyecto.get(campo)
    return getattr(proyecto, campo, None)


# Automatiza a las 08:00 horas la recolección de clima y divisas de los proyectos activos y los persiste en BD.
class TareaProgramada:
    def __init__(
        self,
        clima: ServicioClima,
        indicadores: ServicioIndicadores,
        repositorio: RepositorioDatoExterno,
    ) -> None:
        self.__hora: str = "08:00"
        self.__servicio_clima: ServicioClima = clima
        self.__servicio_indicadores: ServicioIndicadores = indicadores
        self.__repositorio: RepositorioDatoExterno = repositorio
        self.__proyectos: list = []
        self.__ultima_ejecucion: str = ""
        self.__activa: bool = False
        self.__hilo: threading.Thread | None = None

    def configurar_proyectos(self, proyectos: list[Proyecto]) -> None:
        self.__proyectos = list(proyectos)

    def programar(self) -> None:
        if self.__activa:
            return
        self.__activa = True
        self.__hilo = threading.Thread(target=self._bucle_planificador, daemon=True)
        self.__hilo.start()

    def detener(self) -> None:
        self.__activa = False

    def _bucle_planificador(self) -> None:
        while self.__activa:
            ahora = datetime.now()
            hora_actual = ahora.strftime("%H:%M")
            fecha_hoy = ahora.strftime("%Y-%m-%d")

            if hora_actual == self.__hora and self.__ultima_ejecucion != fecha_hoy:
                try:
                    self.ejecutar()
                except Exception:  # el hilo nunca debe morir: se avisa sin detalles internos
                    print("\n[ERROR] La rutina de las 08:00 falló; se reintentará mañana.")
                self.__ultima_ejecucion = fecha_hoy

            time.sleep(30)

    def ejecutar(self) -> dict:
        """ Consulta y guarda clima e indicadores. Retorna un resumen {clima, indicadores, errores} """
        resumen = {"clima": 0, "indicadores": 0, "errores": 0}
        monedas_consultadas: set[str] = set()

        for proyecto in self.__proyectos:
            ciudad = leer_dato(proyecto, "ciudad")
            moneda = leer_dato(proyecto, "moneda")
            id_proyecto = leer_dato(proyecto, "id_proyecto")

            if ciudad and id_proyecto:
                try:
                    dato_clima = self.__servicio_clima.obtener_clima(ciudad)
                    if self.__repositorio.guardar_clima(dato_clima, id_proyecto):
                        resumen["clima"] += 1
                except ErrorServicioExterno as e:
                    resumen["errores"] += 1
                    print(f"[WARNING] Clima de {ciudad}: {e.mensaje_seguro()}")
                except ValueError as e:
                    resumen["errores"] += 1
                    print(f"[WARNING] Clima de {ciudad}: {e}")

            codigo = str(moneda or "").strip().upper()
            if codigo and codigo not in monedas_consultadas:
                monedas_consultadas.add(codigo)
                try:
                    indicador = self.__servicio_indicadores.obtener_indicador(codigo)
                    if self.__repositorio.guardar_indicador(indicador):
                        resumen["indicadores"] += 1
                except ErrorServicioExterno as e:
                    resumen["errores"] += 1
                    print(f"[WARNING] Indicador {codigo}: {e.mensaje_seguro()}")
                except ValueError as e:
                    resumen["errores"] += 1
                    print(f"[WARNING] Indicador {codigo}: {e}")

        return resumen


"""
Código propuesto por la IA y DESCARTADO:

    ciudad = getattr(proyecto, "ciudad", None) or getattr(proyecto, "_Proyecto__ciudad", "")
    ...
    except (ErrorServicioExterno, ValueError):
        pass

Por qué se descartó:
  1. "_Proyecto__ciudad" lee un atributo privado saltándose el encapsulamiento, y con
     los diccionarios que entrega RepositorioProyecto.listar() no encontraba nada:
     la rutina no guardaba ningún dato y no avisaba.
  2. "pass" ocultaba los errores: si la API fallaba, nadie se enteraba. Ahora se
     muestra mensaje_seguro() y se cuenta el error en el resumen.
"""
