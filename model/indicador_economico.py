# Python
from datetime import date, datetime


class IndicadorEconomico():
    """ Valor de una moneda en pesos chilenos para una fecha (lo crea ServicioIndicadores) """

    def __init__(self, codigo: str, valor: float, fecha: date, id_indicador: int = None):
        if not isinstance(codigo, str) or not codigo.strip():
            raise ValueError("El código del indicador no puede estar vacío")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor <= 0:
            raise ValueError("El valor del indicador debe ser un número mayor a 0")

        # oracledb entrega DATE como datetime: se convierte a date para poder comparar
        if isinstance(fecha, datetime):
            fecha = fecha.date()

        self.__id_indicador = id_indicador
        self.__codigo = codigo.strip().upper()
        self.__valor = float(valor)
        self.__fecha = fecha

    @property
    def id_indicador(self):
        return self.__id_indicador

    @property
    def codigo(self):
        return self.__codigo

    @property
    def valor(self):
        return self.__valor

    @property
    def fecha(self):
        return self.__fecha

    def convertir_desde_clp(self, monto: float) -> float:
        """ Ej.: 1.000.000 CLP con USD = 1008.79 → 991.29 USD """
        if isinstance(monto, bool) or not isinstance(monto, (int, float)) or monto < 0:
            raise ValueError("El monto debe ser un número mayor o igual a 0")
        return round(monto / self.__valor, 2)

    def __str__(self):
        return f"{self.__codigo} = {self.__valor} CLP ({self.__fecha:%d-%m-%Y})"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: IndicadorEconomico con código, valor, fecha y
  convertir_desde_clp().
- ¿Qué se adoptó?: El valor representa cuántos pesos chilenos vale 1 unidad de la
  moneda (así lo entrega mindicador.cl), por eso convertir es monto / valor.
- ¿Qué se modificó?: El valor 0 o negativo se rechaza en el constructor: evita una
  división por cero al convertir; el resultado se redondea a 2 decimales.
- ¿Qué se descartó?: Multiplicar en vez de dividir (ver abajo).

Código propuesto por la IA y DESCARTADO:

    def convertir_desde_clp(self, monto):
        return monto * self.valor

Por qué se descartó: es la conversión al revés. 1.000.000 CLP * 1008.79 daría
1.008.790.000 "dólares". Se verificó con el valor real del dólar que entrega
ServicioIndicadores (1008.79) y la operación correcta es la división.
"""
