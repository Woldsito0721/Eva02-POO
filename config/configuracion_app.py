# Python
import os

# Librerías
from dotenv import load_dotenv

# IA (Claude): estructura base sugerida. Se revisó que los errores nombren la
# variable faltante pero nunca muestren su valor (RF15).

load_dotenv()


class ConfiguracionApp():
    """ Lectura de credenciales y claves desde el archivo .env """

    def __init__(self):
        # Se guardan privadas para que nadie las cambie desde afuera
        self.__usuario_bd = os.getenv('DB_USER')
        self.__contrasena_bd = os.getenv('DB_PASSWORD')
        self.__dsn_bd = os.getenv('DB_DSN')
        self.__clave_fernet = os.getenv('FERNET_KEY')
        self.__clave_api_clima = os.getenv('API_KEY_CLIMA')
        self.__clave_api_indicadores = os.getenv('API_KEY_INDICADORES')

        self.__validar()

    def __validar(self):
        """ Verifica que existan los datos mínimos para conectarse a la BD """
        faltantes = []

        if not self.__usuario_bd:
            faltantes.append('DB_USER')
        if not self.__contrasena_bd:
            faltantes.append('DB_PASSWORD')
        if not self.__dsn_bd:
            faltantes.append('DB_DSN')

        if faltantes:
            # Solo se muestra el nombre de la variable, nunca su valor
            raise ValueError(f"[ERROR] Faltan variables en .env | {', '.join(faltantes)}")

    @property
    def usuario_bd(self):
        return self.__usuario_bd

    @property
    def contrasena_bd(self):
        return self.__contrasena_bd

    @property
    def dsn_bd(self):
        return self.__dsn_bd

    @property
    def clave_fernet(self):
        return self.__clave_fernet

    @property
    def clave_api_clima(self):
        return self.__clave_api_clima

    @property
    def clave_api_indicadores(self):
        return self.__clave_api_indicadores


if __name__ == "__main__":
    configuracion = ConfiguracionApp()
    print(f"[INFO] Configuración cargada para el usuario {configuracion.usuario_bd}")
