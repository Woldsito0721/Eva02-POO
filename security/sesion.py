from __future__ import annotations
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.usuario import Usuario
    from model.rol import Permiso

"""
REGISTRO DE USO DE IA:
- ¿Qué se solicitó?: Implementar las clases Sesion y AccesoDenegadoError según el paquete security del diagrama UML.
- ¿Qué generó la herramienta?: Una sesión sin tiempo de expiración y mensajes de excepción que revelaban el rol y permiso exacto del usuario.
- ¿Qué se adoptó?: El control de permisos mediante exigir_permiso() y el uso de TYPE_CHECKING para evitar importaciones circulares.
- ¿Qué se modificó?: Se añadió expiración automática (30 minutos por defecto) y el método mensaje_seguro() en AccesoDenegadoError.
- ¿Qué se descartó?: Exponer detalles internos del sistema o nombres de permisos en los mensajes mostrados por consola.
- Justificación: Restringe el acceso a operaciones sensibles y APIs cumpliendo los criterios 3.1.2 y 3.1.3 de la rúbrica.
"""


# Excepción personalizada que oculta detalles internos cuando falla la autenticación o los permisos.
class AccesoDenegadoError(Exception):
    def __init__(self, detalle_interno: str = "Acceso denegado.") -> None:
        super().__init__(detalle_interno)
        self.__detalle_interno = detalle_interno

    def mensaje_seguro(self) -> str:
        return "Acceso denegado: sesión expirada o permisos insuficientes para realizar esta acción."


# Controla la sesión activa del usuario, su tiempo de expiración(lo pide el diagrama.) y los permisos por rol.
class Sesion:
    def __init__(self, usuario: Usuario, minutos: int = 30) -> None:
        if minutos <= 0:
            raise ValueError("Los minutos de sesión deben ser mayores a 0.")
        self.__usuario: Usuario = usuario
        self.__inicio: datetime = datetime.now()
        self.__expira: datetime = self.__inicio + timedelta(minutes=minutos)
        self.__cerrada: bool = False

    def esta_activa(self) -> bool:
        return not self.__cerrada and datetime.now() < self.__expira

    def get_usuario(self) -> Usuario:
        return self.__usuario

    def exigir_permiso(self, p: Permiso) -> None:
        if not self.esta_activa():
            raise AccesoDenegadoError("La sesión ha expirado o fue cerrada.")
        if not self.__usuario.tiene_permiso(p):
            raise AccesoDenegadoError(
                f"Usuario sin permiso requerido: {p}"
            )

    def cerrar(self) -> None:
        self.__cerrada = True