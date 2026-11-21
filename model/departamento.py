# Proyecto
from model.empleado import Empleado
from security.validador import Validador


class Departamento():
    """ Agrupa empleados (agregación 0..1 a 0..*) y tiene un gerente (cada departamento 1 gerente; un empleado puede gerenciar 0..* departamentos) """

    def __init__(self, nombre: str, gerente: Empleado, id_departamento: int = None):
        if not Validador.validar_texto(nombre, 100):
            raise ValueError("Nombre de departamento inválido (1 a 100 caracteres)")
        if not isinstance(gerente, Empleado):
            raise ValueError("El gerente debe ser un Empleado")

        self.__id_departamento = id_departamento
        self.__nombre = Validador.sanitizar(nombre)
        self.__gerente = gerente
        self.__empleados = []

    @property
    def id_departamento(self):
        return self.__id_departamento

    @property
    def nombre(self):
        return self.__nombre

    @property
    def gerente(self):
        return self.__gerente

    @property
    def id_gerente(self):
        return self.__gerente.id_empleado

    @property
    def empleados(self):
        return tuple(self.__empleados)  # copia de solo lectura: no se modifica la lista interna

    def agregar_empleado(self, empleado: Empleado) -> None:
        """ Un empleado pertenece como máximo a un departamento (0..1): sale del anterior """
        if empleado in self.__empleados:
            return
        if empleado.departamento is not None:
            empleado.departamento.quitar_empleado(empleado)

        self.__empleados.append(empleado)
        empleado._cambiar_departamento(self)

    def quitar_empleado(self, empleado: Empleado) -> None:
        if empleado in self.__empleados:
            self.__empleados.remove(empleado)
            empleado._cambiar_departamento(None)

    def cambiar_gerente(self, empleado: Empleado) -> None:
        if not isinstance(empleado, Empleado):
            raise ValueError("El gerente debe ser un Empleado")
        self.__gerente = empleado

    def obtener_nombre(self) -> str:
        return self.__nombre

    def __str__(self):
        return f"Departamento {self.__nombre} | gerente {self.__gerente.nombre} | {len(self.__empleados)} empleados"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: Departamento con lista de empleados, gerente y los
  métodos agregar/quitar empleado y cambiar gerente.
- ¿Qué se adoptó?: Agregación: los empleados existen aunque el departamento se borre
  (en Oracle: ON DELETE SET NULL).
- ¿Qué se modificó?: agregar_empleado() saca al empleado de su departamento anterior
  para respetar la multiplicidad 0..1 (RF3); empleados se entrega como tupla.
- ¿Qué se descartó?: Exponer la lista interna (ver abajo).

Código propuesto por la IA y DESCARTADO:

    @property
    def empleados(self):
        return self.__empleados

Por qué se descartó: devuelve la misma lista, así que desde afuera se podría hacer
departamento.empleados.append(x) y saltarse la regla de un solo departamento por
empleado. La tupla es una copia que no se puede modificar.
"""
