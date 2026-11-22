# Python
import hashlib
import hmac
import secrets

# Librerías
from cryptography.fernet import Fernet, InvalidToken

# Proyecto
from config.configuracion_app import ConfiguracionApp

"""
REGISTRO DE USO DE IA:
- ¿Qué se solicitó?: Implementar ServicioCifrado en Python con cifrado simétrico Fernet y hashing seguro de contraseñas.
- ¿Qué generó la herramienta?: Un borrador usando hashlib.sha256 sin salt y captura genérica de Exception al descifrar.
- ¿Qué se adoptó?: La estructura de métodos de instancia para cifrar/descifrar y @staticmethod para hashing según el UML.
- ¿Qué se modificó?: Primero se reemplazó sha256 por bcrypt. Luego, por exigencia del profesor, el hash de
  contraseñas se cambió a SHA-512 usando PBKDF2-HMAC-SHA512 (hashlib, librería estándar) con sal aleatoria
  de 16 bytes y 210.000 iteraciones. La clave Fernet se obtiene de ConfiguracionApp (AppConfig no existía).
- ¿Qué se descartó?: Hashes rápidos sin sal, SHA-512 de una sola pasada y bcrypt (ver código comentado al final).
- Justificación: Cumple el requisito de SHA-512; la sal impide comparar hashes iguales entre usuarios y las
  iteraciones hacen lenta la fuerza bruta. Los salarios siguen cifrados de forma reversible con Fernet.
"""


# Gestiona el cifrado reversible de salarios (Fernet) y el hash de contraseñas (PBKDF2-HMAC-SHA512).
class ServicioCifrado:
    ALGORITMO = "pbkdf2_sha512"
    ITERACIONES = 210_000   # valor recomendado por OWASP para PBKDF2-HMAC-SHA512
    BYTES_SAL = 16

    def __init__(self, clave: bytes | None = None) -> None:
        if clave is None:
            clave_texto = ConfiguracionApp().clave_fernet
            if not clave_texto:
                raise ValueError("[ERROR] Falta FERNET_KEY en el archivo .env (ver docs/manual_base_datos.md)")
            clave = clave_texto.encode()
        try:
            self.__fernet: Fernet = Fernet(clave)
        except (ValueError, TypeError) as exc:
            # No se muestra la clave: solo se avisa que el formato es inválido
            raise ValueError("[ERROR] FERNET_KEY no tiene un formato válido (clave Fernet de 44 caracteres)") from exc

    # --- Cifrado reversible (salarios) ---
    def cifrar(self, dato: str) -> bytes:
        if not isinstance(dato, str) or not dato.strip():
            raise ValueError("El dato a cifrar debe ser una cadena válida.")
        return self.__fernet.encrypt(dato.encode("utf-8"))

    def descifrar(self, dato: bytes) -> str:
        try:
            return self.__fernet.decrypt(dato).decode("utf-8")
        except InvalidToken as exc:
            raise ValueError("Token de cifrado inválido o clave incorrecta.") from exc

    # --- Hash de contraseñas (SHA-512, no reversible) ---
    @staticmethod
    def generar_hash(contrasena: str) -> str:
        """
        Retorna 'pbkdf2_sha512$iteraciones$sal$hash' (en hexadecimal, ~190 caracteres,
        cabe en USUARIO.hash_contrasena VARCHAR2(255)). La sal se guarda junto al hash
        porque se necesita para verificar; no es un secreto.
        """
        if not isinstance(contrasena, str) or len(contrasena) < 8:
            raise ValueError("La contraseña debe tener al menos 8 caracteres.")

        sal = secrets.token_bytes(ServicioCifrado.BYTES_SAL)  # sal aleatoria y distinta por usuario
        resumen = hashlib.pbkdf2_hmac("sha512", contrasena.encode("utf-8"), sal, ServicioCifrado.ITERACIONES)
        return f"{ServicioCifrado.ALGORITMO}${ServicioCifrado.ITERACIONES}${sal.hex()}${resumen.hex()}"

    @staticmethod
    def verificar_hash(contrasena: str, hash_guardado: str) -> bool:
        try:
            algoritmo, iteraciones, sal_hex, resumen_hex = hash_guardado.split("$")
            if algoritmo != ServicioCifrado.ALGORITMO:
                return False

            calculado = hashlib.pbkdf2_hmac(
                "sha512", contrasena.encode("utf-8"), bytes.fromhex(sal_hex), int(iteraciones)
            )
            # compare_digest compara en tiempo constante (no revela cuántos caracteres coinciden)
            return hmac.compare_digest(calculado.hex(), resumen_hex)
        except (ValueError, TypeError, AttributeError):
            return False


"""
Código propuesto por la IA y DESCARTADO:

1) SHA-512 de una sola pasada, sin sal:

    @staticmethod
    def generar_hash(contrasena: str) -> str:
        return hashlib.sha512(contrasena.encode("utf-8")).hexdigest()

   Por qué se descartó: dos usuarios con la misma contraseña tendrían el mismo hash,
   y SHA-512 solo es muy rápido (miles de millones de intentos por segundo en una GPU),
   por lo que se puede romper con tablas precalculadas o fuerza bruta.

2) Versión anterior con bcrypt:

    sal = bcrypt.gensalt()
    return bcrypt.hashpw(contrasena.encode("utf-8"), sal).decode("utf-8")

   Por qué se reemplazó: era segura, pero el profesor exige SHA-512. PBKDF2-HMAC-SHA512
   usa SHA-512 y mantiene la sal y el costo por iteraciones que daba bcrypt, sin
   instalar librerías extra (hashlib es parte de Python).
"""
