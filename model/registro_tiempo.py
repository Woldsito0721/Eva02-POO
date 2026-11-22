from __future__ import annotations

# Python
from datetime import date, datetime
from typing import TYPE_CHECKING

# Proyecto
from security.validador import Validador

if TYPE_CHECKING:
    from model.empleado import Empleado
    from model.proyecto import Proyecto


class RegistroTiempo():
    """ Horas que un empleado trabajó en un proyecto en una fecha """

    def __init__(self, empleado: Empleado, proyecto: Proyecto, fecha: date, horas: float,
                 descripcion: str = None, id_registro: int = None):
        # oracledb entrega DATE como datetime: se convierte a date para poder comparar
        if isinstance(fecha, datetime):
            fecha = fecha.date()

        self.__id_registro = id_registro
        self.__empleado = empleado
        self.__proyecto = proyecto
        self.__fecha = fecha
        self.__horas_trabajadas = horas
        self.__descripcion = descripcion

        self.__validar()
        if self.__descripcion:
            self.__descripcion = Validador.sanitizar(self.__descripcion)

    def __validar(self) -> bool:
        """ Método privado del diagrama: revisa los datos antes de aceptarlos """
        if not isinstance(self.__fecha, date):
            raise ValueError("La fecha debe ser una fecha")
        if self.__fecha > date.today():
            raise ValueError("No se pueden registrar horas en fechas futuras")
        if not Validador.validar_horas(self.__horas_trabajadas):
            raise ValueError("Las horas deben ser un número mayor a 0 y hasta 24")
        if self.__descripcion and not Validador.validar_texto(self.__descripcion, 300):
            raise ValueError("Descripción inválida (máximo 300 caracteres)")
        return True

    @property
    def id_registro(self):
        return self.__id_registro

    @property
    def empleado(self):
        return self.__empleado

    @property
    def proyecto(self):
        return self.__proyecto

    @property
    def fecha(self):
        return self.__fecha

    @property
    def horas_trabajadas(self):
        return self.__horas_trabajadas

    @property
    def descripcion(self):
        return self.__descripcion

    def __str__(self):
        return f"{self.__fecha:%d-%m-%Y} | {self.__empleado.nombre} | {self.__proyecto.nombre} | {self.__horas_trabajadas} h"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: RegistroTiempo con empleado, proyecto, fecha, horas,
  descripción y el método privado __validar() del diagrama.
- ¿Qué se adoptó?: Validar las horas con Validador.validar_horas (mayor a 0 y hasta 24)
  antes de llegar al CHECK de Oracle.
- ¿Qué se modificó?: Se agregó la regla de no registrar horas en fechas futuras.
- ¿Qué se descartó?: Validar con assert (ver abajo).

Código propuesto por la IA y DESCARTADO:

    def __validar(self):
        assert 0 <= self.horas <= 24, "Horas fuera de rango"

Por qué se descartó: Python ignora los assert cuando se ejecuta con la opción -O,
así que la validación desaparecería sin aviso. ValueError siempre se ejecuta y
main.py lo puede capturar para mostrar un mensaje claro.
"""
