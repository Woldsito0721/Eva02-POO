from __future__ import annotations

# Python
from datetime import date, datetime
from typing import TYPE_CHECKING

# Proyecto
from model.asignacion import Asignacion
from security.validador import Validador

if TYPE_CHECKING:
    from model.empleado import Empleado
    from model.registro_tiempo import RegistroTiempo


class Proyecto():
    """ Proyecto de EcoTech: dónde se ejecuta (ciudad, país) y en qué moneda se paga """

    def __init__(self, nombre: str, descripcion: str, fecha_inicio: date,
                 pais: str, ciudad: str, moneda: str, id_proyecto: int = None):
        # oracledb entrega DATE como datetime: se convierte a date para poder comparar
        if isinstance(fecha_inicio, datetime):
            fecha_inicio = fecha_inicio.date()
        if not Validador.validar_texto(nombre, 100):
            raise ValueError("Nombre de proyecto inválido (1 a 100 caracteres)")
        if descripcion and not Validador.validar_texto(descripcion, 500):
            raise ValueError("Descripción inválida (máximo 500 caracteres)")
        if not isinstance(fecha_inicio, date):
            raise ValueError("La fecha de inicio debe ser una fecha")
        if not Validador.validar_ciudad(pais):
            raise ValueError("País inválido")
        if not Validador.validar_ciudad(ciudad):  # se valida igual: se envía a la API de clima
            raise ValueError("Ciudad inválida (solo letras, espacios y guiones)")
        if not Validador.validar_codigo_moneda(moneda):
            raise ValueError("Moneda inválida (código de 3 letras, ej. CLP, USD)")

        self.__id_proyecto = id_proyecto
        self.__nombre = Validador.sanitizar(nombre)
        self.__descripcion = Validador.sanitizar(descripcion) if descripcion else None
        self.__fecha_inicio = fecha_inicio
        self.__pais = pais.strip()
        self.__ciudad = ciudad.strip()
        self.__moneda = moneda.strip().upper()
        self.__asignaciones = []
        self.__registros = []

    # --- Propiedades de solo lectura ---
    @property
    def id_proyecto(self):
        return self.__id_proyecto

    @property
    def nombre(self):
        return self.__nombre

    @property
    def descripcion(self):
        return self.__descripcion

    @property
    def fecha_inicio(self):
        return self.__fecha_inicio

    @property
    def pais(self):
        return self.__pais

    @property
    def ciudad(self):
        return self.__ciudad

    @property
    def moneda(self):
        return self.__moneda

    @property
    def asignaciones(self):
        return tuple(self.__asignaciones)

    # --- Comportamiento ---
    def asignar_empleado(self, empleado: Empleado, rol_en_proyecto: str = None) -> Asignacion:
        if self.tiene_asignado(empleado):
            raise ValueError(f"{empleado.nombre} ya está asignado a {self.__nombre}")

        asignacion = Asignacion(empleado, self, rol_en_proyecto)
        self.__asignaciones.append(asignacion)
        return asignacion

    def desasignar_empleado(self, empleado: Empleado) -> None:
        """ No borra la asignación: la finaliza, para conservar el historial """
        for asignacion in self.__asignaciones:
            if asignacion.empleado == empleado and asignacion.esta_activa():
                asignacion.finalizar()
                return
        raise ValueError(f"{empleado.nombre} no tiene una asignación activa en {self.__nombre}")

    def tiene_asignado(self, empleado: Empleado) -> bool:
        # == usa Empleado.__eq__: compara por id_empleado (o identidad si no tiene id)
        return any(a.empleado == empleado and a.esta_activa() for a in self.__asignaciones)

    def agregar_registro(self, registro: RegistroTiempo) -> None:
        """ Lo llama Empleado.registrar_horas() """
        self.__registros.append(registro)

    def calcular_horas_totales(self) -> float:
        return sum(registro.horas_trabajadas for registro in self.__registros)

    def __str__(self):
        return f"Proyecto {self.__nombre} | {self.__ciudad}, {self.__pais} | {self.__moneda}"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: Proyecto con sus datos, lista de asignaciones y
  registros, y los métodos asignar/desasignar empleado y calcular horas totales.
- ¿Qué se adoptó?: La relación muchos a muchos con Empleado se resuelve con la clase
  intermedia Asignacion (rol, fecha de asignación y de fin).
- ¿Qué se modificó?: Se validan ciudad y moneda con el Validador del compañero,
  porque esos datos se envían a las APIs externas (evita inyección en la URL);
  desasignar no borra, finaliza la asignación para conservar el historial.
- ¿Qué se descartó?: Guardar los empleados directamente en una lista (ver abajo).

Código propuesto por la IA y DESCARTADO:

    def asignar_empleado(self, empleado):
        self.empleados.append(empleado)

    def desasignar_empleado(self, empleado):
        self.empleados.remove(empleado)

Por qué se descartó:
  1. Pierde el rol en el proyecto y las fechas (RF6 exige rol, fecha de asignación y fin).
  2. remove() borra el historial: no se sabría quién trabajó antes en el proyecto.
  3. No usa la clase intermedia Asignacion que muestra el diagrama.
"""
