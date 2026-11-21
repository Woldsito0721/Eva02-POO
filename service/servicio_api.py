from abc import ABC
import requests

"""
REGISTRO DE USO DE IA (Criterios 3.1.1 / 3.1.3 / 3.1.4):
- ¿Qué se solicitó?: Implementar la clase abstracta ServicioAPI y la excepción ErrorServicioExterno para centralizar las peticiones HTTP GET con requests.
- ¿Qué generó la herramienta?: Una función directa con requests.get() sin parámetro timeout, sin validación explícita de códigos HTTP y exponiendo el traceback de la librería al usuario.
- ¿Qué se adoptó?: El uso de la librería oficial requests y la encapsulación en una clase base abstracta (ABC) reutilizable.
- ¿Qué se modificó?: Se fijó timeout=10 por defecto, se implementó _validar_codigo() para gestionar estados 200/404/500 y se capturaron Timeout, ConnectionError y HTTPError transformándolos en ErrorServicioExterno.
- ¿Qué se descartó?: Imprimir excepciones crudas de requests que pudieran filtrar URLs con api_key o parámetros internos.
- Justificación: Garantiza la continuidad operativa del sistema ante fallos de red y protege información sensible en los mensajes de error.
"""


# Excepción que encapsula fallos de red o HTTP sin filtrar credenciales ni URLs internas.
class ErrorServicioExterno(Exception):
    def __init__(self, codigo_http: int = 0, detalle_interno: str = "Error en servicio externo.") -> None:
        super().__init__(detalle_interno)
        self.__codigo_http: int = codigo_http
        self.__detalle_interno: str = detalle_interno

    def get_codigo_http(self) -> int:
        return self.__codigo_http

    def mensaje_seguro(self) -> str:
        if self.__codigo_http == 404:
            return "Servicio externo: no se encontraron datos para el parámetro consultado (HTTP 404)."
        if self.__codigo_http in (401, 403):
            return "Servicio externo: error de autorización con el proveedor de datos."
        if self.__codigo_http >= 500:
            return "Servicio externo: el proveedor no se encuentra disponible temporalmente."
        return "Servicio externo: no fue posible completar la consulta por un problema de conexión o tiempo de espera."


# Clase base abstracta que centraliza las solicitudes HTTP GET, timeouts y validación de respuestas JSON.
class ServicioAPI(ABC):
    def __init__(self, url_base: str, timeout: int = 10, api_key: str = "") -> None:
        self._url_base: str = url_base.rstrip("/")
        self._timeout: int = timeout
        self.__api_key: str = api_key

    def _get_api_key(self) -> str:
        return self.__api_key

    def _validar_codigo(self, respuesta: requests.Response) -> None:
        if respuesta.status_code != 200:
            raise ErrorServicioExterno(
                codigo_http=respuesta.status_code,
                detalle_interno=f"Respuesta HTTP inesperada: {respuesta.status_code}",
            )

    def _get(self, endpoint: str, params: dict | None = None) -> dict:
        url = f"{self._url_base}/{endpoint.lstrip('/')}" if endpoint else self._url_base
        try:
            respuesta = requests.get(url, params=params, timeout=self._timeout)
            self._validar_codigo(respuesta)
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
        except requests.exceptions.HTTPError as exc:
            codigo = exc.response.status_code if exc.response is not None else 0
            raise ErrorServicioExterno(
                codigo_http=codigo,
                detalle_interno=f"Fallo HTTP {codigo} en solicitud GET.",
            ) from exc
        except ValueError as exc:
            raise ErrorServicioExterno(
                detalle_interno="La respuesta de la API externa no tiene un formato JSON válido."
            ) from exc