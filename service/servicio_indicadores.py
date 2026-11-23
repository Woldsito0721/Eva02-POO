from datetime import date, datetime, timedelta
from model.indicador_economico import IndicadorEconomico
from security.validador import Validador
from service.servicio_api import ServicioAPI, ErrorServicioExterno

"""
REGISTRO DE USO DE IA (Criterios 3.1.1 / 3.1.2 / 3.1.4):
- ¿Qué se solicitó?: Implementar ServicioIndicadores heredando de ServicioAPI para consultar indicadores económicos en mindicador.cl.
- ¿Qué generó la herramienta?: Solicitud directa concatenando el código ingresado a la URL y acceso sin validar a serie[0]["valor"].
- ¿Qué se adoptó?: La herencia de ServicioAPI utilizando el método protegido _obtener_json() y el parseo JSON de mindicador.cl.
- ¿Qué se modificó?: Se validó el código ISO de 3 letras con Validador.validar_codigo_moneda(), se mapeó USD/EUR a los endpoints oficiales de mindicador.cl y se manejó CLP como moneda base (valor 1.0).
  Cambio (23-11): en las pruebas mindicador.cl dejó de responder (ni con 60 s de espera) y la
  consulta de monedas no mostraba nada. Se agregó una fuente de respaldo sin llave
  (open.er-api.com) para USD y EUR; la espera de mindicador bajó a 5 s y, si falla, no se le
  vuelve a consultar por 10 minutos para que el menú no quede esperando en cada consulta.
  Si ninguna fuente responde, main.py muestra el último valor guardado en Oracle.
  Se quitó la UF (CLF), a pedido del equipo: solo la publica mindicador.cl, que no
  respondía, y no tiene fuente de respaldo.
- ¿Qué se descartó?: Concatenación de entrada de usuario sin validar en la URL de la petición.
- Justificación: Garantiza compatibilidad entre los códigos ISO de los proyectos y la API económica chilena, evitando errores de formato o inyección de rutas.
"""


# Consulta valores de divisas e indicadores económicos y retorna IndicadorEconomico.
class ServicioIndicadores(ServicioAPI):
    # Monedas que muestra el menú y que se cargan al iniciar el programa
    PRINCIPALES = ("USD", "EUR")
    NOMBRES = {"USD": "Dólar", "EUR": "Euro"}

    __MAPA_MONEDAS = {
        "USD": "dolar",
        "EUR": "euro",
    }
    __URL_RESPALDO = "https://open.er-api.com/v6"
    __MINUTOS_PAUSA = 10

    def __init__(self) -> None:
        super().__init__(url_base="https://mindicador.cl/api", tiempo_espera=5)
        self.__principal_caida_hasta: datetime | None = None

    def consultar(self, parametro: str) -> IndicadorEconomico:
        return self.obtener_indicador(parametro)

    def obtener_indicador(self, codigo: str) -> IndicadorEconomico:
        codigo_limpio = Validador.sanitizar(codigo).upper()
        if not Validador.validar_codigo_moneda(codigo_limpio):
            raise ValueError("Código de moneda inválido. Debe ser un código ISO de 3 letras (ej. USD, EUR, CLP).")

        if codigo_limpio == "CLP":
            return IndicadorEconomico(codigo="CLP", valor=1.0, fecha=date.today())

        ruta = self.__MAPA_MONEDAS.get(codigo_limpio)
        if not ruta:
            raise ErrorServicioExterno(
                codigo_http=404,
                detalle_interno=f"Moneda '{codigo_limpio}' no soportada por el proveedor de indicadores.",
            )

        try:
            return self.__desde_mindicador(codigo_limpio, ruta)
        except ErrorServicioExterno:
            return self.__desde_respaldo(codigo_limpio)

    # --- Fuente principal: mindicador.cl ---
    def __desde_mindicador(self, codigo: str, ruta: str) -> IndicadorEconomico:
        if self.__principal_caida_hasta and datetime.now() < self.__principal_caida_hasta:
            raise ErrorServicioExterno(detalle_interno="mindicador.cl en pausa tras un fallo reciente.")
        try:
            # Sin reintento: si mindicador no responde se pasa de inmediato al respaldo
            datos = self._obtener_json(ruta, reintentos=0)
        except ErrorServicioExterno:
            self.__principal_caida_hasta = datetime.now() + timedelta(minutes=self.__MINUTOS_PAUSA)
            raise
        self.__principal_caida_hasta = None

        serie = datos.get("serie") if isinstance(datos, dict) else None
        if not serie or not isinstance(serie, list):
            raise ErrorServicioExterno(
                detalle_interno=f"No se encontraron valores históricos para el indicador {codigo}."
            )

        ultimo = serie[0]
        valor = ultimo.get("valor")
        fecha_texto = ultimo.get("fecha")

        if valor is None:
            raise ErrorServicioExterno(
                detalle_interno="El registro del indicador económico no contiene valor numérico."
            )

        try:
            fecha_ind = (
                datetime.fromisoformat(str(fecha_texto).replace("Z", "+00:00")).date()
                if fecha_texto
                else date.today()
            )
        except ValueError:
            fecha_ind = date.today()

        return IndicadorEconomico(codigo=codigo, valor=float(valor), fecha=fecha_ind)

    # --- Fuente de respaldo: open.er-api.com (USD y EUR) ---
    def __desde_respaldo(self, codigo: str) -> IndicadorEconomico:
        # Tasas de 1 USD en cada moneda: 1 USD = CLP pesos; 1 EUR = CLP / EUR pesos
        datos = self._obtener_json("latest/USD", url_base=self.__URL_RESPALDO)
        if not isinstance(datos, dict) or datos.get("result") != "success" or not isinstance(datos.get("rates"), dict):
            raise ErrorServicioExterno(detalle_interno="La fuente de respaldo no entregó tasas de cambio.")
        tasas = datos["rates"]

        pesos_por_dolar = tasas.get("CLP")
        euros_por_dolar = tasas.get("EUR")
        if not pesos_por_dolar or (codigo == "EUR" and not euros_por_dolar):
            raise ErrorServicioExterno(detalle_interno="La fuente de respaldo no trae CLP o EUR.")

        valor = pesos_por_dolar if codigo == "USD" else pesos_por_dolar / euros_por_dolar
        try:
            fecha = datetime.fromtimestamp(int(datos.get("time_last_update_unix"))).date()
        except (TypeError, ValueError):
            fecha = date.today()
        return IndicadorEconomico(codigo=codigo, valor=round(float(valor), 2), fecha=fecha)


"""
Código propuesto por la IA y DESCARTADO:

    def obtener_indicador(self, codigo):
        datos = self._consultar(codigo.lower())
        return IndicadorEconomico(codigo, datos["serie"][0]["valor"], date.today())

Por qué se descartó:
  1. Concatena lo que escribe el usuario directamente en la URL (inyección de rutas).
  2. mindicador.cl no usa códigos ISO: USD es "dolar" y EUR es "euro", por lo que
     "usd" daría 404.
  3. datos["serie"][0] lanza KeyError/IndexError si la API cambia o viene vacía.
  4. Usaba la fecha de hoy en vez de la fecha real del valor publicado.

    # Primera idea para el respaldo: reintentar mindicador.cl 3 veces con 10 s cada una
Por qué se descartó: cuando mindicador.cl no responde, el usuario esperaba hasta 30 s por
moneda (90 s al iniciar el programa) para terminar igual sin datos. Es mejor esperar poco
y usar otra fuente.
"""
