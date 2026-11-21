import bcrypt
from cryptography.fernet import Fernet, InvalidToken
from config.app_config import AppConfig

"""
REGISTRO DE USO DE IA:
- ¿Qué se solicitó?: Implementar ServicioCifrado en Python con cifrado simétrico Fernet y hashing seguro de contraseñas.
- ¿Qué generó la herramienta?: Un borrador usando hashlib.sha256 sin salt y captura genérica de Exception al descifrar.
- ¿Qué se adoptó?: La estructura de métodos de instancia para cifrar/descifrar y @staticmethod para hashing según el UML.
- ¿Qué se modificó?: Se reemplazó sha256 por bcrypt con generación automática de salt y se conectó el constructor por defecto con AppConfig.fernet().
- ¿Qué se descartó?: El uso de hashes rápidos sin sal (vulnerables a fuerza bruta) y bloques except genéricos.
- Justificación: Garantiza confidencialidad de salarios en RAW(200) y protección robusta de contraseñas en Oracle.
"""


# Gestiona el cifrado reversible de salarios y la encriptación de contraseñas (con bcrypt).
class ServicioCifrado:
    def __init__(self, clave: bytes | None = None) -> None:
        if clave is not None:
            self.__fernet: Fernet = Fernet(clave)
        else:
            self.__fernet: Fernet = AppConfig.fernet()

    def cifrar(self, dato: str) -> bytes:
        if not isinstance(dato, str) or not dato.strip():
            raise ValueError("El dato a cifrar debe ser una cadena válida.")
        return self.__fernet.encrypt(dato.encode("utf-8"))

    def descifrar(self, dato: bytes) -> str:
        try:
            return self.__fernet.decrypt(dato).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Token de cifrado inválido o clave incorrecta.") from exc

    @staticmethod
    def generar_hash(contrasena: str) -> str:
        if not isinstance(contrasena, str) or len(contrasena) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")
        sal = bcrypt.gensalt()
        hashed = bcrypt.hashpw(contrasena.encode("utf-8"), sal)
        return hashed.decode("utf-8")

    @staticmethod
    def verificar_hash(contrasena: str, hash_guardado: str) -> bool:
        try:
            return bcrypt.checkpw(
                contrasena.encode("utf-8"), hash_guardado.encode("utf-8")
            )
        except (ValueError, TypeError):
            return False