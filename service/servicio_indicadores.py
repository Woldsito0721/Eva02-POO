from datetime import date, datetime
from model.indicador_economico import IndicadorEconomico
from security.validador import Validador
from service.servicio_api import ServicioAPI, ErrorServicioExterno

"""
REGISTRO DE USO DE IA (Criterios 3.1.1 / 3.1.2 / 3.1.4):
- ¿Qué se solicitó?: Implementar ServicioIndicadores heredando de ServicioAPI para consultar indicadores económicos en mindicador.cl.
- ¿Qué generó la herramienta?: Solicitud directa concatenando el código ingresado a la URL y acceso sin validar a serie[0]["valor"].
- ¿Qué se adoptó?: La herencia de ServicioAPI utilizando el método protegido _get() y el parseo JSON de mindicador.cl.
- ¿Qué se modificó?: Se validó el código ISO de 3 letras con Validador.validar_codigo_moneda(), se mapeó USD/EUR/CLF a los endpoints oficiales de mindicador.cl y se manejó CLP como moneda base (valor 1.0).
- ¿Qué se descartó?: Concatenación de entrada de usuario sin validar en la URL de la petición.
- Justificación: Garantiza compatibilidad entre los códigos ISO de los proyectos y la API económica chilena, evitando errores de formato o inyección de rutas.
"""


# Consulta valores de divisas e indicadores económicos en mindicador.cl y retorna IndicadorEconomico.
class ServicioIndicadores(ServicioAPI):
    __MAPA_MONEDAS = {
        "USD": "dolar",
        "EUR": "euro",
        "CLF": "uf",
    }

    def __init__(self) -> None:
        super().__init__(url_base="https://mindicador.cl/api", timeout=10)

    def obtener_indicador(self, codigo: str) -> IndicadorEconomico:
        codigo_limpio = Validador.sanitizar(codigo).upper()
        if not Validador.validar_codigo_moneda(codigo_limpio):
            raise ValueError("Código de moneda inválido. Debe ser un código ISO de 3 letras (ej. USD, EUR, CLP).")

        if codigo_limpio == "CLP":
            return IndicadorEconomico(codigo="CLP", valor=1.0, fecha=date.today())

        endpoint = self.__MAPA_MONEDAS.get(codigo_limpio)
        if not endpoint:
            raise ErrorServicioExterno(
                codigo_http=404,
                detalle_interno=f"Moneda '{codigo_limpio}' no soportada por el proveedor de indicadores.",
            )

        datos = self._get(endpoint)
        serie = datos.get("serie")
        if not serie or not isinstance(serie, list):
            raise ErrorServicioExterno(
                detalle_interno=f"No se encontraron valores históricos para el indicador {codigo_limpio}."
            )

        ultimo = serie[0]
        valor = ultimo.get("valor")
        fecha_raw = ultimo.get("fecha")

        if valor is None:
            raise ErrorServicioExterno(
                detalle_interno="El registro del indicador económico no contiene valor numérico."
            )

        try:
            fecha_ind = (
                datetime.fromisoformat(str(fecha_raw).replace("Z", "+00:00")).date()
                if fecha_raw
                else date.today()
            )
        except ValueError:
            fecha_ind = date.today()

        return IndicadorEconomico(
            codigo=codigo_limpio,
            valor=float(valor),
            fecha=fecha_ind,
        )