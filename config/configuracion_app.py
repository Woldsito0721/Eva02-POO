# Python
import os

# Librerías
from dotenv import load_dotenv

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


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase ConfiguracionApp que lee el .env con
  python-dotenv y expone cada valor con @property de solo lectura.
- ¿Qué se adoptó?: Atributos privados (__) sin setters y validación de las variables
  obligatorias de la BD al crear el objeto.
- ¿Qué se modificó?: Los nombres se tradujeron al español (usuario_bd, clave_fernet...)
  para no mezclar idiomas; el mensaje de error nombra la variable faltante pero nunca
  muestra su valor (RF15).
- ¿Qué se descartó?: Constantes sueltas a nivel de módulo, como en la actividad de
  clases (ver abajo).
- Justificación: El diagrama pide una clase; con @property nadie puede reemplazar las
  credenciales desde otro archivo durante la ejecución.

Código propuesto por la IA y DESCARTADO:

    load_dotenv()
    DB_USER = os.getenv('DB_USER')
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_DSN = os.getenv('DB_DSN')

Por qué se descartó:
  1. Cualquier módulo puede sobrescribirlas (configuracion_app.DB_PASSWORD = "x").
  2. Si falta una variable queda en None sin aviso, y el error aparece recién al
     conectar, lejos de la causa real.
  3. No corresponde a la clase «utility» del diagrama.
"""
