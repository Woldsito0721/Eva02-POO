"""
Sistema de gestión EcoTech Solutions - punto de entrada.
Ejecutar desde la raíz del proyecto:  python main.py

VERSIÓN PARCIAL (capa de datos): por ahora el menú trabaja con diccionarios y sin
inicio de sesión. Cuando estén listas las clases de model/ y security/ (Sesion,
ServicioCifrado), se agregan el login, los permisos por rol y el CRUD de empleados.

Reglas PEP8 (vistas en clases):
- clases -> inicial en mayúscula (SistemaEcoTech)
- funciones y variables -> minúscula y snake_case (mostrar_menu)
"""

# Python
from datetime import datetime

# Proyecto
from database.conexion_bd import ConexionBD
from database.repositorios import (
    RepositorioDatoExterno, RepositorioDepartamento, RepositorioEmpleado,
    RepositorioProyecto, RepositorioRegistroTiempo,
)


class SistemaEcoTech():
    """ Ciclo principal de la aplicación: conexión, menú y coordinación con los repositorios """

    def __init__(self):
        self.__conexion = ConexionBD()
        self.__repositorios = {}

    # ------------------------------------------------------------------
    # Entradas por consola (validación mínima mientras se integra Validador)
    # ------------------------------------------------------------------
    def __pedir_texto(self, mensaje: str, maximo: int, obligatorio: bool = True) -> str:
        while True:
            texto = input(mensaje).strip()
            if not texto and not obligatorio:
                return None
            if 0 < len(texto) <= maximo:
                return texto
            print(f"[WARNING] Debe tener entre 1 y {maximo} caracteres")

    def __pedir_entero(self, mensaje: str) -> int:
        while True:
            try:
                return int(input(mensaje))
            except ValueError:
                print("[WARNING] Debe ingresar un número entero")

    def __pedir_fecha(self, mensaje: str):
        while True:
            try:
                return datetime.strptime(input(mensaje).strip(), "%d-%m-%Y").date()
            except ValueError:
                print("[WARNING] Formato de fecha: dd-mm-aaaa")

    # ------------------------------------------------------------------
    # Proyectos (CRUD completo)
    # ------------------------------------------------------------------
    def __mostrar_proyecto(self, p: dict):
        print(f"  [{p['id_proyecto']}] {p['nombre']} | {p['ciudad']}, {p['pais']} | "
              f"moneda {p['moneda']} | inicio {p['fecha_inicio']:%d-%m-%Y}")

    def __listar_proyectos(self):
        proyectos = self.__repositorios["proyectos"].listar()
        if not proyectos:
            print("  (sin proyectos registrados)")
        for proyecto in proyectos:
            self.__mostrar_proyecto(proyecto)

    def __crear_proyecto(self):
        print("Ingrese datos del proyecto")
        self.__repositorios["proyectos"].insertar({
            "nombre": self.__pedir_texto(" - Nombre: ", 100),
            "descripcion": self.__pedir_texto(" - Descripción (opcional): ", 500, obligatorio=False),
            "fecha_inicio": self.__pedir_fecha(" - Fecha de inicio (dd-mm-aaaa): "),
            "pais": self.__pedir_texto(" - País: ", 60),
            "ciudad": self.__pedir_texto(" - Ciudad: ", 80),
            "moneda": self.__pedir_texto(" - Moneda (ej. CLP, USD): ", 10).upper(),
        })

    def __editar_proyecto(self):
        repositorio = self.__repositorios["proyectos"]
        proyecto = repositorio.buscar_por_id(self.__pedir_entero(" - Id del proyecto: "))
        if not proyecto:
            print("[WARNING] Proyecto no encontrado")
            return

        print("Deje en blanco para mantener el valor actual")
        for campo, maximo in (("nombre", 100), ("ciudad", 80), ("pais", 60), ("moneda", 10)):
            nuevo = self.__pedir_texto(f" - {campo} [{proyecto[campo]}]: ", maximo, obligatorio=False)
            if nuevo:
                proyecto[campo] = nuevo.upper() if campo == "moneda" else nuevo
        repositorio.actualizar(proyecto)

    def __eliminar_proyecto(self):
        id_proyecto = self.__pedir_entero(" - Id del proyecto a eliminar: ")
        if input(f"¿Confirma eliminar el proyecto {id_proyecto}? (s/n): ").lower() == "s":
            # Si tiene asignaciones u horas, el repositorio informa ORA-02292 y no se borra
            self.__repositorios["proyectos"].eliminar(id_proyecto)

    def __menu_proyectos(self):
        while True:
            print("\n--- Proyectos ---")
            print("1. Listar\n2. Crear\n3. Editar\n4. Eliminar\n0. Volver")
            opcion = input("Opción: ").strip()

            if opcion == "1":
                self.__listar_proyectos()
            elif opcion == "2":
                self.__crear_proyecto()
            elif opcion == "3":
                self.__editar_proyecto()
            elif opcion == "4":
                self.__eliminar_proyecto()
            elif opcion == "0":
                return
            else:
                print("[WARNING] Opción no válida")

    # ------------------------------------------------------------------
    # Consultas (solo lectura)
    # ------------------------------------------------------------------
    def __listar_departamentos(self):
        departamentos = self.__repositorios["departamentos"].listar()
        if not departamentos:
            print("  (sin departamentos registrados)")
        for d in departamentos:
            print(f"  [{d['id_departamento']}] {d['nombre']} | gerente: empleado {d['id_gerente']}")

    def __listar_empleados(self):
        empleados = self.__repositorios["empleados"].listar()
        if not empleados:
            print("  (sin empleados registrados)")
        for e in empleados:
            # El salario NO se muestra: requiere permiso VER_SALARIOS y descifrado (pendiente)
            print(f"  [{e['id_empleado']}] {e['nombre']} | {e['correo']} | "
                  f"departamento: {e['id_departamento'] or 'sin asignar'}")

    def __listar_horas(self):
        registros = self.__repositorios["registros"].listar()
        if not registros:
            print("  (sin horas registradas)")
        for r in registros:
            print(f"  {r['fecha']:%d-%m-%Y} | empleado {r['id_empleado']} | proyecto {r['id_proyecto']} | "
                  f"{r['horas_trabajadas']} h | {r['descripcion'] or ''}")

    def __listar_indicadores(self):
        indicadores = self.__repositorios["externos"].listar_indicadores()
        if not indicadores:
            print("  (sin indicadores: se cargan con la rutina de las 08:00)")
        for i in indicadores:
            print(f"  {i['fecha']:%d-%m-%Y} | {i['codigo']} = {i['valor']}")

    # ------------------------------------------------------------------
    # Ciclo principal
    # ------------------------------------------------------------------
    def mostrar_menu(self):
        print("\n===== EcoTech Solutions =====")
        print("1. Proyectos")
        print("2. Departamentos (listar)")
        print("3. Empleados (listar)")
        print("4. Horas registradas (listar)")
        print("5. Indicadores económicos (listar)")
        print("0. Salir")

    def ejecutar(self):
        print("[INFO] Conectando a Oracle FreeSQL...")
        if not self.__conexion.conectar():
            print("[ERROR] No se pudo iniciar: revise el .env (python -m test.prueba_conexion)")
            return

        self.__repositorios = {
            "proyectos": RepositorioProyecto(self.__conexion),
            "departamentos": RepositorioDepartamento(self.__conexion),
            "empleados": RepositorioEmpleado(self.__conexion),
            "registros": RepositorioRegistroTiempo(self.__conexion),
            "externos": RepositorioDatoExterno(self.__conexion),
        }

        try:
            while True:
                self.mostrar_menu()
                opcion = input("Opción: ").strip()

                if opcion == "1":
                    self.__menu_proyectos()
                elif opcion == "2":
                    self.__listar_departamentos()
                elif opcion == "3":
                    self.__listar_empleados()
                elif opcion == "4":
                    self.__listar_horas()
                elif opcion == "5":
                    self.__listar_indicadores()
                elif opcion == "0":
                    print("[INFO] Hasta pronto")
                    break
                else:
                    print("[WARNING] Opción no válida")
        except KeyboardInterrupt:
            print("\n[INFO] Programa interrumpido por el usuario")  # Ctrl+C no muestra traceback
        finally:
            self.__conexion.cerrar()  # La conexión se cierra siempre, aunque haya error


if __name__ == "__main__":
    SistemaEcoTech().ejecutar()


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase SistemaEcoTech con conexión única, menú
  principal, submenú CRUD de proyectos y listados de solo lectura.
- ¿Qué se adoptó?: Menú con if/elif como en la actividad de clases, mensajes
  [INFO]/[WARNING]/[ERROR], confirmación antes de eliminar y cierre de la conexión
  en finally.
- ¿Qué se modificó?: Las entradas se validan en bucle (texto con largo máximo según
  la columna de Oracle, enteros, fechas dd-mm-aaaa) para que un dato mal escrito no
  detenga el programa. El salario no se muestra en el listado de empleados.
- ¿Qué se descartó?: Un menú armado con un diccionario de funciones (ver abajo).
- Pendiente: login (Sesion), permisos por rol (Permiso) y CRUD de empleados con
  salario cifrado (ServicioCifrado), cuando el compañero termine model/ y security/.
  Reemplazar __pedir_texto por Validador.validar_texto / Validador.sanitizar.

Código propuesto por la IA y DESCARTADO:

    acciones = {
        "1": self.__menu_proyectos,
        "2": self.__listar_departamentos,
        "3": self.__listar_empleados,
        "0": lambda: exit(),
    }
    acciones.get(opcion, lambda: print("[WARNING] Opción no válida"))()

Por qué se descartó:
  1. Es más corto, pero usa lambda y funciones guardadas en un diccionario, algo que
     no se ha visto en clases y cuesta más explicar en la defensa.
  2. exit() dentro del lambda cerraría el programa sin pasar por el finally, y la
     conexión a Oracle quedaría abierta.
  3. Con if/elif es más fácil agregar después la verificación de permisos por opción
     (sesion.exigir_permiso(Permiso.GESTIONAR_PROYECTOS)).
"""
