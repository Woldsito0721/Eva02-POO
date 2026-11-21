"""
Prueba de los servicios externos (APIs) y de la rutina de las 08:00.
Ejecutar desde la raíz del proyecto:  python -m test.prueba_servicios

Necesita internet (Open-Meteo y mindicador.cl). No usa la base de datos: la
rutina se prueba con un repositorio de prueba que guarda en memoria.
"""

# Python
from datetime import date

# Proyecto
from service.servicio_api import ErrorServicioExterno, ServicioAPI
from service.servicio_clima import ServicioClima
from service.servicio_indicadores import ServicioIndicadores
from service.tarea_programada import TareaProgramada

resultados = {"ok": 0, "fallo": 0}


def verificar(descripcion: str, condicion: bool):
    if condicion:
        resultados["ok"] += 1
        print(f"  [OK] {descripcion}")
    else:
        resultados["fallo"] += 1
        print(f"  [FALLO] {descripcion}")


def lanza_error(funcion, tipo_error) -> bool:
    try:
        funcion()
        return False
    except tipo_error:
        return True


class RepositorioEnMemoria():
    """ Reemplaza a RepositorioDatoExterno para probar la rutina sin tocar Oracle """

    def __init__(self):
        self.climas = []
        self.indicadores = {}

    def guardar_clima(self, dato_clima, id_proyecto):
        self.climas.append((id_proyecto, dato_clima))
        return len(self.climas)

    def guardar_indicador(self, indicador):
        clave = (indicador.codigo, indicador.fecha)
        if clave in self.indicadores:  # igual que el MERGE: no duplica
            return False
        self.indicadores[clave] = indicador.valor
        return True


def ejecutar_pruebas():
    clima = ServicioClima()
    indicadores = ServicioIndicadores()

    print("\n1. CLASE ABSTRACTA")
    verificar("ServicioAPI no se puede instanciar", lanza_error(lambda: ServicioAPI("https://x"), TypeError))

    print("\n2. CLIMA (Open-Meteo)")
    dato = clima.consultar("Puerto Montt")
    verificar(f"clima de Puerto Montt: {dato}", dato.temperatura is not None and 0 <= dato.humedad <= 100)
    verificar("ciudad con símbolos rechazada antes de llamar a la API",
              lanza_error(lambda: clima.obtener_clima("Osorno&lat=0"), ValueError))
    try:
        clima.obtener_clima("Ciudadquenoexiste")
        verificar("ciudad inexistente → ErrorServicioExterno", False)
    except ErrorServicioExterno as e:
        verificar("ciudad inexistente → ErrorServicioExterno (404)", e.obtener_codigo_http() == 404)
        verificar("mensaje seguro sin URL", "http" not in e.mensaje_seguro())

    print("\n3. INDICADORES (mindicador.cl)")
    dolar = indicadores.consultar("usd")
    verificar(f"dólar: {dolar}", dolar.codigo == "USD" and dolar.valor > 0)
    verificar("CLP es la moneda base (1.0)", indicadores.obtener_indicador("CLP").valor == 1.0)
    verificar("código inválido rechazado", lanza_error(lambda: indicadores.obtener_indicador("PESOS"), ValueError))
    verificar("moneda no soportada → ErrorServicioExterno",
              lanza_error(lambda: indicadores.obtener_indicador("JPY"), ErrorServicioExterno))

    print("\n4. RUTINA DE LAS 08:00")
    repositorio = RepositorioEnMemoria()
    tarea = TareaProgramada(clima, indicadores, repositorio)
    # Mezcla de diccionario (como entrega RepositorioProyecto) y ciudad inválida
    tarea.configurar_proyectos([
        {"id_proyecto": 1, "ciudad": "Osorno", "moneda": "USD"},
        {"id_proyecto": 2, "ciudad": "Ciudadquenoexiste", "moneda": "USD"},
    ])
    resumen = tarea.ejecutar()
    verificar("guarda el clima del proyecto válido", resumen["clima"] == 1)
    verificar("la ciudad inexistente se informa como error sin detener la rutina", resumen["errores"] == 1)
    verificar("USD se consulta una sola vez", resumen["indicadores"] == 1)
    segunda = tarea.ejecutar()
    verificar("segunda ejecución no duplica el indicador", segunda["indicadores"] == 0)


if __name__ == "__main__":
    print("--- Prueba de servicios externos EcoTech ---")
    try:
        ejecutar_pruebas()
    except ErrorServicioExterno as e:
        print(f"[FALLO] Sin acceso a las APIs: {e.mensaje_seguro()}")
    print(f"\n--- Resultado: {resultados['ok']} OK, {resultados['fallo']} FALLO ---")


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: Un script que prueba ServicioClima, ServicioIndicadores,
  la clase abstracta ServicioAPI y la TareaProgramada.
- ¿Qué se adoptó?: Probar también los casos de error (ciudad inexistente, moneda no
  soportada, entradas inválidas) y que el mensaje seguro no exponga la URL.
- ¿Qué se modificó?: La rutina se prueba con un repositorio en memoria para no
  ensuciar la base de datos del evaluador.
- ¿Qué se descartó?: Simular las APIs con unittest.mock (ver abajo).

Código propuesto por la IA y DESCARTADO:

    from unittest.mock import patch

    @patch("requests.get")
    def test_clima(mock_get):
        mock_get.return_value.json.return_value = {"current": {...}}

Por qué se descartó: mock no se ha visto en la asignatura y probaría una respuesta
inventada. La guía pide verificar que los datos reales de la API sean utilizables.
"""
