from model.dato_clima import DatoClima
from security.validador import Validador
from service.servicio_api import ServicioAPI, ErrorServicioExterno

"""
REGISTRO DE USO DE IA (Criterios 3.1.1 / 3.1.2 / 3.1.4):
- ¿Qué se solicitó?: Implementar ServicioClima heredando de ServicioAPI para consultar Open-Meteo y retornar un objeto DatoClima.
- ¿Qué generó la herramienta?: Consulta directa sin validar el nombre de la ciudad y acceso con corchetes rígidos (data["current"]["temperature_2m"]) que lanzaban KeyError si la ciudad no existía.
- ¿Qué se adoptó?: La herencia de ServicioAPI reutilizando _obtener_json() y la traducción de códigos meteorológicos WMO a texto legible.
- ¿Qué se modificó?: Se integró Validador.validar_ciudad() antes de hacer solicitudes HTTP, se resolvió geocodificación por nombre de ciudad y se usó .get() defensivo para validar la presencia de datos.
- ¿Qué se descartó?: Coordenadas fijas en duro (hardcoded) para una sola ciudad.
- Justificación: Permite consultar el clima de cualquier ciudad donde EcoTech ejecute proyectos sin romper el sistema ante ciudades inexistentes.
"""


# Consulta condiciones meteorológicas actuales por ciudad en Open-Meteo y construye objetos DatoClima.
class ServicioClima(ServicioAPI):
    __URL_GEOCODING = "https://geocoding-api.open-meteo.com/v1"
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
        61: "Lluvia ligera",
        63: "Lluvia moderada",
        65: "Lluvia intensa",
        71: "Nieve ligera",
        80: "Chubascos ligeros",
        81: "Chubascos moderados",
        95: "Tormenta eléctrica",
    }

    def __init__(self) -> None:
        super().__init__(url_base="https://api.open-meteo.com/v1", tiempo_espera=10)

    def _obtener_coordenadas(self, ciudad: str) -> tuple[float, float, str]:
        # La geocodificación usa otra URL base: se pasa como parámetro en vez de
        # cambiar self._url_base, que comparten el menú y la rutina de las 08:00
        datos_geo = self._obtener_json(
            "search",
            parametros={"name": ciudad, "count": 1, "language": "es"},
            url_base=self.__URL_GEOCODING,
        )

        resultados = datos_geo.get("results")
        if not resultados or not isinstance(resultados, list):
            raise ErrorServicioExterno(
                codigo_http=404,
                detalle_interno=f"No se encontraron coordenadas para la ciudad: {ciudad}",
            )

        lugar = resultados[0]
        latitud = lugar.get("latitude")
        longitud = lugar.get("longitude")
        nombre_oficial = lugar.get("name", ciudad)

        if latitud is None or longitud is None:
            raise ErrorServicioExterno(
                detalle_interno="Respuesta de geocodificación incompleta."
            )
        return float(latitud), float(longitud), str(nombre_oficial)

    def consultar(self, parametro: str) -> DatoClima:
        return self.obtener_clima(parametro)

    def obtener_clima(self, ciudad: str) -> DatoClima:
        ciudad_limpia = Validador.sanitizar(ciudad)
        if not Validador.validar_ciudad(ciudad_limpia):
            raise ValueError("Nombre de ciudad inválido para consulta climática.")

        lat, lon, nombre_ciudad = self._obtener_coordenadas(ciudad_limpia)
        datos = self._obtener_json(
            "forecast",
            parametros={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,relative_humidity_2m,weather_code",
            },
        )

        actual = datos.get("current")
        if not isinstance(actual, dict):
            raise ErrorServicioExterno(
                detalle_interno="El JSON de Open-Meteo no contiene el bloque 'current'."
            )

        temperatura = actual.get("temperature_2m")
        humedad = actual.get("relative_humidity_2m")
        codigo_wmo = actual.get("weather_code")

        if temperatura is None or humedad is None:
            raise ErrorServicioExterno(
                detalle_interno="Faltan campos de temperatura o humedad en la respuesta climática."
            )

        estado = self.__CODIGOS_WMO.get(int(codigo_wmo or 0), "Condición variable")
        return DatoClima(
            ciudad=nombre_ciudad,
            temperatura=float(temperatura),
            humedad=int(humedad),
            estado=estado,
        )

"""
Código propuesto por la IA y DESCARTADO:

    def _obtener_coordenadas(self, ciudad):
        url_original = self._url_base
        try:
            self._url_base = self.__URL_GEOCODING
            datos_geo = self._consultar("search", parametros={...})
        finally:
            self._url_base = url_original

Por qué se descartó: cambiaba temporalmente un atributo del objeto. Si la rutina de
las 08:00 (otro hilo) consultaba el clima en ese mismo instante, usaría la URL
equivocada. Pasar url_base como parámetro no modifica el estado compartido.
"""
