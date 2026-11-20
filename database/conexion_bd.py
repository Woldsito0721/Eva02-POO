# Librerías
import oracledb

# Proyecto
from config.configuracion_app import ConfiguracionApp

# IA (Claude): basado en conectar_db() visto en clases, convertido a clase según
# el diagrama. Se reemplazó traceback.print_exc() por un mensaje con solo el
# código ORA, para no exponer detalles internos de la conexión.


class ConexionBD():
    """ Maneja la conexión a Oracle FreeSQL: abrir, cursor, commit, rollback y cierre """

    def __init__(self):
        configuracion = ConfiguracionApp()

        self.__usuario = configuracion.usuario_bd
        self.__contrasena = configuracion.contrasena_bd
        self.__dsn = configuracion.dsn_bd
        self.__conexion = None

    def conectar(self):
        """ Abre la conexión si aún no existe. Retorna True si quedó conectada """
        if self.__conexion:
            return True

        try:
            self.__conexion = oracledb.connect(
                user=self.__usuario,
                password=self.__contrasena,
                dsn=self.__dsn
            )
            return True
        except oracledb.DatabaseError as e:
            error = e.args[0]
            print(f"[ERROR] No se pudo conectar a la BD | ORA-{error.code:05d}")
            self.__conexion = None
            return False

    def obtener_cursor(self):
        """ Entrega un cursor nuevo; conecta primero si es necesario """
        if not self.conectar():
            raise ConnectionError("[ERROR] Sin conexión a la base de datos")

        return self.__conexion.cursor()

    def confirmar(self):
        """ Guarda los cambios pendientes (commit) """
        if self.__conexion:
            self.__conexion.commit()

    def revertir(self):
        """ Deshace los cambios pendientes (rollback) """
        if self.__conexion:
            self.__conexion.rollback()

    def cerrar(self):
        """ Cierra la conexión si está abierta """
        if self.__conexion:
            self.__conexion.close()
            self.__conexion = None

    def esta_conectada(self):
        return self.__conexion is not None

    # Permite usar: with ConexionBD() as bd:
    def __enter__(self):
        self.conectar()
        return self

    def __exit__(self, tipo_error, valor_error, traza):
        if tipo_error:
            self.revertir()  # Si algo falla dentro del with, nada cambia en la BD
        self.cerrar()


if __name__ == "__main__":
    with ConexionBD() as bd:
        if bd.esta_conectada():
            cursor = bd.obtener_cursor()
            cursor.execute("select 'Conexión OK' from dual")
            print(f"[INFO] {cursor.fetchone()[0]}")
            cursor.close()
        else:
            print("[ERROR] No se pudo establecer la conexión")
