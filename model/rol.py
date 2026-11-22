# Python
from enum import Enum


class Permiso(Enum):
    """ Acciones del sistema que se pueden autorizar a un rol """
    GESTIONAR_EMPLEADOS = "GESTIONAR_EMPLEADOS"
    GESTIONAR_DEPARTAMENTOS = "GESTIONAR_DEPARTAMENTOS"
    GESTIONAR_PROYECTOS = "GESTIONAR_PROYECTOS"
    REGISTRAR_HORAS = "REGISTRAR_HORAS"
    VER_SALARIOS = "VER_SALARIOS"
    CONSULTAR_APIS = "CONSULTAR_APIS"


# Permisos de cada rol. El nombre del rol es lo
# único que se guarda en Oracle (USUARIO.rol); los permisos se arman aquí.
PERMISOS_POR_ROL = {
    "ADMINISTRADOR": set(Permiso),  # todos los permisos
    "GERENTE": {
        Permiso.GESTIONAR_PROYECTOS, Permiso.REGISTRAR_HORAS, Permiso.CONSULTAR_APIS,
    },
    "EMPLEADO": {Permiso.REGISTRAR_HORAS},
}


class Rol():
    """ Rol de un usuario y el conjunto de permisos que concede """

    def __init__(self, nombre: str, permisos: set):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValueError("El nombre del rol no puede estar vacío")
        if not all(isinstance(p, Permiso) for p in permisos):
            raise ValueError("Los permisos deben ser del tipo Permiso")

        self.__nombre = nombre.strip().upper()
        self.__permisos = frozenset(permisos)  # inmutable: nadie agrega permisos desde afuera

    @classmethod
    def desde_nombre(cls, nombre: str):
        """ Crea el rol a partir del texto guardado en USUARIO.rol """
        nombre = str(nombre).strip().upper()
        if nombre not in PERMISOS_POR_ROL:
            raise ValueError(f"Rol no válido: {nombre}")
        return cls(nombre, PERMISOS_POR_ROL[nombre])

    def obtener_nombre(self) -> str:
        return self.__nombre

    @property
    def nombre(self) -> str:
        return self.__nombre

    def concede(self, permiso: Permiso) -> bool:
        return permiso in self.__permisos

    def __str__(self):
        return self.__nombre


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: El enum Permiso con los 6 permisos del diagrama y la
  clase Rol con nombre, permisos y concede().
- ¿Qué se adoptó?: Enum para que solo existan permisos válidos (un texto mal escrito
  como "VER_SALARIO" da error en vez de negar el acceso en silencio).
- ¿Qué se modificó?: Se agregó desde_nombre() para reconstruir el rol desde Oracle,
  y los permisos se guardan en un frozenset para que no se puedan modificar.
- ¿Qué se descartó?: Guardar los permisos como lista de textos (ver abajo) y el permiso
  GENERAR_INFORMES, porque los informes PDF/Excel quedaron fuera de alcance.
- Justificación: El rol vive en USUARIO.rol (texto con CHECK) y sus permisos en
  Python: si cambian los permisos de un rol no hay que modificar la base de datos.

Código propuesto por la IA y DESCARTADO:

    class Rol():
        def __init__(self, nombre: str, permisos: list):
            self.nombre = nombre
            self.permisos = permisos          # ej. ["VER_SALARIOS", "REGISTRAR_HORAS"]

        def concede(self, permiso: str) -> bool:
            return permiso in self.permisos

Por qué se descartó:
  1. Atributos públicos: cualquiera puede hacer rol.permisos.append("VER_SALARIOS").
  2. Con textos, un error de tipeo ("VER_SALARIO") no avisa: solo niega el acceso.
  3. No corresponde al «enumeration» Permiso del diagrama.
"""
