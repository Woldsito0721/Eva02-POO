# Python
from datetime import datetime


class DatoClima():
    """ Lectura de clima de una ciudad en una hora (la crea ServicioClima) """

    # Umbrales para decidir si se puede trabajar en terreno
    TEMPERATURA_MINIMA = 0.0
    TEMPERATURA_MAXIMA = 35.0
    # "desconocida": si la API entrega un código que no se conoce, por seguridad no es apto
    PALABRAS_NO_APTAS = ("tormenta", "granizo", "nieve", "helada", "fuerte", "intensa",
                         "intensos", "violento", "desconocida")

    def __init__(self, ciudad: str, temperatura: float, humedad: int, estado: str,
                 fecha_consulta: datetime = None, id_clima: int = None, id_proyecto: int = None,
                 probabilidad_lluvia: int = None):
        if not isinstance(ciudad, str) or not ciudad.strip():
            raise ValueError("La ciudad no puede estar vacía")
        if humedad is not None and not 0 <= humedad <= 100:
            raise ValueError("La humedad debe estar entre 0 y 100")
        if probabilidad_lluvia is not None and not 0 <= probabilidad_lluvia <= 100:
            raise ValueError("La probabilidad de lluvia debe estar entre 0 y 100")

        self.__id_clima = id_clima
        self.__id_proyecto = id_proyecto  # FK opcional a PROYECTO (None = consulta por ciudad)
        self.__ciudad = ciudad.strip()
        self.__temperatura = temperatura
        self.__humedad = humedad
        self.__estado = estado
        self.__fecha_consulta = fecha_consulta or datetime.now()
        self.__probabilidad_lluvia = probabilidad_lluvia  # solo pronóstico por hora (no se guarda en BD)

    @property
    def id_clima(self):
        return self.__id_clima

    @property
    def id_proyecto(self):
        return self.__id_proyecto

    @property
    def ciudad(self):
        return self.__ciudad

    @property
    def temperatura(self):
        return self.__temperatura

    @property
    def humedad(self):
        return self.__humedad

    @property
    def estado(self):
        return self.__estado

    @property
    def fecha_consulta(self):
        return self.__fecha_consulta

    @property
    def probabilidad_lluvia(self):
        return self.__probabilidad_lluvia

    def es_apto_para_trabajo(self) -> bool:
        """ Planificación operativa: temperatura en rango y sin fenómenos fuertes """
        if self.__temperatura is not None and not (
                self.TEMPERATURA_MINIMA <= self.__temperatura <= self.TEMPERATURA_MAXIMA):
            return False

        estado = (self.__estado or "").lower()
        return not any(palabra in estado for palabra in self.PALABRAS_NO_APTAS)

    def __str__(self):
        apto = "apto" if self.es_apto_para_trabajo() else "NO apto"
        return f"{self.__ciudad}: {self.__temperatura} °C, {self.__humedad}% humedad, {self.__estado} ({apto})"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: DatoClima con los campos que entrega ServicioClima
  (ciudad, temperatura, humedad, estado) y es_apto_para_trabajo().
- ¿Qué se adoptó?: Los nombres del constructor coinciden con cómo lo crea
  ServicioClima (ciudad=, temperatura=, humedad=, estado=) y se exponen con
  @property porque así los lee RepositorioDatoExterno.
- ¿Qué se modificó?: Los umbrales quedaron como constantes de clase para poder
  ajustarlos sin tocar la lógica; la humedad se valida igual que el CHECK de Oracle.
- ¿Qué se descartó?: Decidir "apto" solo por la temperatura (ver abajo).
- Cambio (23-11): el clima ahora se consulta por ciudad (10 ciudades de Chile), así que
  id_proyecto pasó a ser opcional, y se agregó probabilidad_lluvia para la tabla de
  pronóstico por hora que muestra el menú (no se guarda en Oracle).

Código propuesto por la IA y DESCARTADO:

    def es_apto_para_trabajo(self):
        return 5 < self.temperatura < 30

Por qué se descartó: con 15 °C y "Tormenta eléctrica" diría que es apto. Open-Meteo
entrega el estado en texto (ServicioClima lo traduce), así que se revisa también.
"""
