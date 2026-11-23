from __future__ import annotations
from typing import TYPE_CHECKING

from service.servicio_api import ErrorServicioExterno
from service.servicio_clima import ServicioClima
from service.servicio_indicadores import ServicioIndicadores

if TYPE_CHECKING:
    from database.repositorios import RepositorioDatoExterno

"""
REGISTRO DE USO DE IA:
- ¿Qué se solicitó?: Originalmente, TareaProgramada: ejecutar automáticamente a las 08:00 la
  consulta de clima e indicadores según los proyectos activos.
- ¿Qué generó la herramienta?: Un bucle infinito while True en el hilo principal con listas de
  ciudades y monedas escritas en duro y sin manejo de errores individuales.
- ¿Qué se adoptó?: La composición con ServicioClima, ServicioIndicadores y RepositorioDatoExterno,
  los errores aislados por ítem (una API caída no detiene a la otra) y el resumen de resultados.
- ¿Qué se modificó?: Cambio (23-11), a pedido del equipo: se eliminó la rutina de las 08:00.
  Ejecutándose en un computador local solo funcionaba si el programa estaba abierto justo a esa
  hora, así que la clase pasó a llamarse CargaInicial y se ejecuta una vez al iniciar main.py,
  antes del inicio de sesión. Carga las 10 ciudades de ServicioClima en una sola consulta y las
  monedas principales (USD, EUR, UF). Ya no usa hilos (threading) ni time.sleep().
- ¿Qué se descartó?: El hilo con la espera a las 08:00 (ver abajo).
- Justificación: El usuario siempre encuentra datos al entrar al menú de clima y monedas, sin
  depender de la hora a la que abra el programa.
"""


# Al iniciar el programa trae de internet el clima de las 10 ciudades y las monedas principales y los guarda en Oracle.
class CargaInicial:
    def __init__(
        self,
        clima: ServicioClima,
        indicadores: ServicioIndicadores,
        repositorio: RepositorioDatoExterno,
    ) -> None:
        self.__servicio_clima: ServicioClima = clima
        self.__servicio_indicadores: ServicioIndicadores = indicadores
        self.__repositorio: RepositorioDatoExterno = repositorio

    def ejecutar(self) -> dict:
        """ Consulta y guarda clima e indicadores. Retorna un resumen {clima, indicadores, errores} """
        resumen = {"clima": 0, "indicadores": 0, "errores": 0}

        # 1) Clima actual de las 10 ciudades (una sola llamada a Open-Meteo)
        try:
            for dato_clima in self.__servicio_clima.obtener_clima_ciudades():
                if self.__repositorio.guardar_clima(dato_clima):
                    resumen["clima"] += 1
        except ErrorServicioExterno as e:
            resumen["errores"] += 1
            print(f"[WARNING] Clima: {e.mensaje_seguro()}")
        except ValueError as e:
            resumen["errores"] += 1
            print(f"[WARNING] Clima: {e}")

        # 2) Monedas principales. consultar() es el método abstracto de ServicioAPI (polimorfismo)
        for codigo in ServicioIndicadores.PRINCIPALES:
            try:
                indicador = self.__servicio_indicadores.consultar(codigo)
                self.__repositorio.guardar_indicador(indicador)  # False = ya estaba guardado hoy
                resumen["indicadores"] += 1
            except ErrorServicioExterno as e:
                resumen["errores"] += 1
                print(f"[WARNING] {ServicioIndicadores.NOMBRES[codigo]}: {e.mensaje_seguro()}")
            except ValueError as e:
                resumen["errores"] += 1
                print(f"[WARNING] {ServicioIndicadores.NOMBRES[codigo]}: {e}")

        return resumen


"""
Código propuesto por la IA y DESCARTADO (versión anterior, TareaProgramada):

    def _bucle_planificador(self):
        while self.__activa:
            if datetime.now().strftime("%H:%M") == "08:00" and self.__ultima_ejecucion != hoy:
                self.ejecutar()
            time.sleep(30)

Por qué se descartó:
  1. En un computador local el programa casi nunca está abierto justo a las 08:00, así que
     la rutina no se ejecutaba y el menú de clima e indicadores aparecía vacío.
  2. El hilo imprimía mensajes en medio de los menús mientras el usuario escribía.
  3. Obligaba a compartir la conexión de Oracle entre dos hilos (con un candado).
"""
