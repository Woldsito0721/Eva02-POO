from __future__ import annotations

# Python
from datetime import date, datetime
from typing import TYPE_CHECKING

# Proyecto
from security.validador import Validador

if TYPE_CHECKING:
    from model.empleado import Empleado
    from model.proyecto import Proyecto


class Asignacion():
    """ Clase intermedia Empleado ↔ Proyecto con el rol y el periodo de trabajo """

    def __init__(self, empleado: Empleado, proyecto: Proyecto, rol_en_proyecto: str = None,
                 fecha_asignacion: date = None, fecha_fin: date = None, id_asignacion: int = None):
        if rol_en_proyecto and not Validador.validar_texto(rol_en_proyecto, 60):
            raise ValueError("Rol en el proyecto inválido (máximo 60 caracteres)")

        # oracledb entrega DATE como datetime: se convierte a date para poder comparar
        if isinstance(fecha_asignacion, datetime):
            fecha_asignacion = fecha_asignacion.date()
        if isinstance(fecha_fin, datetime):
            fecha_fin = fecha_fin.date()
        fecha_asignacion = fecha_asignacion or date.today()
        if fecha_fin and fecha_fin < fecha_asignacion:
            raise ValueError("La fecha de fin no puede ser anterior a la de asignación")

        self.__id_asignacion = id_asignacion
        self.__empleado = empleado
        self.__proyecto = proyecto
        self.__rol_en_proyecto = Validador.sanitizar(rol_en_proyecto) if rol_en_proyecto else None
        self.__fecha_asignacion = fecha_asignacion
        self.__fecha_fin = fecha_fin

    @property
    def id_asignacion(self):
        return self.__id_asignacion

    @property
    def empleado(self):
        return self.__empleado

    @property
    def proyecto(self):
        return self.__proyecto

    @property
    def rol_en_proyecto(self):
        return self.__rol_en_proyecto

    @property
    def fecha_asignacion(self):
        return self.__fecha_asignacion

    @property
    def fecha_fin(self):
        return self.__fecha_fin

    def esta_activa(self) -> bool:
        # Finalizada hoy ya no está activa: el último día de trabajo es fecha_fin - 1
        return self.__fecha_fin is None or self.__fecha_fin > date.today()

    def finalizar(self, fecha_fin: date = None) -> None:
        fecha_fin = fecha_fin or date.today()
        if fecha_fin < self.__fecha_asignacion:
            raise ValueError("La fecha de fin no puede ser anterior a la de asignación")
        self.__fecha_fin = fecha_fin

    def __str__(self):
        estado = "activa" if self.esta_activa() else f"finalizada {self.__fecha_fin:%d-%m-%Y}"
        return f"{self.__empleado.nombre} en {self.__proyecto.nombre} ({self.__rol_en_proyecto or 'sin rol'}) | {estado}"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase asociativa Asignacion con empleado, proyecto,
  rol, fechas, esta_activa() y finalizar().
- ¿Qué se adoptó?: La misma regla del CHECK de Oracle (fecha_fin >= fecha_asignacion)
  se valida también en Python, para avisar antes de ir a la BD.
- ¿Qué se modificó?: fecha_asignacion es hoy por defecto; finalizar() recibe una fecha
  opcional para poder registrar términos pasados.
- ¿Qué se descartó?: Marcar la asignación con un booleano "activa" (ver abajo).

Código propuesto por la IA y DESCARTADO:

    def finalizar(self):
        self.activa = False

Por qué se descartó: se perdería CUÁNDO terminó la asignación, y la tabla ASIGNACION
guarda fecha_fin. Con la fecha, "activa" se calcula y nunca queda desincronizada.
"""
