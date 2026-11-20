# Librerías
import oracledb

# Proyecto
from config.configuracion_app import ConfiguracionApp


class ConexionBD():
    """ Maneja la conexión a Oracle FreeSQL: abrir, cursor, commit, rollback y cierre """

    def __init__(self):
        configuracion = ConfiguracionApp()

        self.__usuario = configuracion.usuario_bd
        self.__contrasena = configuracion.contrasena_bd
        self.__dsn = configuracion.dsn_bd
        self.__conexion = None
        self.__fallo_conexion = False

    def conectar(self):
        """ Abre la conexión si aún no existe. Retorna True si quedó conectada """
        if self.__conexion:
            return True

        # Si ya falló una vez no se reintenta: cada intento fallido suma
        # para el bloqueo de la cuenta (ORA-28000)
        if self.__fallo_conexion:
            return False

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
            self.__fallo_conexion = True
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


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase ConexionBD a partir de la función conectar_db()
  vista en clases, con los métodos del diagrama (conectar, obtener_cursor, confirmar,
  revertir, cerrar) y soporte para "with".
- ¿Qué se adoptó?: Una sola conexión reutilizada por todos los repositorios, rollback
  automático si ocurre un error dentro del "with".
- ¿Qué se modificó?: Se reemplazó traceback.print_exc() por un mensaje con solo el
  código ORA (no expone datos internos) y se agregó __fallo_conexion: durante las
  pruebas, los reintentos automáticos bloquearon la cuenta de FreeSQL (ORA-28000).
- ¿Qué se descartó?: Un pool de conexiones (ver abajo).
- Justificación: Es un programa de consola de un solo usuario; una conexión basta y
  es más simple de explicar y depurar.

Código propuesto por la IA y DESCARTADO:

    self.__pool = oracledb.create_pool(
        user=self.__usuario, password=self.__contrasena, dsn=self.__dsn,
        min=1, max=5, increment=1
    )

    def obtener_cursor(self):
        return self.__pool.acquire().cursor()

Por qué se descartó:
  1. Un pool sirve cuando muchos usuarios se conectan a la vez (ej. una web); aquí
     hay un único usuario por ejecución.
  2. FreeSQL limita las sesiones por cuenta: abrir varias puede agotar el cupo.
  3. Cada cursor tomaría una conexión distinta, y commit/rollback ya no aplicarían
     a todas las operaciones de una misma transacción.
"""
