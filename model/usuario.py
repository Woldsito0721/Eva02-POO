# Proyecto
from model.rol import Permiso, Rol
from security.servicio_cifrado import ServicioCifrado


class Usuario():
    """ Cuenta de acceso al sistema de un empleado (no es un tipo de empleado) """

    MAXIMO_INTENTOS = 3

    def __init__(self, nombre_usuario: str, hash_contrasena: str, rol: Rol,
                 id_empleado: int = None, id_usuario: int = None,
                 intentos_fallidos: int = 0, bloqueado: bool = False):
        if not isinstance(nombre_usuario, str) or not 0 < len(nombre_usuario.strip()) <= 50:
            raise ValueError("El nombre de usuario debe tener entre 1 y 50 caracteres")
        if not isinstance(hash_contrasena, str) or not hash_contrasena.strip():
            raise ValueError("El hash de la contraseña no puede estar vacío")
        if not isinstance(rol, Rol):
            raise ValueError("El rol debe ser un objeto Rol")

        self.__id_usuario = id_usuario
        self.__nombre_usuario = nombre_usuario.strip()
        self.__hash_contrasena = hash_contrasena   # nunca se guarda la contraseña en texto plano
        self.__rol = rol
        self.__id_empleado = id_empleado
        self.__intentos_fallidos = int(intentos_fallidos)
        self.__bloqueado = bool(bloqueado)

    @classmethod
    def crear(cls, nombre_usuario: str, contrasena: str, rol: Rol, id_empleado: int):
        """ Crea un usuario nuevo a partir de la contraseña en texto (se guarda solo el hash) """
        return cls(nombre_usuario, ServicioCifrado.generar_hash(contrasena), rol, id_empleado)

    # --- Propiedades de solo lectura (sin setters) ---
    @property
    def id_usuario(self):
        return self.__id_usuario

    @property
    def nombre_usuario(self):
        return self.__nombre_usuario

    @property
    def hash_contrasena(self):
        return self.__hash_contrasena

    @property
    def rol(self):
        return self.__rol

    @property
    def id_empleado(self):
        return self.__id_empleado

    @property
    def intentos_fallidos(self):
        return self.__intentos_fallidos

    @property
    def bloqueado(self):
        return self.__bloqueado

    # --- Comportamiento ---
    def autenticar(self, contrasena: str) -> bool:
        """
        Verifica la contraseña. Cada fallo suma un intento y al tercero la cuenta
        se bloquea. Quien llama debe guardar el cambio con
        RepositorioUsuario.actualizar_intentos().
        """
        if self.__bloqueado:
            return False

        if ServicioCifrado.verificar_hash(contrasena, self.__hash_contrasena):
            self.__intentos_fallidos = 0
            return True

        self.__intentos_fallidos += 1
        if self.__intentos_fallidos >= self.MAXIMO_INTENTOS:
            self.__bloqueado = True
        return False

    def tiene_permiso(self, permiso: Permiso) -> bool:
        """ Usado por Sesion.exigir_permiso() """
        return not self.__bloqueado and self.__rol.concede(permiso)

    def cambiar_contrasena(self, actual: str, nueva: str) -> None:
        if self.__bloqueado:
            raise ValueError("La cuenta está bloqueada: un administrador debe desbloquearla")
        if not self.autenticar(actual):
            raise ValueError("La contraseña actual no es correcta")
        self.__hash_contrasena = ServicioCifrado.generar_hash(nueva)  # valida mínimo 8 caracteres

    def desbloquear(self) -> None:
        """ Solo un administrador debería llamarlo (se verifica en main con la sesión) """
        self.__intentos_fallidos = 0
        self.__bloqueado = False

    def obtener_nombre_usuario(self) -> str:
        return self.__nombre_usuario

    def __str__(self):
        estado = "BLOQUEADO" if self.__bloqueado else "activo"
        return f"Usuario {self.__nombre_usuario} | rol {self.__rol} | {estado}"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase Usuario con autenticación, conteo de intentos
  fallidos, bloqueo y verificación de permisos a través de su Rol.
- ¿Qué se adoptó?: Asociación con Empleado mediante id_empleado (un usuario ES una
  cuenta de acceso, no un tipo de empleado) y el hash SHA-512 (PBKDF2) de ServicioCifrado.
- ¿Qué se modificó?: Se agregaron crear() para no recibir nunca la contraseña en texto
  en el constructor, desbloquear() y el límite de 3 intentos fallidos.
- ¿Qué se descartó?: Comparar contraseñas en texto plano (ver abajo).
- Justificación: Si la BD se filtra, los hashes SHA-512 con sal no se pueden revertir.

Código propuesto por la IA y DESCARTADO:

    def autenticar(self, contrasena: str) -> bool:
        return self.contrasena == contrasena

Por qué se descartó:
  1. Obliga a guardar la contraseña en texto plano en Oracle (falla RF8).
  2. No cuenta intentos fallidos: permite fuerza bruta ilimitada.
  3. La comparación con == no es de tiempo constante; hmac.compare_digest sí lo es.
"""
