"""
Sistema de gestión EcoTech Solutions - punto de entrada.
Ejecutar desde la raíz del proyecto:  python main.py

Flujo: conexión a Oracle → (primera vez) creación del administrador → carga de datos
de internet (clima de 10 ciudades y monedas) → inicio de sesión → menú según los
permisos del rol → cierre de sesión.

Reglas PEP8 (vistas en clases):
- clases -> inicial en mayúscula (SistemaEcoTech)
- funciones y variables -> minúscula y snake_case (mostrar_menu)
"""

# Python
from datetime import date, datetime
from getpass import getpass

# Proyecto
from database.conexion_bd import ConexionBD
from database.repositorios import (
    RepositorioAsignacion, RepositorioDatoExterno, RepositorioDepartamento, RepositorioEmpleado,
    RepositorioProyecto, RepositorioRegistroTiempo, RepositorioUsuario,
)
from model.asignacion import Asignacion
from model.departamento import Departamento
from model.empleado import Empleado
from model.indicador_economico import IndicadorEconomico
from model.proyecto import Proyecto
from model.registro_tiempo import RegistroTiempo
from model.rol import PERMISOS_POR_ROL, Permiso, Rol
from model.usuario import Usuario
from security.servicio_cifrado import ServicioCifrado
from security.sesion import AccesoDenegadoError, Sesion
from security.validador import Validador
from service.carga_inicial import CargaInicial
from service.servicio_api import ErrorServicioExterno
from service.servicio_clima import ServicioClima
from service.servicio_indicadores import ServicioIndicadores


class SistemaEcoTech():
    """ Ciclo principal: conexión, carga de datos de internet, sesión y menús por permisos """

    MAXIMO_INTENTOS_LOGIN = 3

    def __init__(self):
        self.__conexion = None
        self.__sesion = None
        self.__cifrado = None
        self.__repositorios = {}
        self.__clima = ServicioClima()
        self.__indicadores = ServicioIndicadores()

    # ==================================================================
    # Entradas por consola (todas pasan por Validador)
    # ==================================================================
    def __pedir_texto(self, mensaje: str, maximo: int, obligatorio: bool = True):
        while True:
            texto = Validador.sanitizar(input(mensaje))
            if not texto and not obligatorio:
                return None
            if Validador.validar_texto(texto, maximo):
                return texto
            print(f"[WARNING] Debe tener entre 1 y {maximo} caracteres")

    def __pedir_con_validador(self, mensaje: str, validar, aviso: str, obligatorio: bool = True):
        """ Pide un dato hasta que la función validar() lo acepte """
        while True:
            texto = Validador.sanitizar(input(mensaje))
            if not texto and not obligatorio:
                return None
            if validar(texto):
                return texto
            print(f"[WARNING] {aviso}")

    def __pedir_entero(self, mensaje: str) -> int:
        while True:
            try:
                return int(input(mensaje))
            except ValueError:
                print("[WARNING] Debe ingresar un número entero")

    def __pedir_numero(self, mensaje: str) -> float:
        while True:
            try:
                return float(input(mensaje).replace(",", "."))
            except ValueError:
                print("[WARNING] Debe ingresar un número (ej. 7.5)")

    def __pedir_fecha(self, mensaje: str, vacia_es_hoy: bool = False):
        while True:
            texto = input(mensaje).strip()
            if not texto and vacia_es_hoy:
                return date.today()
            try:
                return datetime.strptime(texto, "%d-%m-%Y").date()
            except ValueError:
                print("[WARNING] Formato de fecha: dd-mm-aaaa")

    def __pedir_contrasena_nueva(self) -> str:
        while True:
            contrasena = getpass(" - Contraseña (mínimo 8 caracteres, no se muestra): ")
            if len(contrasena) < 8:
                print("[WARNING] La contraseña debe tener al menos 8 caracteres")
            elif getpass(" - Repita la contraseña: ") != contrasena:
                print("[WARNING] Las contraseñas no coinciden")
            else:
                return contrasena

    def __confirmar(self, mensaje: str) -> bool:
        return input(f"{mensaje} (s/n): ").strip().lower() == "s"

    # ==================================================================
    # Conversión de filas de Oracle (diccionarios) a objetos del modelo
    # ==================================================================
    def __empleado_desde_fila(self, fila: dict) -> Empleado:
        return Empleado(fila["nombre"], fila["direccion"], fila["telefono"], fila["correo"],
                        fila["fecha_inicio_contrato"], bytes(fila["salario_cifrado"]),
                        id_empleado=fila["id_empleado"])

    def __proyecto_desde_fila(self, fila: dict) -> Proyecto:
        return Proyecto(fila["nombre"], fila["descripcion"], fila["fecha_inicio"], fila["pais"],
                        fila["ciudad"], fila["moneda"], id_proyecto=fila["id_proyecto"])

    def __departamento_desde_fila(self, fila: dict) -> Departamento:
        """ El gerente es un Empleado (asociación «gerente»): se carga desde su fila """
        gerente = self.__empleado_desde_fila(self.__repositorios["empleados"].buscar_por_id(fila["id_gerente"]))
        return Departamento(fila["nombre"], gerente, id_departamento=fila["id_departamento"])

    def __usuario_desde_fila(self, fila: dict) -> Usuario:
        return Usuario(fila["nombre_usuario"], fila["hash_contrasena"], Rol.desde_nombre(fila["rol"]),
                       id_empleado=fila["id_empleado"], id_usuario=fila["id_usuario"],
                       intentos_fallidos=fila["intentos_fallidos"], bloqueado=fila["bloqueado"] == 1)

    # ==================================================================
    # Inicio: conexión, administrador inicial y sesión
    # ==================================================================
    def __iniciar_componentes(self) -> bool:
        try:
            self.__conexion = ConexionBD()       # lee el .env (ValueError si falta algo)
            self.__cifrado = ServicioCifrado()   # ValueError si falta o es inválida FERNET_KEY
        except ValueError as e:
            print(e)
            return False

        print("[INFO] Conectando a Oracle FreeSQL...")
        if not self.__conexion.conectar():
            print("[ERROR] No se pudo iniciar: revise el .env y la red (ver README.md)")
            return False

        self.__repositorios = {
            "proyectos": RepositorioProyecto(self.__conexion),
            "departamentos": RepositorioDepartamento(self.__conexion),
            "empleados": RepositorioEmpleado(self.__conexion),
            "asignaciones": RepositorioAsignacion(self.__conexion),
            "registros": RepositorioRegistroTiempo(self.__conexion),
            "usuarios": RepositorioUsuario(self.__conexion),
            "externos": RepositorioDatoExterno(self.__conexion),
        }
        return True

    def __crear_administrador_inicial(self) -> bool:
        """ Si USUARIO está vacía, crea el primer empleado y su cuenta ADMINISTRADOR """
        print("\n[INFO] No hay usuarios registrados. Se creará el administrador inicial.")
        try:
            empleado = Empleado.crear(
                self.__pedir_texto(" - Nombre completo: ", 100),
                None, None,
                self.__pedir_con_validador(" - Correo: ", Validador.validar_correo, "Correo inválido"),
                date.today(),
                self.__pedir_numero(" - Salario mensual (CLP): "),
                self.__cifrado,
            )
        except ValueError as e:
            print(f"[WARNING] {e}")
            return False

        id_empleado = self.__repositorios["empleados"].insertar(empleado)
        if not id_empleado:
            return False

        nombre_usuario = self.__pedir_texto(" - Nombre de usuario: ", 50)
        usuario = Usuario.crear(nombre_usuario, self.__pedir_contrasena_nueva(),
                                Rol.desde_nombre("ADMINISTRADOR"), id_empleado)
        if self.__repositorios["usuarios"].insertar(usuario):
            print("[INFO] Administrador creado. Ahora inicie sesión.")
            return True
        return False

    def iniciar_sesion(self, nombre_usuario: str, contrasena: str) -> bool:
        repositorio = self.__repositorios["usuarios"]
        fila = repositorio.buscar_por_nombre(nombre_usuario)
        # Mensaje genérico: no se revela si falló el usuario o la contraseña
        mensaje_fallo = "[WARNING] Usuario o contraseña incorrectos, o cuenta bloqueada"

        if not fila:
            print(mensaje_fallo)
            return False

        usuario = self.__usuario_desde_fila(fila)
        autenticado = usuario.autenticar(contrasena)
        # Los intentos fallidos y el bloqueo se guardan de inmediato en Oracle (RF8)
        repositorio.actualizar_intentos(usuario.id_usuario, usuario.intentos_fallidos, usuario.bloqueado)

        if not autenticado:
            print(mensaje_fallo)
            return False

        self.__sesion = Sesion(usuario)
        print(f"[INFO] Bienvenido/a {usuario.nombre_usuario} (rol {usuario.rol})")
        return True

    def cerrar_sesion(self) -> None:
        if self.__sesion:
            self.__sesion.cerrar()
            self.__sesion = None
            print("[INFO] Sesión cerrada")

    def __pantalla_login(self) -> bool:
        for _ in range(self.MAXIMO_INTENTOS_LOGIN):
            print("\n===== Inicio de sesión =====")
            nombre = Validador.sanitizar(input("Usuario: "))
            contrasena = getpass("Contraseña (no se muestra): ")
            if not nombre or not contrasena:
                print("[WARNING] Usuario y contraseña son obligatorios")
                continue
            if self.iniciar_sesion(nombre, contrasena):
                return True
        print("[ERROR] Demasiados intentos. Cerrando el programa.")
        return False

    def __usuario_actual(self) -> Usuario:
        return self.__sesion.obtener_usuario()

    def __exigir(self, permiso: Permiso) -> None:
        """ Lanza AccesoDenegadoError si la sesión expiró o el rol no tiene el permiso """
        self.__sesion.exigir_permiso(permiso)

    def __exigir_administrador(self) -> None:
        """ Gestión de usuarios: sesión vigente y rol ADMINISTRADOR """
        if not self.__sesion.esta_activa():
            raise AccesoDenegadoError("La sesión ha expirado o fue cerrada.")
        if not self.__es_administrador():
            raise AccesoDenegadoError("Gestión de usuarios reservada al ADMINISTRADOR")

    def __es_administrador(self) -> bool:
        return self.__usuario_actual().rol.nombre == "ADMINISTRADOR"

    # ==================================================================
    # 1. Proyectos
    # ==================================================================
    def __mostrar_proyecto(self, p: dict):
        print(f"  [{p['id_proyecto']}] {p['nombre']} | {p['ciudad']}, {p['pais']} | "
              f"moneda {p['moneda']} | inicio {p['fecha_inicio']:%d-%m-%Y}")

    def __listar_proyectos(self):
        proyectos = self.__repositorios["proyectos"].listar()
        if not proyectos:
            print("  (sin proyectos registrados)")
        for proyecto in proyectos:
            self.__mostrar_proyecto(proyecto)

    def __pedir_datos_proyecto(self, actual: dict = None) -> Proyecto:
        actual = actual or {}
        aviso = " (Enter = mantener)" if actual else ""
        obligatorio = not actual

        def valor(campo, nuevo):
            return nuevo if nuevo is not None else actual.get(campo)

        nombre = valor("nombre", self.__pedir_texto(f" - Nombre{aviso}: ", 100, obligatorio))
        descripcion = valor("descripcion", self.__pedir_texto(" - Descripción (opcional): ", 500, False))
        fecha = actual.get("fecha_inicio") or self.__pedir_fecha(" - Fecha de inicio (dd-mm-aaaa, Enter = hoy): ", True)
        pais = valor("pais", self.__pedir_con_validador(f" - País{aviso}: ", Validador.validar_ciudad, "Solo letras", obligatorio))
        ciudad = valor("ciudad", self.__pedir_con_validador(f" - Ciudad{aviso}: ", Validador.validar_ciudad, "Solo letras, espacios y guiones", obligatorio))
        moneda = valor("moneda", self.__pedir_con_validador(f" - Moneda ISO (CLP, USD, EUR){aviso}: ",
                                                             Validador.validar_codigo_moneda, "Código de 3 letras", obligatorio))
        # El constructor de Proyecto vuelve a validar todo (ValueError si algo está mal)
        return Proyecto(nombre, descripcion, fecha, pais, ciudad, moneda, id_proyecto=actual.get("id_proyecto"))

    def __menu_proyectos(self):
        self.__exigir(Permiso.GESTIONAR_PROYECTOS)
        repositorio = self.__repositorios["proyectos"]
        while True:
            self.__exigir(Permiso.GESTIONAR_PROYECTOS)  # en cada vuelta: la sesión pudo expirar dentro del submenú
            print("\n--- Proyectos ---\n1. Listar\n2. Crear\n3. Editar\n4. Eliminar\n0. Volver")
            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    self.__listar_proyectos()
                elif opcion == "2":
                    repositorio.insertar(self.__pedir_datos_proyecto())
                elif opcion == "3":
                    actual = repositorio.buscar_por_id(self.__pedir_entero(" - Id del proyecto: "))
                    if not actual:
                        print("[WARNING] Proyecto no encontrado")
                    elif repositorio.actualizar(self.__pedir_datos_proyecto(actual)):
                        print("[INFO] Proyecto actualizado")
                elif opcion == "4":
                    id_proyecto = self.__pedir_entero(" - Id del proyecto a eliminar: ")
                    # Con asignaciones u horas, Oracle responde ORA-02292 y no se borra
                    if self.__confirmar(f"¿Eliminar el proyecto {id_proyecto}?") and repositorio.eliminar(id_proyecto):
                        print("[INFO] Proyecto eliminado")
                elif opcion == "0":
                    return
                else:
                    print("[WARNING] Opción no válida")
            except ValueError as e:
                print(f"[WARNING] {e}")

    # ==================================================================
    # 2. Departamentos
    # ==================================================================
    def __menu_departamentos(self):
        self.__exigir(Permiso.GESTIONAR_DEPARTAMENTOS)
        repositorio = self.__repositorios["departamentos"]
        empleados = self.__repositorios["empleados"]
        while True:
            self.__exigir(Permiso.GESTIONAR_DEPARTAMENTOS)  # en cada vuelta: la sesión pudo expirar dentro del submenú
            print("\n--- Departamentos ---\n1. Listar\n2. Crear\n3. Editar\n4. Eliminar\n5. Asignar empleado\n0. Volver")
            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    departamentos = repositorio.listar()
                    if not departamentos:
                        print("  (sin departamentos registrados)")
                    for d in departamentos:
                        print(f"  [{d['id_departamento']}] {d['nombre']} | gerente: empleado {d['id_gerente']}")
                elif opcion in ("2", "3"):
                    actual = None
                    if opcion == "3":
                        actual = repositorio.buscar_por_id(self.__pedir_entero(" - Id del departamento: "))
                        if not actual:
                            print("[WARNING] Departamento no encontrado")
                            continue
                    fila_gerente = empleados.buscar_por_id(self.__pedir_entero(" - Id del empleado gerente: "))
                    if not fila_gerente:
                        print("[WARNING] El gerente debe ser un empleado existente")
                        continue
                    departamento = Departamento(self.__pedir_texto(" - Nombre: ", 100),
                                                self.__empleado_desde_fila(fila_gerente),
                                                id_departamento=actual["id_departamento"] if actual else None)
                    if actual:
                        if repositorio.actualizar(departamento):
                            print("[INFO] Departamento actualizado")
                    else:
                        repositorio.insertar(departamento)
                elif opcion == "4":
                    id_departamento = self.__pedir_entero(" - Id del departamento a eliminar: ")
                    # ON DELETE SET NULL: sus empleados quedan sin departamento
                    if self.__confirmar("Sus empleados quedarán sin departamento. ¿Continuar?") and repositorio.eliminar(id_departamento):
                        print("[INFO] Departamento eliminado")
                elif opcion == "5":
                    fila = empleados.buscar_por_id(self.__pedir_entero(" - Id del empleado: "))
                    if not fila:
                        print("[WARNING] Empleado no encontrado")
                        continue
                    id_departamento = self.__pedir_entero(" - Id del departamento (0 = quitar): ")
                    # El empleado se arma sin departamento: con 0 queda así (NULL en Oracle)
                    empleado = self.__empleado_desde_fila(fila)
                    if id_departamento:
                        fila_departamento = repositorio.buscar_por_id(id_departamento)
                        if not fila_departamento:
                            print("[WARNING] Departamento no encontrado")
                            continue
                        # Agregación 0..1: agregar_empleado() deja al empleado en UN solo departamento
                        self.__departamento_desde_fila(fila_departamento).agregar_empleado(empleado)
                    if empleados.actualizar(empleado):
                        print("[INFO] Departamento del empleado actualizado")
                elif opcion == "0":
                    return
                else:
                    print("[WARNING] Opción no válida")
            except ValueError as e:
                print(f"[WARNING] {e}")

    # ==================================================================
    # 3. Empleados (salario cifrado)
    # ==================================================================
    def __menu_empleados(self):
        self.__exigir(Permiso.GESTIONAR_EMPLEADOS)
        repositorio = self.__repositorios["empleados"]
        while True:
            self.__exigir(Permiso.GESTIONAR_EMPLEADOS)  # en cada vuelta: la sesión pudo expirar dentro del submenú
            print("\n--- Empleados ---\n1. Listar\n2. Crear\n3. Editar datos de contacto\n4. Eliminar"
                  "\n5. Ver salario\n6. Calcular pago en moneda extranjera\n0. Volver")
            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    empleados = repositorio.listar()
                    if not empleados:
                        print("  (sin empleados registrados)")
                    for e in empleados:
                        # El salario NO se muestra aquí: requiere el permiso VER_SALARIOS
                        print(f"  [{e['id_empleado']}] {e['nombre']} | {e['correo']} | "
                              f"departamento: {e['id_departamento'] or 'sin asignar'}")
                elif opcion == "2":
                    empleado = Empleado.crear(
                        self.__pedir_texto(" - Nombre: ", 100),
                        self.__pedir_texto(" - Dirección (opcional): ", 200, False),
                        self.__pedir_con_validador(" - Teléfono (opcional): ", Validador.validar_telefono, "8 a 15 dígitos", False),
                        self.__pedir_con_validador(" - Correo: ", Validador.validar_correo, "Correo inválido"),
                        self.__pedir_fecha(" - Inicio de contrato (dd-mm-aaaa, Enter = hoy): ", True),
                        self.__pedir_numero(" - Salario mensual (CLP): "),
                        self.__cifrado,  # el salario se cifra con Fernet antes de llegar a Oracle
                    )
                    repositorio.insertar(empleado)
                elif opcion == "3":
                    fila = repositorio.buscar_por_id(self.__pedir_entero(" - Id del empleado: "))
                    if not fila:
                        print("[WARNING] Empleado no encontrado")
                        continue
                    print("Deje en blanco para mantener el valor actual")
                    fila["direccion"] = self.__pedir_texto(f" - Dirección [{fila['direccion']}]: ", 200, False) or fila["direccion"]
                    fila["telefono"] = self.__pedir_con_validador(f" - Teléfono [{fila['telefono']}]: ",
                                                                   Validador.validar_telefono, "8 a 15 dígitos", False) or fila["telefono"]
                    fila["correo"] = self.__pedir_con_validador(f" - Correo [{fila['correo']}]: ",
                                                                 Validador.validar_correo, "Correo inválido", False) or fila["correo"]
                    if repositorio.actualizar(fila):
                        print("[INFO] Empleado actualizado")
                elif opcion == "4":
                    id_empleado = self.__pedir_entero(" - Id del empleado a eliminar: ")
                    # Con asignaciones, horas o siendo gerente → ORA-02292
                    if self.__confirmar(f"¿Eliminar el empleado {id_empleado}?") and repositorio.eliminar(id_empleado):
                        print("[INFO] Empleado eliminado")
                elif opcion in ("5", "6"):
                    fila = repositorio.buscar_por_id(self.__pedir_entero(" - Id del empleado: "))
                    if not fila:
                        print("[WARNING] Empleado no encontrado")
                        continue
                    empleado = self.__empleado_desde_fila(fila)
                    if opcion == "5":
                        # obtener_salario() exige VER_SALARIOS: si no lo tiene → AccesoDenegadoError
                        salario = empleado.obtener_salario(self.__usuario_actual(), self.__cifrado)
                        print(f"  Salario de {empleado.nombre}: ${salario:,.0f} CLP")
                    else:
                        self.__exigir(Permiso.CONSULTAR_APIS)
                        codigo = self.__pedir_con_validador(" - Moneda (USD o EUR): ",
                                                            lambda texto: texto.upper() in ServicioIndicadores.PRINCIPALES,
                                                            "Escriba USD o EUR")
                        indicador = self.__obtener_indicador(codigo.upper())
                        if not indicador:
                            print("[WARNING] No hay valor disponible para esa moneda (sin internet y sin datos guardados)")
                            continue
                        pago = empleado.calcular_pago_en_moneda(self.__usuario_actual(), indicador, self.__cifrado)
                        print(f"  Pago de {empleado.nombre}: {pago:,.2f} {indicador.codigo} "
                              f"(1 {indicador.codigo} = {indicador.valor} CLP al {indicador.fecha:%d-%m-%Y})")
                elif opcion == "0":
                    return
                else:
                    print("[WARNING] Opción no válida")
            except ValueError as e:
                print(f"[WARNING] {e}")
            except ErrorServicioExterno as e:
                print(f"[WARNING] {e.mensaje_seguro()}")

    # ==================================================================
    # 4. Asignaciones
    # ==================================================================
    def __menu_asignaciones(self):
        self.__exigir(Permiso.GESTIONAR_PROYECTOS)
        repositorio = self.__repositorios["asignaciones"]
        while True:
            self.__exigir(Permiso.GESTIONAR_PROYECTOS)  # en cada vuelta: la sesión pudo expirar dentro del submenú
            print("\n--- Asignaciones ---\n1. Listar por proyecto\n2. Asignar empleado a proyecto\n3. Finalizar asignación\n0. Volver")
            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    asignaciones = repositorio.listar_por_proyecto(self.__pedir_entero(" - Id del proyecto: "))
                    if not asignaciones:
                        print("  (sin asignaciones)")
                    for a in asignaciones:
                        estado = "activa" if a["fecha_fin"] is None else f"finalizada {a['fecha_fin']:%d-%m-%Y}"
                        print(f"  [{a['id_asignacion']}] empleado {a['id_empleado']} | {a['rol_en_proyecto'] or 'sin rol'} | {estado}")
                elif opcion == "2":
                    fila_empleado = self.__repositorios["empleados"].buscar_por_id(self.__pedir_entero(" - Id del empleado: "))
                    fila_proyecto = self.__repositorios["proyectos"].buscar_por_id(self.__pedir_entero(" - Id del proyecto: "))
                    if not fila_empleado or not fila_proyecto:
                        print("[WARNING] Empleado o proyecto no encontrado")
                        continue
                    if repositorio.esta_asignado(fila_empleado["id_empleado"], fila_proyecto["id_proyecto"]):
                        print("[WARNING] El empleado ya tiene una asignación activa en ese proyecto")
                        continue
                    # Clase asociativa del diagrama: une el objeto Empleado con el objeto Proyecto
                    asignacion = Asignacion(self.__empleado_desde_fila(fila_empleado),
                                            self.__proyecto_desde_fila(fila_proyecto),
                                            self.__pedir_texto(" - Rol en el proyecto (opcional): ", 60, False))
                    repositorio.insertar(asignacion)
                elif opcion == "3":
                    fila = repositorio.buscar_por_id(self.__pedir_entero(" - Id de la asignación: "))
                    if not fila:
                        print("[WARNING] Asignación no encontrada")
                        continue
                    asignacion = Asignacion(
                        self.__empleado_desde_fila(self.__repositorios["empleados"].buscar_por_id(fila["id_empleado"])),
                        self.__proyecto_desde_fila(self.__repositorios["proyectos"].buscar_por_id(fila["id_proyecto"])),
                        fila["rol_en_proyecto"], fila["fecha_asignacion"], fila["fecha_fin"], fila["id_asignacion"])
                    if not asignacion.esta_activa():
                        print("[WARNING] La asignación ya estaba finalizada")
                        continue
                    asignacion.finalizar()  # valida fecha_fin >= fecha_asignacion
                    if repositorio.actualizar(asignacion):
                        print("[INFO] Asignación finalizada (se conserva en el historial)")
                elif opcion == "0":
                    return
                else:
                    print("[WARNING] Opción no válida")
            except ValueError as e:
                print(f"[WARNING] {e}")

    # ==================================================================
    # 5. Registro de horas
    # ==================================================================
    def __menu_horas(self):
        self.__exigir(Permiso.REGISTRAR_HORAS)
        registros = self.__repositorios["registros"]
        id_empleado = self.__usuario_actual().id_empleado  # cada usuario registra SUS horas
        while True:
            self.__exigir(Permiso.REGISTRAR_HORAS)  # en cada vuelta: la sesión pudo expirar dentro del submenú
            print("\n--- Registro de horas ---\n1. Registrar horas\n2. Listar mis horas\n0. Volver")
            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    fila_proyecto = self.__repositorios["proyectos"].buscar_por_id(self.__pedir_entero(" - Id del proyecto: "))
                    if not fila_proyecto:
                        print("[WARNING] Proyecto no encontrado")
                        continue
                    # RF4: solo puede registrar horas en un proyecto donde está asignado
                    if not self.__repositorios["asignaciones"].esta_asignado(id_empleado, fila_proyecto["id_proyecto"]):
                        print("[WARNING] No tiene una asignación activa en ese proyecto")
                        continue
                    # RegistroTiempo.__validar() revisa horas (0 a 24], fecha no futura y descripción
                    registro = RegistroTiempo(
                        self.__empleado_desde_fila(self.__repositorios["empleados"].buscar_por_id(id_empleado)),
                        self.__proyecto_desde_fila(fila_proyecto),
                        self.__pedir_fecha(" - Fecha (dd-mm-aaaa, Enter = hoy): ", True),
                        self.__pedir_numero(" - Horas trabajadas (más de 0 y hasta 24): "),
                        self.__pedir_texto(" - Descripción (opcional): ", 300, False))
                    registros.insertar(registro)
                elif opcion == "2":
                    propios = registros.listar_por_empleado(id_empleado)
                    if not propios:
                        print("  (sin horas registradas)")
                    for r in propios:
                        print(f"  {r['fecha']:%d-%m-%Y} | proyecto {r['id_proyecto']} | {r['horas_trabajadas']} h | {r['descripcion'] or ''}")
                elif opcion == "0":
                    return
                else:
                    print("[WARNING] Opción no válida")
            except ValueError as e:
                print(f"[WARNING] {e}")

    # ==================================================================
    # 6. Usuarios (solo ADMINISTRADOR)
    # ==================================================================
    def __menu_usuarios(self):
        self.__exigir_administrador()
        repositorio = self.__repositorios["usuarios"]
        while True:
            self.__exigir_administrador()  # en cada vuelta: la sesión pudo expirar
            print("\n--- Usuarios ---\n1. Listar\n2. Crear usuario para un empleado\n3. Desbloquear cuenta\n0. Volver")
            opcion = input("Opción: ").strip()
            if opcion == "1":
                for u in repositorio.listar():
                    estado = "BLOQUEADO" if u["bloqueado"] == 1 else "activo"
                    print(f"  [{u['id_usuario']}] {u['nombre_usuario']} | {u['rol']} | empleado {u['id_empleado']} | {estado}")
            elif opcion == "2":
                id_empleado = self.__pedir_entero(" - Id del empleado: ")
                if not self.__repositorios["empleados"].buscar_por_id(id_empleado):
                    print("[WARNING] Empleado no encontrado")
                    continue
                rol = self.__pedir_con_validador(" - Rol (ADMINISTRADOR, GERENTE, EMPLEADO): ",
                                                 lambda texto: texto.upper() in PERMISOS_POR_ROL, "Rol no válido")
                usuario = Usuario.crear(self.__pedir_texto(" - Nombre de usuario: ", 50),
                                        self.__pedir_contrasena_nueva(), Rol.desde_nombre(rol), id_empleado)
                repositorio.insertar(usuario)  # usuario o empleado repetido → ORA-00001
            elif opcion == "3":
                fila = repositorio.buscar_por_nombre(self.__pedir_texto(" - Nombre de usuario: ", 50))
                if not fila:
                    print("[WARNING] Usuario no encontrado")
                    continue
                usuario = self.__usuario_desde_fila(fila)
                usuario.desbloquear()
                if repositorio.actualizar_intentos(usuario.id_usuario, 0, False):
                    print(f"[INFO] Cuenta {usuario.nombre_usuario} desbloqueada")
            elif opcion == "0":
                return
            else:
                print("[WARNING] Opción no válida")

    # ==================================================================
    # 7. Clima y monedas (APIs)
    # ==================================================================
    def __cargar_datos_internet(self):
        """ Al iniciar el programa: clima de las 10 ciudades y monedas principales a Oracle """
        print("[INFO] Cargando datos de internet (clima de 10 ciudades y monedas)...")
        carga = CargaInicial(self.__clima, self.__indicadores, self.__repositorios["externos"])
        resumen = carga.ejecutar()
        print(f"[INFO] Datos cargados: {resumen['clima']} ciudades y {resumen['indicadores']} monedas"
              + (f" ({resumen['errores']} con error; se usarán los últimos datos guardados)" if resumen["errores"] else ""))

    def __obtener_indicador(self, codigo: str):
        """
        Valor de una moneda: 1) el guardado HOY (carga inicial), 2) internet,
        3) el último guardado en Oracle si la API no responde. None si no hay nada.
        """
        externos = self.__repositorios["externos"]
        guardado = externos.ultimo_indicador(codigo)
        if guardado and guardado["fecha"].date() >= date.today():
            return IndicadorEconomico(guardado["codigo"], float(guardado["valor"]), guardado["fecha"])
        try:
            indicador = self.__indicadores.obtener_indicador(codigo)
            externos.guardar_indicador(indicador)
            return indicador
        except ErrorServicioExterno as e:
            print(f"[WARNING] {ServicioIndicadores.NOMBRES.get(codigo, codigo)}: {e.mensaje_seguro()}")
        if guardado:
            print(f"[INFO] Se usa el último valor guardado ({guardado['fecha']:%d-%m-%Y})")
            return IndicadorEconomico(guardado["codigo"], float(guardado["valor"]), guardado["fecha"])
        return None

    def __consultar_clima(self):
        ciudades = list(ServicioClima.CIUDADES)
        print("\n--- Ciudades ---")
        for numero, ciudad in enumerate(ciudades, start=1):
            print(f"{numero:>2}. {ciudad}")
        print(" 0. Volver")
        numero = self.__pedir_entero("Ciudad: ")
        if numero == 0:
            return
        if not 1 <= numero <= len(ciudades):
            print("[WARNING] Opción no válida")
            return

        # Clima de AHORA y las horas que quedan del día (hora local de la ciudad)
        actual, siguientes = self.__clima.obtener_pronostico(ciudades[numero - 1])
        print(f"\n  {actual.ciudad} | {actual.fecha_consulta:%d-%m-%Y} a las {actual.fecha_consulta:%H:%M}")
        print(f"  Ahora: {actual.temperatura} °C | humedad {actual.humedad}% | {actual.estado}")
        print("  → Se puede trabajar en terreno" if actual.es_apto_para_trabajo()
              else "  → NO se recomienda trabajar en terreno ahora")
        self.__repositorios["externos"].guardar_clima(actual)

        if not siguientes:
            print("  (no quedan más horas de pronóstico para hoy)")
            return
        print("\n  Hora  | Temp.    | Humedad | Lluvia | Estado")
        print("  ------+----------+---------+--------+---------------------------")
        for hora in siguientes:
            lluvia = f"{hora.probabilidad_lluvia}%" if hora.probabilidad_lluvia is not None else "-"
            print(f"  {hora.fecha_consulta:%H:%M} | {hora.temperatura:>5.1f} °C | {hora.humedad:>6}% | {lluvia:>6} | {hora.estado}")

    def __consultar_monedas(self):
        print("\n  Moneda | Valor en pesos chilenos | Fecha")
        print("  -------+-------------------------+-----------")
        for codigo in ServicioIndicadores.PRINCIPALES:
            indicador = self.__obtener_indicador(codigo)
            nombre = ServicioIndicadores.NOMBRES[codigo]
            if indicador:
                valor = f"{indicador.valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                print(f"  {nombre:<6} | {'$' + valor:>23} | {indicador.fecha:%d-%m-%Y}")
            else:
                print(f"  {nombre:<6} | {'sin datos':>23} |")

    def __menu_servicios(self):
        self.__exigir(Permiso.CONSULTAR_APIS)
        while True:
            self.__exigir(Permiso.CONSULTAR_APIS)  # en cada vuelta: la sesión pudo expirar dentro del submenú
            print("\n--- Clima y monedas ---\n1. Clima\n2. Monedas\n0. Volver")
            opcion = input("Opción: ").strip()
            try:
                if opcion == "1":
                    self.__consultar_clima()
                elif opcion == "2":
                    self.__consultar_monedas()
                elif opcion == "0":
                    return
                else:
                    print("[WARNING] Opción no válida")
            except ValueError as e:
                print(f"[WARNING] {e}")
            except ErrorServicioExterno as e:
                print(f"[WARNING] {e.mensaje_seguro()}")  # nunca la URL ni el detalle técnico

    # ==================================================================
    # Ciclo principal
    # ==================================================================
    def mostrar_menu(self):
        usuario = self.__usuario_actual()
        print(f"\n===== EcoTech Solutions | {usuario.nombre_usuario} ({usuario.rol}) =====")
        # Se muestran solo las opciones que el rol puede usar
        opciones = [
            ("1", "Proyectos", Permiso.GESTIONAR_PROYECTOS),
            ("2", "Departamentos", Permiso.GESTIONAR_DEPARTAMENTOS),
            ("3", "Empleados y salarios", Permiso.GESTIONAR_EMPLEADOS),
            ("4", "Asignaciones", Permiso.GESTIONAR_PROYECTOS),
            ("5", "Registro de horas", Permiso.REGISTRAR_HORAS),
            ("6", "Usuarios", None),  # None = reservado al rol ADMINISTRADOR
            ("7", "Clima y monedas", Permiso.CONSULTAR_APIS),
        ]
        for numero, texto, permiso in opciones:
            visible = self.__es_administrador() if permiso is None else usuario.tiene_permiso(permiso)
            if visible:
                print(f"{numero}. {texto}")
        print("9. Cerrar sesión\n0. Salir")

    def ejecutar(self):
        if not self.__iniciar_componentes():
            return

        try:
            if self.__repositorios["usuarios"].contar() == 0 and not self.__crear_administrador_inicial():
                print("[ERROR] No se pudo crear el administrador inicial")
                return

            # Trae de internet el clima de las 10 ciudades y las monedas antes del login
            self.__cargar_datos_internet()

            menus = {"1": self.__menu_proyectos, "2": self.__menu_departamentos, "3": self.__menu_empleados,
                     "4": self.__menu_asignaciones, "5": self.__menu_horas, "6": self.__menu_usuarios,
                     "7": self.__menu_servicios}

            while self.__pantalla_login():
                while self.__sesion:
                    if not self.__sesion.esta_activa():
                        print("[WARNING] La sesión expiró (30 minutos). Inicie sesión nuevamente.")
                        self.cerrar_sesion()
                        break

                    self.mostrar_menu()
                    opcion = input("Opción: ").strip()
                    if opcion == "0":
                        print("[INFO] Hasta pronto")
                        return
                    if opcion == "9":
                        self.cerrar_sesion()
                        break
                    if opcion not in menus:
                        print("[WARNING] Opción no válida")
                        continue
                    try:
                        menus[opcion]()
                    except AccesoDenegadoError as e:
                        print(f"[WARNING] {e.mensaje_seguro()}")  # sin revelar rol ni permiso
        except KeyboardInterrupt:
            print("\n[INFO] Programa interrumpido por el usuario")  # Ctrl+C no muestra traceback
        finally:
            self.__conexion.cerrar()  # La conexión se cierra siempre, aunque haya error


if __name__ == "__main__":
    SistemaEcoTech().ejecutar()


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase SistemaEcoTech con conexión única, creación
  del administrador inicial, inicio de sesión, menú filtrado por permisos, CRUD de
  proyectos, departamentos, empleados, asignaciones, horas y usuarios, y consultas a
  las APIs.
- ¿Qué se adoptó?: Menús con if/elif como en la actividad de clases, mensajes
  [INFO]/[WARNING]/[ERROR], confirmación antes de eliminar y cierre de la conexión y
  de la rutina en finally.
- ¿Qué se modificó?: Las contraseñas se piden con getpass (no se ven en pantalla), el
  mensaje de login es genérico (no revela si falló el usuario o la clave), los
  intentos fallidos se guardan en Oracle en cada intento, todas las entradas pasan por
  Validador y por los constructores del modelo, y las excepciones AccesoDenegadoError
  y ErrorServicioExterno se muestran solo con mensaje_seguro().
- ¿Qué se descartó?: Un login que comparaba la contraseña en texto plano (ver abajo).
- Justificación: Cumple el criterio 3.1.2 (solo usuarios autenticados acceden y cada
  opción exige su permiso) sin exponer información sensible en consola.
- Revisión final (22-11), tras evaluar el código contra la rúbrica:
  1. Asignaciones, horas y "asignar empleado a departamento" ahora arman los objetos
     del modelo (Asignacion, RegistroTiempo, Departamento.agregar_empleado) y se los
     pasan al repositorio, en vez de guardar diccionarios. Así las reglas del diagrama
     (RegistroTiempo.__validar, agregación 0..1) se aplican siempre.
  2. Cada submenú vuelve a exigir el permiso en cada vuelta del bucle: antes la
     expiración de 30 minutos solo se revisaba al entrar al submenú.
- Cambio (23-11), a pedido del equipo:
  1. Se eliminó la rutina de las 08:00 (en un computador local casi nunca está abierto
     el programa a esa hora). En su lugar, al iniciar se cargan de internet el clima de
     10 ciudades de Chile y el dólar y el euro (CargaInicial), antes del login.
  2. El menú 7 quedó en "1. Clima" (elegir 1 de 10 ciudades: clima de ahora y pronóstico
     por hora del resto del día) y "2. Monedas" (dólar y euro de una vez). Si la API
     de monedas no responde se usa el último valor guardado en Oracle.
  3. "Listar mis horas" consulta solo las horas del usuario en Oracle (antes traía todas).

Código propuesto por la IA y DESCARTADO:

    usuario = input("Usuario: ")
    clave = input("Contraseña: ")
    cursor.execute(f"select * from usuario where nombre_usuario = '{usuario}' "
                   f"and hash_contrasena = '{clave}'")
    if cursor.fetchone():
        print("Bienvenido")
    else:
        print("El usuario no existe o la contraseña es incorrecta")

Por qué se descartó:
  1. Arma el SQL con f-string: escribiendo  ' or '1'='1  como usuario se entra sin
     contraseña (inyección SQL).
  2. Compara la contraseña en texto plano: obligaría a guardarla sin hash SHA-512.
  3. input() muestra la contraseña en pantalla; getpass() la oculta.
  4. No cuenta intentos fallidos ni bloquea la cuenta (fuerza bruta ilimitada).

    # Versión anterior del registro de horas (descartada en la revisión final)
    horas = self.__pedir_numero(" - Horas trabajadas: ")
    if not Validador.validar_horas(horas): ...
    if fecha > date.today(): ...
    registros.insertar({"id_empleado": id_empleado, "id_proyecto": id_proyecto, ...})

Por qué se descartó: repetía a mano las reglas que ya tiene RegistroTiempo.__validar()
(duplicación de código) y guardaba un diccionario, así que la clase del diagrama no
participaba en el flujo real del programa.
"""
