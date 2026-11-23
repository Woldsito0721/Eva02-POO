"""
Prueba manual de la base de datos: conexión + ingreso de datos.
Ejecutar desde la raíz del proyecto:  python -m test.prueba_ingreso_bd

Trabaja sobre una tabla PROPIA de prueba (PRUEBA_BD), así no se tocan
las 8 tablas del sistema. Al terminar se puede borrar con la opción 4.
Hace UN solo intento de conexión (para no bloquear la cuenta: ORA-28000).
"""

# Librerías
import oracledb

# Proyecto
from database.conexion_bd import ConexionBD, codigo_error

TABLA_PRUEBA = "PRUEBA_BD"


def validar_conexion(bd: ConexionBD) -> bool:
    """ Conecta y muestra el usuario y la hora del servidor Oracle """
    if not bd.conectar():
        print("[FALLO] Sin conexión. ORA-01017 = contraseña incorrecta | "
              "ORA-28000 = cuenta bloqueada")
        return False

    cursor = bd.obtener_cursor()
    cursor.execute("select user, to_char(sysdate, 'DD-MM-YYYY HH24:MI:SS') from dual")
    usuario, hora = cursor.fetchone()
    cursor.close()
    print(f"[OK] Conectado como {usuario} | hora del servidor: {hora}")
    return True


def crear_tabla_prueba(bd: ConexionBD):
    """ Crea PRUEBA_BD solo si todavía no existe """
    cursor = bd.obtener_cursor()
    cursor.execute("select count(*) from user_tables where table_name = :nombre",
                   nombre=TABLA_PRUEBA)
    existe = cursor.fetchone()[0] > 0

    if not existe:
        cursor.execute(f"""
            CREATE TABLE {TABLA_PRUEBA} (
                id_prueba     NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                texto         VARCHAR2(100) NOT NULL,
                fecha_ingreso DATE DEFAULT SYSDATE
            )""")
        print(f"[OK] Tabla {TABLA_PRUEBA} creada")
    else:
        print(f"[INFO] La tabla {TABLA_PRUEBA} ya existe, se reutiliza")
    cursor.close()


def ingresar_registro(bd: ConexionBD):
    """ Inserta el texto que escribe el usuario (consulta parametrizada) """
    texto = input("Texto a ingresar: ").strip()
    if not texto or len(texto) > 100:
        print("[ERROR] El texto debe tener entre 1 y 100 caracteres")
        return

    cursor = bd.obtener_cursor()
    id_generado = cursor.var(oracledb.NUMBER)
    try:
        cursor.execute(
            f"INSERT INTO {TABLA_PRUEBA} (texto) VALUES (:texto) "
            "RETURNING id_prueba INTO :id_generado",
            texto=texto, id_generado=id_generado)
        bd.confirmar()
        print(f"[OK] Registro guardado con id {int(id_generado.getvalue()[0])}")
    except oracledb.Error as e:
        bd.revertir()
        print(f"[ERROR] No se pudo guardar | {codigo_error(e)}")
    finally:
        cursor.close()


def listar_registros(bd: ConexionBD):
    """ Muestra lo que hay guardado en PRUEBA_BD """
    cursor = bd.obtener_cursor()
    cursor.execute(f"SELECT id_prueba, texto, to_char(fecha_ingreso, 'DD-MM-YYYY HH24:MI') "
                   f"FROM {TABLA_PRUEBA} ORDER BY id_prueba")
    filas = cursor.fetchall()
    cursor.close()

    if not filas:
        print("[INFO] La tabla está vacía")
        return
    for id_prueba, texto, fecha in filas:
        print(f"  {id_prueba:>4} | {fecha} | {texto}")


def eliminar_registro(bd: ConexionBD):
    """ Borra un registro por id """
    entrada = input("Id a eliminar: ").strip()
    if not entrada.isdigit():
        print("[ERROR] El id debe ser un número")
        return

    cursor = bd.obtener_cursor()
    cursor.execute(f"DELETE FROM {TABLA_PRUEBA} WHERE id_prueba = :id",
                   id=int(entrada))
    borrados = cursor.rowcount
    bd.confirmar()
    cursor.close()
    print("[OK] Registro eliminado" if borrados else "[INFO] No existe ese id")


def borrar_tabla_prueba(bd: ConexionBD):
    """ Elimina PRUEBA_BD para dejar la BD como estaba """
    confirmacion = input(f"¿Borrar la tabla {TABLA_PRUEBA} y todos sus datos? (s/n): ")
    if confirmacion.strip().lower() != "s":
        print("[INFO] Cancelado")
        return
    cursor = bd.obtener_cursor()
    cursor.execute(f"DROP TABLE {TABLA_PRUEBA} PURGE")
    cursor.close()
    print(f"[OK] Tabla {TABLA_PRUEBA} eliminada")


def menu(bd: ConexionBD):
    opciones = {
        "1": ingresar_registro,
        "2": listar_registros,
        "3": eliminar_registro,
    }
    while True:
        print("\n--- Prueba de BD ---")
        print("1. Ingresar registro")
        print("2. Listar registros")
        print("3. Eliminar registro")
        print("4. Borrar tabla de prueba y salir")
        print("0. Salir (los datos quedan guardados)")
        opcion = input("Opción: ").strip()

        if opcion == "0":
            break
        if opcion == "4":
            borrar_tabla_prueba(bd)
            break
        accion = opciones.get(opcion)
        if accion:
            accion(bd)
        else:
            print("[ERROR] Opción no válida")


if __name__ == "__main__":
    bd = ConexionBD()  # Sin "with" para que haya un solo intento de conexión
    try:
        if validar_conexion(bd):
            crear_tabla_prueba(bd)
            menu(bd)
    finally:
        bd.cerrar()


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: Un script con menú para validar la conexión e
  ingresar, listar y eliminar datos en una tabla de prueba.
- ¿Qué se adoptó?: Tabla propia PRUEBA_BD, consultas parametrizadas (:texto, :id)
  y un solo intento de conexión, igual que test/prueba_conexion.py.
- ¿Qué se descartó?: Insertar directamente en DEPARTAMENTO (ver abajo).

Código propuesto por la IA y DESCARTADO:

    cursor.execute(
        "INSERT INTO departamento (nombre, id_gerente) VALUES (:nombre, :gerente)",
        nombre="Depto prueba", gerente=1)

Por qué se descartó: DEPARTAMENTO exige un gerente que exista en EMPLEADO, así que
la prueba fallaría con la BD vacía y además dejaría datos falsos en las tablas reales.
Una tabla aparte permite probar sin ensuciar el sistema y borrarla al final.
"""
