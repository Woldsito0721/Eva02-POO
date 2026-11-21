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
- ¿Qué se descartó?: El bloqueo del hilo principal y el uso de ciudades o monedas estáticas.
- Justificación: Garantiza la continuidad operativa del menú interactivo y permite escalar automáticamente al registrar nuevos proyectos internacionales.
"""


# Automatiza a las 08:00 horas la recolección de clima y divisas de los proyectos activos y los persiste en BD.
class TareaProgramada:
    def __init__(
        self,
        clima: ServicioClima,
        indicadores: ServicioIndicadores,
        repo: RepositorioDatoExterno,
    ) -> None:
        self.__hora: str = "08:00"
        self.__servicio_clima: ServicioClima = clima
        self.__servicio_indicadores: ServicioIndicadores = indicadores
        self.__repositorio: RepositorioDatoExterno = repo
        self.__proyectos: list[Proyecto] = []
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
                self.ejecutar()
                self.__ultima_ejecucion = fecha_hoy

            time.sleep(30)

    def ejecutar(self) -> None:
        monedas_consultadas: set[str] = set()

        for proyecto in self.__proyectos:
            ciudad = getattr(proyecto, "ciudad", None) or getattr(
                proyecto, "_Proyecto__ciudad", ""
            )
            moneda = getattr(proyecto, "moneda", None) or getattr(
                proyecto, "_Proyecto__moneda", ""
            )
            id_proyecto = getattr(proyecto, "id_proyecto", None) or getattr(
                proyecto, "_Proyecto__id_proyecto", None
            )

            if ciudad:
                try:
                    dato_clima = self.__servicio_clima.obtener_clima(ciudad)
                    if hasattr(self.__repositorio, "guardar_clima"):
                        self.__repositorio.guardar_clima(dato_clima, id_proyecto)
                except (ErrorServicioExterno, ValueError):
                    pass

            if moneda:
                codigo = str(moneda).strip().upper()
                if codigo and codigo not in monedas_consultadas:
                    monedas_consultadas.add(codigo)
                    try:
                        indicador = self.__servicio_indicadores.obtener_indicador(codigo)
                        if hasattr(self.__repositorio, "guardar_indicador_si_no_existe"):
                            self.__repositorio.guardar_indicador_si_no_existe(indicador)
                        elif hasattr(self.__repositorio, "guardar_indicador"):
                            self.__repositorio.guardar_indicador(indicador)
                    except (ErrorServicioExterno, ValueError):
                        pass