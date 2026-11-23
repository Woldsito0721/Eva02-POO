from abc import ABC, abstractmethod
import requests

"""
REGISTRO DE USO DE IA (Criterios 3.1.1 / 3.1.3 / 3.1.4):
- ¿Qué se solicitó?: Implementar la clase abstracta ServicioAPI y la excepción ErrorServicioExterno para centralizar las peticiones HTTP GET con requests.
- ¿Qué generó la herramienta?: Una función directa con requests.get() sin parámetro timeout, sin validación explícita de códigos HTTP y exponiendo el traceback de la librería al usuario.
- ¿Qué se adoptó?: El uso de la librería oficial requests y la encapsulación en una clase base abstracta (ABC) reutilizable.
- ¿Qué se modificó?: Se fijó un tiempo de espera de 10 s, se implementó _validar_codigo() para gestionar estados 200/404/500 y se capturaron Timeout, ConnectionError y el resto de RequestException transformándolos en ErrorServicioExterno.
  Tras la auditoría: se agregó el método abstracto consultar() (sin él, ServicioAPI se podía instanciar), se tradujeron los nombres al español (_obtener_json, ruta, parametros, tiempo_espera), se quitó api_key porque Open-Meteo y mindicador.cl no la usan, y _obtener_json acepta una url_base opcional para no modificar atributos compartidos entre hilos.
  Cambio (23-11): _obtener_json() reintenta una vez cuando la API tarda, se cae la conexión
  o responde 5xx (mindicador.cl respondía de forma intermitente en las pruebas); un 429
  (demasiadas solicitudes) o un 404 no se reintentan porque insistir no lo arregla.
- ¿Qué se descartó?: Imprimir excepciones crudas de requests que pudieran filtrar URLs o parámetros internos.
- Justificación: Garantiza la continuidad operativa del sistema ante fallos de red y protege información sensible en los mensajes de error.
"""


# Excepción que encapsula fallos de red o HTTP sin filtrar credenciales ni URLs internas.
class ErrorServicioExterno(Exception):
    def __init__(self, codigo_http: int = 0, detalle_interno: str = "Error en servicio externo.") -> None:
        super().__init__(detalle_interno)
        self.__codigo_http: int = codigo_http
        self.__detalle_interno: str = detalle_interno

    def obtener_codigo_http(self) -> int:
        return self.__codigo_http

    def mensaje_seguro(self) -> str:
        if self.__codigo_http == 404:
            return "Servicio externo: no se encontraron datos para el parámetro consultado (HTTP 404)."
        if self.__codigo_http in (401, 403):
            return "Servicio externo: error de autorización con el proveedor de datos."
        if self.__codigo_http == 429:
            return "Servicio externo: se alcanzó el límite de consultas del proveedor; intente más tarde."
        if self.__codigo_http >= 500:
            return "Servicio externo: el proveedor no se encuentra disponible temporalmente."
        return "Servicio externo: no fue posible completar la consulta por un problema de conexión o tiempo de espera."


# Clase base abstracta que centraliza las solicitudes HTTP GET, tiempos de espera y validación de respuestas JSON.
class ServicioAPI(ABC):
    def __init__(self, url_base: str, tiempo_espera: int = 10) -> None:
        self._url_base: str = url_base.rstrip("/")
        self._tiempo_espera: int = tiempo_espera

    @abstractmethod
    def consultar(self, parametro: str):
        """ Cada servicio define su consulta principal (clima por ciudad, indicador por moneda) """

    def _validar_codigo(self, respuesta: requests.Response) -> None:
        if respuesta.status_code != 200:
            raise ErrorServicioExterno(
                codigo_http=respuesta.status_code,
                detalle_interno=f"Respuesta HTTP inesperada: {respuesta.status_code}",
            )

    def _obtener_json(self, ruta: str, parametros: dict | None = None, url_base: str | None = None,
                      reintentos: int = 1):
        """
        GET que retorna el JSON (dict o list). Si falla por tiempo de espera, conexión o un
        error 5xx del proveedor, se reintenta 'reintentos' veces antes de rendirse.
        """
        base = (url_base or self._url_base).rstrip("/")
        url = f"{base}/{ruta.lstrip('/')}" if ruta else base
        for intento in range(reintentos + 1):
            try:
                return self.__solicitar(url, parametros)
            except ErrorServicioExterno as error:
                codigo = error.obtener_codigo_http()
                reintentable = codigo == 0 or codigo >= 500  # 0 = red / tiempo de espera
                if not reintentable or intento == reintentos:
                    raise

    def __solicitar(self, url: str, parametros: dict | None):
        try:
            respuesta = requests.get(url, params=parametros, timeout=self._tiempo_espera)
            self._validar_codigo(respuesta)  # cualquier código distinto de 200 → ErrorServicioExterno
            return respuesta.json()
        except ErrorServicioExterno:
            raise
        except requests.exceptions.Timeout as exc:
            raise ErrorServicioExterno(
                detalle_interno="Tiempo de espera agotado al consultar la API externa."
            ) from exc
        except requests.exceptions.ConnectionError as exc:
            raise ErrorServicioExterno(
                detalle_interno="Error de conectividad de red con la API externa."
            ) from exc
        except requests.exceptions.RequestException as exc:  # SSLError, TooManyRedirects, etc.
            raise ErrorServicioExterno(
                detalle_interno="Fallo inesperado en la solicitud HTTP."
            ) from exc
        except ValueError as exc:
            raise ErrorServicioExterno(
                detalle_interno="La respuesta de la API externa no tiene un formato JSON válido."
            ) from exc


"""
Código propuesto por la IA y DESCARTADO:

        except requests.exceptions.HTTPError as exc:
            codigo = exc.response.status_code if exc.response is not None else 0
            raise ErrorServicioExterno(codigo_http=codigo, ...) from exc

Por qué se descartó: requests.get() nunca lanza HTTPError por sí solo (solo lo hace
raise_for_status(), que no se usa); los códigos 404/500 ya los detecta
_validar_codigo(). Ese bloque era código inalcanzable. Se reemplazó por
RequestException, que sí cubre errores reales no previstos (SSL, redirecciones).
"""
