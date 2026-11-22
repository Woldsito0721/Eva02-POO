"""
Prueba de conexión a Oracle FreeSQL.
Ejecutar desde la raíz del proyecto:  python -m test.prueba_conexion

Hace UN solo intento de conexión (para no bloquear la cuenta con
reintentos: ORA-28000) y revisa que existan las 8 tablas del sistema.
"""

# Proyecto
from config.configuracion_app import ConfiguracionApp
from database.conexion_bd import ConexionBD

TABLAS_ESPERADAS = [
    "ASIGNACION", "DATO_CLIMA", "DEPARTAMENTO", "EMPLEADO",
    "INDICADOR_ECONOMICO", "PROYECTO", "REGISTRO_TIEMPO", "USUARIO",
]


def probar_configuracion():
    """ Paso 1: el .env tiene los datos mínimos """
    try:
        configuracion = ConfiguracionApp()
        print(f"[OK] 1/3 .env cargado (usuario: {configuracion.usuario_bd})")
        return True
    except ValueError as e:
        print(f"[FALLO] 1/3 {e}")
        return False


def probar_conexion(bd: ConexionBD):
    """ Paso 2: Oracle acepta las credenciales """
    if bd.conectar():
        print("[OK] 2/3 Conectado a Oracle FreeSQL")
        return True

    print("[FALLO] 2/3 Sin conexión. ORA-01017 = contraseña incorrecta | "
          "ORA-28000 = cuenta bloqueada (regenerar contraseña en FreeSQL > Connect)")
    return False


def probar_tablas(bd: ConexionBD):
    """ Paso 3: existen las 8 tablas de sql/crear_tablas.sql """
    cursor = bd.obtener_cursor()
    cursor.execute("select table_name from user_tables")
    existentes = {fila[0] for fila in cursor.fetchall()}
    cursor.close()

    faltantes = [t for t in TABLAS_ESPERADAS if t not in existentes]
    if faltantes:
        print(f"[FALLO] 3/3 Faltan tablas: {', '.join(faltantes)} (ejecutar sql/crear_tablas.sql)")
        return False

    print("[OK] 3/3 Las 8 tablas existen")
    return True


if __name__ == "__main__":
    print("--- Prueba de conexión EcoTech ---")

    if probar_configuracion():
        bd = ConexionBD()  # Sin "with" para que haya un solo intento de conexión
        try:
            if probar_conexion(bd) and probar_tablas(bd):
                print("--- Todo correcto ---")
        finally:
            bd.cerrar()


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: Un script de 3 pasos (configuración, conexión, tablas).
- ¿Qué se modificó?: Se usa ConexionBD sin "with" para hacer UN solo intento de
  conexión; la primera versión hacía dos y aceleraba el bloqueo de la cuenta.
- ¿Qué se descartó?: Usar unittest/pytest (ver abajo).

Código propuesto por la IA y DESCARTADO:

    import unittest

    class PruebaConexion(unittest.TestCase):
        def test_conexion(self):
            self.assertTrue(ConexionBD().conectar())

Por qué se descartó: unittest no se ha visto en la asignatura; un script con mensajes
[OK]/[FALLO] es más fácil de leer en la defensa y muestra en qué paso falla.
"""
