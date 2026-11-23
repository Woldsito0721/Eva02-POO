# Python
from abc import ABC, abstractmethod

# Librerías
import oracledb

# Proyecto
from database.conexion_bd import ConexionBD, codigo_error

# Mensajes para los errores de integridad más comunes
MENSAJES_ORA = {
    1: "El registro ya existe (dato único duplicado)",                      # ORA-00001
    2290: "Un dato no cumple las reglas de la tabla (CHECK)",               # ORA-02290
    2291: "El registro relacionado no existe (clave foránea)",              # ORA-02291
    2292: "No se puede eliminar: tiene registros asociados",                # ORA-02292
}


def leer_campo(dato, campo: str):
    """
    Lee un campo tanto de un diccionario como de un objeto de model/.
    Así los repositorios aceptan Proyecto, Empleado, DatoClima, etc., o un diccionario.
    """
    if isinstance(dato, dict):
        return dato.get(campo)
    return getattr(dato, campo, None)


class RepositorioCRUD(ABC):
    """ Clase base de todos los repositorios: define el CRUD y ejecuta el SQL de forma segura """

    def __init__(self, conexion: ConexionBD, tabla: str):
        self._conexion = conexion
        self._tabla = tabla

    # --- Contrato que cada repositorio concreto debe implementar ---
    @abstractmethod
    def insertar(self, objeto) -> int:
        pass

    @abstractmethod
    def buscar_por_id(self, id: int):
        pass

    @abstractmethod
    def listar(self) -> list:
        pass

    @abstractmethod
    def actualizar(self, objeto) -> bool:
        pass

    @abstractmethod
    def eliminar(self, id: int) -> bool:
        pass

    # --- Lógica común reutilizada por todos los repositorios ---
    def _ejecutar(self, sql: str, parametros=None, confirmar: bool = True, crear_id: bool = False):
        """
        Ejecuta una sentencia parametrizada (:nombre).
        Retorna el cursor si funcionó, o None si hubo error (después de hacer rollback).
        Quien recibe el cursor debe cerrarlo, y debe hacerlo dentro del candado.
        """
        cursor = None
        parametros = parametros if parametros is not None else {}

        try:
            cursor = self._conexion.obtener_cursor()

            if crear_id:
                # Variable de salida donde Oracle deja el id GENERATED ALWAYS AS IDENTITY
                parametros["id_generado"] = cursor.var(oracledb.NUMBER)

            cursor.execute(sql, parametros)  # Datos parametrizados: evita inyección SQL

            if confirmar:
                self._conexion.confirmar()

            return cursor
        except oracledb.IntegrityError as e:
            self._conexion.revertir()  # Si algo falla, nos aseguramos de que nada cambie en la bd
            numero = getattr(e.args[0], "code", 0) if e.args else 0
            mensaje = MENSAJES_ORA.get(numero, "Error de integridad")
            print(f"[WARNING] {self._tabla} | {mensaje} ({codigo_error(e)})")
        except oracledb.Error as e:  # cualquier otro error de Oracle (ORA-*) o del driver (DPY-*)
            self._conexion.revertir()
            print(f"[ERROR] {self._tabla} | Error de base de datos ({codigo_error(e)})")
        except ConnectionError as e:
            print(e)

        if cursor:
            cursor.close()
        return None

    def _insertar_con_id(self, sql: str, parametros: dict, informar: bool = True) -> int:
        """
        INSERT que termina en 'returning id_x into :id_generado'. Retorna el id (0 si falló).
        informar=False no imprime el [INFO] (para cargas automáticas de muchas filas).
        """
        with self._conexion.candado:
            cursor = self._ejecutar(sql, parametros, crear_id=True)
            if not cursor:
                return 0

            id_generado = int(parametros["id_generado"].getvalue()[0])
            cursor.close()

        if informar:
            print(f"[INFO] {self._tabla} | Registro {id_generado} insertado")
        return id_generado

    def _consultar_uno(self, sql: str, parametros=None):
        """ SELECT que retorna una sola fila (tupla) o None """
        with self._conexion.candado:
            cursor = self._ejecutar(sql, parametros, confirmar=False)
            if not cursor:
                return None

            fila = cursor.fetchone()
            cursor.close()
        return fila

    def _consultar_varios(self, sql: str, parametros=None) -> list:
        """ SELECT que retorna una lista de filas (tuplas) """
        with self._conexion.candado:
            cursor = self._ejecutar(sql, parametros, confirmar=False)
            if not cursor:
                return []

            filas = cursor.fetchall()
            cursor.close()
        return filas

    def _modificar(self, sql: str, parametros: dict) -> bool:
        """ UPDATE, DELETE o MERGE. Retorna True si afectó al menos una fila """
        with self._conexion.candado:
            cursor = self._ejecutar(sql, parametros)
            if not cursor:
                return False

            afectadas = cursor.rowcount  # rowcount = cantidad de filas afectadas
            cursor.close()
        return afectadas > 0


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase abstracta RepositorioCRUD con los 5 métodos
  abstractos del diagrama y los métodos protegidos _ejecutar, _insertar_con_id,
  _consultar_uno, _consultar_varios y _modificar.
- ¿Qué se adoptó?: Concentrar en _ejecutar() el try/except/commit/rollback que en la
  actividad de clases se repetía en cada función (insertar_datos_cliente, etc.), y
  distinguir los errores con error.code como enseñó el profesor.
- ¿Qué se modificó?: Se reemplazó traceback.print_exc() por mensajes con el código ORA
  (no expone detalles internos) y se agregó un diccionario MENSAJES_ORA en español.
  Tras la auditoría: cada operación se ejecuta dentro del candado de ConexionBD, se captura oracledb.Error en vez de solo
  DatabaseError, y leer_campo() permite recibir objetos de model/ o diccionarios.
  Cambio (23-11): _insertar_con_id() acepta informar=False para que la carga inicial de las
  10 ciudades no llene la pantalla con 10 mensajes [INFO].
- ¿Qué se descartó?: Un eliminar() genérico en la clase padre (ver abajo).
- Justificación: Cada hijo solo escribe su SQL; el manejo de errores se hereda, lo que
  evita duplicar código (criterio 2.1.2) y garantiza rollback ante cualquier fallo.

Código propuesto por la IA y DESCARTADO:

    def eliminar(self, id: int) -> bool:
        sql = f"delete from {self._tabla} where id_{self._tabla.lower()} = :id"
        return self._modificar(sql, {"id": id})

Por qué se descartó:
  1. Arma el nombre de la tabla y la columna con f-string. Aunque el valor viene del
     código y no del usuario, es mala práctica mezclar texto armado con SQL.
  2. No sirve para todas las tablas: DATO_CLIMA usa id_clima y REGISTRO_TIEMPO usa
     id_registro, no id_dato_clima ni id_registro_tiempo.
  3. Dejar eliminar() como abstracto obliga a cada repositorio a escribir su DELETE
     explícito, que es más fácil de leer y de explicar en la defensa.
"""
