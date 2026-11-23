from datetime import datetime

from model.dato_clima import DatoClima
from security.validador import Validador
from service.servicio_api import ServicioAPI, ErrorServicioExterno

"""
REGISTRO DE USO DE IA (Criterios 3.1.1 / 3.1.2 / 3.1.4):
- ¿Qué se solicitó?: Implementar ServicioClima heredando de ServicioAPI para consultar Open-Meteo y retornar un objeto DatoClima.
- ¿Qué generó la herramienta?: Consulta directa sin validar el nombre de la ciudad y acceso con corchetes rígidos (data["current"]["temperature_2m"]) que lanzaban KeyError si la ciudad no existía.
- ¿Qué se adoptó?: La herencia de ServicioAPI reutilizando _obtener_json() y la traducción de códigos meteorológicos WMO a texto legible.
- ¿Qué se modificó?: Se usó .get() defensivo para validar la presencia de datos.
  Cambio (23-11): el clima se consulta para 10 ciudades fijas de Chile (lista blanca con
  sus coordenadas) en vez de geocodificar texto libre: la API de geocodificación respondía
  HTTP 429 (límite de consultas) y una lista cerrada impide enviar cualquier texto a la URL.
  Se agregó el pronóstico hora por hora del día (en la hora local de la ciudad), una sola
  consulta para las 10 ciudades al iniciar el programa, y la tabla WMO completa: antes los
  códigos 96 y 99 (tormenta con granizo) no estaban y el sistema los marcaba como "apto".
- ¿Qué se descartó?: La geocodificación por nombre (ver abajo).
- Justificación: Menos llamadas a la API (1 en vez de 2 por ciudad), sin dependencia de un
  segundo servicio y solo con ciudades válidas.
"""


# Consulta el clima actual y el pronóstico por hora de 10 ciudades de Chile en Open-Meteo.
class ServicioClima(ServicioAPI):
    # Ciudades disponibles (norte a sur) con su latitud y longitud
    CIUDADES = {
        "Arica": (-18.4783, -70.3126),
        "Antofagasta": (-23.6509, -70.3975),
        "La Serena": (-29.9027, -71.2519),
        "Valparaíso": (-33.0472, -71.6127),
        "Santiago": (-33.4489, -70.6693),
        "Concepción": (-36.8270, -73.0503),
        "Temuco": (-38.7359, -72.5904),
        "Valdivia": (-39.8142, -73.2459),
        "Puerto Montt": (-41.4693, -72.9424),
        "Punta Arenas": (-53.1638, -70.9171),
    }
    __VARIABLES = "temperature_2m,relative_humidity_2m,weather_code"
    __CODIGOS_WMO = {
        0: "Despejado",
        1: "Mayormente despejado",
        2: "Parcialmente nublado",
        3: "Nublado",
        45: "Niebla",
        48: "Niebla con escarcha",
        51: "Llovizna ligera",
        53: "Llovizna moderada",
        55: "Llovizna intensa",
        56: "Llovizna helada ligera",
        57: "Llovizna helada intensa",
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        65: "Lluvia intensa",
        66: "Lluvia helada ligera",
        67: "Lluvia helada intensa",
        71: "Nieve ligera",
        73: "Nieve moderada",
        75: "Nieve intensa",
        77: "Granos de nieve",
        80: "Chubascos ligeros",
        81: "Chubascos moderados",
        82: "Chubascos violentos",
        85: "Chubascos de nieve ligeros",
        86: "Chubascos de nieve intensos",
        95: "Tormenta eléctrica",
        96: "Tormenta con granizo ligero",
        99: "Tormenta con granizo fuerte",
    }

    def __init__(self) -> None:
        super().__init__(url_base="https://api.open-meteo.com/v1", tiempo_espera=10)

    # --- Apoyo interno ---
    def _coordenadas(self, ciudad: str) -> tuple[float, float]:
        """ Solo se aceptan las 10 ciudades de la lista (lista blanca) """
        ciudad_limpia = Validador.sanitizar(ciudad)
        if ciudad_limpia not in self.CIUDADES:
            raise ValueError("Ciudad no disponible para la consulta de clima.")
        return self.CIUDADES[ciudad_limpia]

    def _estado(self, codigo_wmo) -> str:
        if codigo_wmo is None:
            return "Condición desconocida"
        return self.__CODIGOS_WMO.get(int(codigo_wmo), "Condición desconocida")

    def _dato_actual(self, ciudad: str, datos: dict) -> DatoClima:
        """ Arma el DatoClima con el bloque 'current' de la respuesta """
        actual = datos.get("current") if isinstance(datos, dict) else None
        if not isinstance(actual, dict):
            raise ErrorServicioExterno(detalle_interno="El JSON de Open-Meteo no contiene el bloque 'current'.")

        temperatura = actual.get("temperature_2m")
        humedad = actual.get("relative_humidity_2m")
        if temperatura is None or humedad is None:
            raise ErrorServicioExterno(detalle_interno="Faltan campos de temperatura o humedad en la respuesta climática.")

        return DatoClima(
            ciudad=ciudad,
            temperatura=float(temperatura),
            humedad=int(humedad),
            estado=self._estado(actual.get("weather_code")),
            fecha_consulta=self._leer_hora(actual.get("time")),
        )

    @staticmethod
    def _leer_hora(texto) -> datetime:
        """ Open-Meteo entrega la hora local de la ciudad como '2026-11-23T15:15' """
        try:
            return datetime.fromisoformat(str(texto))
        except ValueError:
            return datetime.now()

    # --- Consultas ---
    def consultar(self, parametro: str) -> DatoClima:
        return self.obtener_clima(parametro)

    def obtener_clima(self, ciudad: str) -> DatoClima:
        """ Clima actual de una de las 10 ciudades """
        latitud, longitud = self._coordenadas(ciudad)
        datos = self._obtener_json("forecast", parametros={
            "latitude": latitud, "longitude": longitud,
            "current": self.__VARIABLES, "timezone": "auto",
        })
        return self._dato_actual(Validador.sanitizar(ciudad), datos)

    def obtener_pronostico(self, ciudad: str) -> tuple[DatoClima, list[DatoClima]]:
        """
        Clima de AHORA y pronóstico de las horas que quedan del día, según la hora
        local de la ciudad en el momento de la consulta. Una sola llamada a la API.
        """
        latitud, longitud = self._coordenadas(ciudad)
        nombre = Validador.sanitizar(ciudad)
        datos = self._obtener_json("forecast", parametros={
            "latitude": latitud, "longitude": longitud,
            "current": self.__VARIABLES,
            "hourly": self.__VARIABLES + ",precipitation_probability",
            "forecast_days": 1, "timezone": "auto",
        })
        actual = self._dato_actual(nombre, datos)

        por_hora = datos.get("hourly")
        if not isinstance(por_hora, dict) or not isinstance(por_hora.get("time"), list):
            raise ErrorServicioExterno(detalle_interno="El JSON de Open-Meteo no contiene el bloque 'hourly'.")

        def columna(nombre_columna):
            valores = por_hora.get(nombre_columna)
            return valores if isinstance(valores, list) else [None] * len(por_hora["time"])

        hora_actual = actual.fecha_consulta.replace(minute=0, second=0, microsecond=0)
        siguientes = []
        for hora, temperatura, humedad, codigo, lluvia in zip(
                por_hora["time"], columna("temperature_2m"), columna("relative_humidity_2m"),
                columna("weather_code"), columna("precipitation_probability")):
            momento = self._leer_hora(hora)
            if momento <= hora_actual or temperatura is None:
                continue  # solo las horas que vienen después de la hora actual
            siguientes.append(DatoClima(
                ciudad=nombre,
                temperatura=float(temperatura),
                humedad=int(humedad) if humedad is not None else None,
                estado=self._estado(codigo),
                fecha_consulta=momento,
                probabilidad_lluvia=int(lluvia) if lluvia is not None else None,
            ))
        return actual, siguientes

    def obtener_clima_ciudades(self) -> list[DatoClima]:
        """ Clima actual de las 10 ciudades en UNA sola consulta (Open-Meteo acepta varias coordenadas) """
        nombres = list(self.CIUDADES)
        datos = self._obtener_json("forecast", parametros={
            "latitude": ",".join(str(self.CIUDADES[n][0]) for n in nombres),
            "longitude": ",".join(str(self.CIUDADES[n][1]) for n in nombres),
            "current": self.__VARIABLES, "timezone": "auto",
        })
        # Con varias coordenadas la API responde una lista, en el mismo orden
        if not isinstance(datos, list) or len(datos) != len(nombres):
            raise ErrorServicioExterno(detalle_interno="Respuesta inesperada al consultar varias ciudades.")
        return [self._dato_actual(nombre, dato) for nombre, dato in zip(nombres, datos)]


"""
Código propuesto por la IA y DESCARTADO:

    def _obtener_coordenadas(self, ciudad: str):
        datos_geo = self._obtener_json("search", parametros={"name": ciudad, "count": 1},
                                       url_base="https://geocoding-api.open-meteo.com/v1")
        lugar = datos_geo["results"][0]
        return lugar["latitude"], lugar["longitude"]

Por qué se descartó:
  1. Cada consulta de clima hacía 2 llamadas (geocodificar + pronóstico); en las pruebas la
     API de geocodificación respondió HTTP 429 (demasiadas solicitudes) y el clima fallaba.
  2. Aceptaba cualquier texto y lo enviaba a la URL; con 10 ciudades fijas el usuario elige
     un número del 1 al 10 y nunca se envía texto escrito por él.
  3. Un nombre ambiguo (ej. "Concepción", que existe en varios países) podía devolver otra
     ciudad; las coordenadas fijas siempre son las de Chile.
"""
