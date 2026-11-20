# Proyecto
from database.conexion_bd import ConexionBD
from database.repositorio_crud import RepositorioCRUD

# NOTA: mientras las clases de model/ no estén listas, los repositorios reciben
# y devuelven diccionarios cuyas claves son los nombres de las columnas.
# Cuando estén listas, __a_diccionario() pasará a crear el objeto (Proyecto, etc.).


def filas_a_diccionarios(columnas: tuple, filas: list) -> list:
    """ Convierte las tuplas que entrega Oracle en diccionarios {columna: valor} """
    return [dict(zip(columnas, fila)) for fila in filas]


# ---------------------------------------------------------------------------
class RepositorioDepartamento(RepositorioCRUD):
    """ CRUD de la tabla DEPARTAMENTO """

    __COLUMNAS = ("id_departamento", "nombre", "id_gerente")

    def __init__(self, conexion: ConexionBD):
        super().__init__(conexion, "DEPARTAMENTO")

    def __a_diccionario(self, fila):
        return dict(zip(self.__COLUMNAS, fila)) if fila else None

    def insertar(self, departamento: dict) -> int:
        # Si id_gerente no es un empleado existente, Oracle responde ORA-02291
        sql = """
            insert into departamento (nombre, id_gerente)
            values (:nombre, :id_gerente)
            returning id_departamento into :id_generado
        """
        return self._insertar_con_id(sql, {
            "nombre": departamento["nombre"],
            "id_gerente": departamento["id_gerente"],
        })

    def buscar_por_id(self, id: int):
        sql = "select id_departamento, nombre, id_gerente from departamento where id_departamento = :id"
        return self.__a_diccionario(self._consultar_uno(sql, {"id": id}))

    def listar(self) -> list:
        sql = "select id_departamento, nombre, id_gerente from departamento order by nombre"
        return filas_a_diccionarios(self.__COLUMNAS, self._consultar_varios(sql))

    def actualizar(self, departamento: dict) -> bool:
        sql = """
            update departamento set nombre = :nombre, id_gerente = :id_gerente
             where id_departamento = :id_departamento
        """
        return self._modificar(sql, {
            "id_departamento": departamento["id_departamento"],
            "nombre": departamento["nombre"],
            "id_gerente": departamento["id_gerente"],
        })

    def eliminar(self, id: int) -> bool:
        # ON DELETE SET NULL: sus empleados quedan sin departamento
        return self._modificar("delete from departamento where id_departamento = :id", {"id": id})


# ---------------------------------------------------------------------------
class RepositorioEmpleado(RepositorioCRUD):
    """ CRUD de la tabla EMPLEADO. El salario llega YA CIFRADO (bytes) desde ServicioCifrado """

    __COLUMNAS = ("id_empleado", "nombre", "direccion", "telefono", "correo",
                  "fecha_inicio_contrato", "salario_cifrado", "id_departamento")

    def __init__(self, conexion: ConexionBD):
        super().__init__(conexion, "EMPLEADO")

    def __a_diccionario(self, fila):
        return dict(zip(self.__COLUMNAS, fila)) if fila else None

    def insertar(self, empleado: dict) -> int:
        # El correo es único: si se repite, Oracle responde ORA-00001
        sql = """
            insert into empleado (nombre, direccion, telefono, correo,
                                  fecha_inicio_contrato, salario_cifrado, id_departamento)
            values (:nombre, :direccion, :telefono, :correo,
                    :fecha_inicio_contrato, :salario_cifrado, :id_departamento)
            returning id_empleado into :id_generado
        """
        return self._insertar_con_id(sql, {
            "nombre": empleado["nombre"],
            "direccion": empleado.get("direccion"),
            "telefono": empleado.get("telefono"),
            "correo": empleado["correo"],
            "fecha_inicio_contrato": empleado["fecha_inicio_contrato"],
            "salario_cifrado": empleado["salario_cifrado"],  # bytes de Fernet → columna RAW
            "id_departamento": empleado.get("id_departamento"),
        })

    def buscar_por_id(self, id: int):
        sql = f"select {', '.join(self.__COLUMNAS)} from empleado where id_empleado = :id"
        return self.__a_diccionario(self._consultar_uno(sql, {"id": id}))

    def listar(self) -> list:
        sql = f"select {', '.join(self.__COLUMNAS)} from empleado order by nombre"
        return filas_a_diccionarios(self.__COLUMNAS, self._consultar_varios(sql))

    def actualizar(self, empleado: dict) -> bool:
        sql = """
            update empleado
               set nombre = :nombre, direccion = :direccion, telefono = :telefono,
                   correo = :correo, fecha_inicio_contrato = :fecha_inicio_contrato,
                   salario_cifrado = :salario_cifrado, id_departamento = :id_departamento
             where id_empleado = :id_empleado
        """
        return self._modificar(sql, {columna: empleado.get(columna) for columna in self.__COLUMNAS})

    def eliminar(self, id: int) -> bool:
        # Con asignaciones, horas o siendo gerente → ORA-02292 (lo informa _ejecutar)
        # Su USUARIO se borra solo (ON DELETE CASCADE)
        return self._modificar("delete from empleado where id_empleado = :id", {"id": id})


# ---------------------------------------------------------------------------
class RepositorioProyecto(RepositorioCRUD):
    """ CRUD de la tabla PROYECTO """

    __COLUMNAS = ("id_proyecto", "nombre", "descripcion", "fecha_inicio", "pais", "ciudad", "moneda")

    def __init__(self, conexion: ConexionBD):
        super().__init__(conexion, "PROYECTO")

    def __a_diccionario(self, fila):
        return dict(zip(self.__COLUMNAS, fila)) if fila else None

    def insertar(self, proyecto: dict) -> int:
        sql = """
            insert into proyecto (nombre, descripcion, fecha_inicio, pais, ciudad, moneda)
            values (:nombre, :descripcion, :fecha_inicio, :pais, :ciudad, :moneda)
            returning id_proyecto into :id_generado
        """
        return self._insertar_con_id(sql, {
            "nombre": proyecto["nombre"],
            "descripcion": proyecto.get("descripcion"),
            "fecha_inicio": proyecto["fecha_inicio"],
            "pais": proyecto["pais"],
            "ciudad": proyecto["ciudad"],
            "moneda": proyecto["moneda"],
        })

    def buscar_por_id(self, id: int):
        sql = f"select {', '.join(self.__COLUMNAS)} from proyecto where id_proyecto = :id"
        return self.__a_diccionario(self._consultar_uno(sql, {"id": id}))

    def listar(self) -> list:
        # TareaProgramada usa esta lista para saber qué ciudades y monedas consultar
        sql = f"select {', '.join(self.__COLUMNAS)} from proyecto order by id_proyecto"
        return filas_a_diccionarios(self.__COLUMNAS, self._consultar_varios(sql))

    def actualizar(self, proyecto: dict) -> bool:
        sql = """
            update proyecto
               set nombre = :nombre, descripcion = :descripcion, fecha_inicio = :fecha_inicio,
                   pais = :pais, ciudad = :ciudad, moneda = :moneda
             where id_proyecto = :id_proyecto
        """
        return self._modificar(sql, {columna: proyecto.get(columna) for columna in self.__COLUMNAS})

    def eliminar(self, id: int) -> bool:
        # Con asignaciones u horas → ORA-02292. Su DATO_CLIMA se borra solo (CASCADE)
        return self._modificar("delete from proyecto where id_proyecto = :id", {"id": id})


# ---------------------------------------------------------------------------
class RepositorioAsignacion(RepositorioCRUD):
    """ CRUD de la tabla ASIGNACION (empleado ↔ proyecto) """

    __COLUMNAS = ("id_asignacion", "id_empleado", "id_proyecto", "rol_en_proyecto",
                  "fecha_asignacion", "fecha_fin")

    def __init__(self, conexion: ConexionBD):
        super().__init__(conexion, "ASIGNACION")

    def __a_diccionario(self, fila):
        return dict(zip(self.__COLUMNAS, fila)) if fila else None

    def insertar(self, asignacion: dict) -> int:
        sql = """
            insert into asignacion (id_empleado, id_proyecto, rol_en_proyecto, fecha_asignacion, fecha_fin)
            values (:id_empleado, :id_proyecto, :rol_en_proyecto, :fecha_asignacion, :fecha_fin)
            returning id_asignacion into :id_generado
        """
        return self._insertar_con_id(sql, {
            "id_empleado": asignacion["id_empleado"],
            "id_proyecto": asignacion["id_proyecto"],
            "rol_en_proyecto": asignacion.get("rol_en_proyecto"),
            "fecha_asignacion": asignacion["fecha_asignacion"],
            "fecha_fin": asignacion.get("fecha_fin"),
        })

    def buscar_por_id(self, id: int):
        sql = f"select {', '.join(self.__COLUMNAS)} from asignacion where id_asignacion = :id"
        return self.__a_diccionario(self._consultar_uno(sql, {"id": id}))

    def listar(self) -> list:
        sql = f"select {', '.join(self.__COLUMNAS)} from asignacion order by id_asignacion"
        return filas_a_diccionarios(self.__COLUMNAS, self._consultar_varios(sql))

    def listar_por_proyecto(self, id_proyecto: int) -> list:
        """ Empleados asignados a un proyecto (método extra del diagrama) """
        sql = f"select {', '.join(self.__COLUMNAS)} from asignacion where id_proyecto = :id_proyecto"
        return filas_a_diccionarios(self.__COLUMNAS, self._consultar_varios(sql, {"id_proyecto": id_proyecto}))

    def esta_asignado(self, id_empleado: int, id_proyecto: int) -> bool:
        """ True si el empleado tiene una asignación activa (sin fecha_fin) en el proyecto (RF4) """
        sql = """
            select count(*) from asignacion
             where id_empleado = :id_empleado and id_proyecto = :id_proyecto and fecha_fin is null
        """
        fila = self._consultar_uno(sql, {"id_empleado": id_empleado, "id_proyecto": id_proyecto})
        return bool(fila and fila[0] > 0)

    def actualizar(self, asignacion: dict) -> bool:
        # Si fecha_fin < fecha_asignacion, Oracle responde ORA-02290 (CHECK)
        sql = """
            update asignacion
               set rol_en_proyecto = :rol_en_proyecto, fecha_asignacion = :fecha_asignacion,
                   fecha_fin = :fecha_fin
             where id_asignacion = :id_asignacion
        """
        return self._modificar(sql, {
            "id_asignacion": asignacion["id_asignacion"],
            "rol_en_proyecto": asignacion.get("rol_en_proyecto"),
            "fecha_asignacion": asignacion["fecha_asignacion"],
            "fecha_fin": asignacion.get("fecha_fin"),
        })

    def eliminar(self, id: int) -> bool:
        return self._modificar("delete from asignacion where id_asignacion = :id", {"id": id})


# ---------------------------------------------------------------------------
class RepositorioRegistroTiempo(RepositorioCRUD):
    """ CRUD de la tabla REGISTRO_TIEMPO (horas trabajadas) """

    __COLUMNAS = ("id_registro", "id_empleado", "id_proyecto", "fecha", "horas_trabajadas", "descripcion")

    def __init__(self, conexion: ConexionBD):
        super().__init__(conexion, "REGISTRO_TIEMPO")

    def __a_diccionario(self, fila):
        return dict(zip(self.__COLUMNAS, fila)) if fila else None

    def insertar(self, registro: dict) -> int:
        # Horas fuera de 0..24 → ORA-02290 (CHECK). La regla "solo en proyectos donde
        # está asignado" se valida antes con RepositorioAsignacion.esta_asignado()
        sql = """
            insert into registro_tiempo (id_empleado, id_proyecto, fecha, horas_trabajadas, descripcion)
            values (:id_empleado, :id_proyecto, :fecha, :horas_trabajadas, :descripcion)
            returning id_registro into :id_generado
        """
        return self._insertar_con_id(sql, {
            "id_empleado": registro["id_empleado"],
            "id_proyecto": registro["id_proyecto"],
            "fecha": registro["fecha"],
            "horas_trabajadas": registro["horas_trabajadas"],
            "descripcion": registro.get("descripcion"),
        })

    def buscar_por_id(self, id: int):
        sql = f"select {', '.join(self.__COLUMNAS)} from registro_tiempo where id_registro = :id"
        return self.__a_diccionario(self._consultar_uno(sql, {"id": id}))

    def listar(self) -> list:
        sql = f"select {', '.join(self.__COLUMNAS)} from registro_tiempo order by fecha desc"
        return filas_a_diccionarios(self.__COLUMNAS, self._consultar_varios(sql))

    def total_horas_proyecto(self, id_proyecto: int) -> float:
        """ Suma de horas registradas en un proyecto (apoya Proyecto.calcular_horas_totales) """
        sql = "select nvl(sum(horas_trabajadas), 0) from registro_tiempo where id_proyecto = :id_proyecto"
        fila = self._consultar_uno(sql, {"id_proyecto": id_proyecto})
        return float(fila[0]) if fila else 0.0

    def actualizar(self, registro: dict) -> bool:
        sql = """
            update registro_tiempo
               set fecha = :fecha, horas_trabajadas = :horas_trabajadas, descripcion = :descripcion
             where id_registro = :id_registro
        """
        return self._modificar(sql, {
            "id_registro": registro["id_registro"],
            "fecha": registro["fecha"],
            "horas_trabajadas": registro["horas_trabajadas"],
            "descripcion": registro.get("descripcion"),
        })

    def eliminar(self, id: int) -> bool:
        return self._modificar("delete from registro_tiempo where id_registro = :id", {"id": id})


# ---------------------------------------------------------------------------
class RepositorioUsuario(RepositorioCRUD):
    """ CRUD de la tabla USUARIO. La contraseña llega YA HASHEADA (bcrypt) desde ServicioCifrado """

    __COLUMNAS = ("id_usuario", "nombre_usuario", "hash_contrasena", "intentos_fallidos",
                  "bloqueado", "rol", "id_empleado")

    def __init__(self, conexion: ConexionBD):
        super().__init__(conexion, "USUARIO")

    def __a_diccionario(self, fila):
        return dict(zip(self.__COLUMNAS, fila)) if fila else None

    def insertar(self, usuario: dict) -> int:
        # rol fuera de ADMINISTRADOR/GERENTE/EMPLEADO → ORA-02290 (CHECK)
        sql = """
            insert into usuario (nombre_usuario, hash_contrasena, rol, id_empleado)
            values (:nombre_usuario, :hash_contrasena, :rol, :id_empleado)
            returning id_usuario into :id_generado
        """
        return self._insertar_con_id(sql, {
            "nombre_usuario": usuario["nombre_usuario"],
            "hash_contrasena": usuario["hash_contrasena"],
            "rol": usuario["rol"],
            "id_empleado": usuario["id_empleado"],
        })

    def buscar_por_id(self, id: int):
        sql = f"select {', '.join(self.__COLUMNAS)} from usuario where id_usuario = :id"
        return self.__a_diccionario(self._consultar_uno(sql, {"id": id}))

    def buscar_por_nombre(self, nombre_usuario: str):
        """ Usado en el inicio de sesión """
        sql = f"select {', '.join(self.__COLUMNAS)} from usuario where nombre_usuario = :nombre_usuario"
        return self.__a_diccionario(self._consultar_uno(sql, {"nombre_usuario": nombre_usuario}))

    def listar(self) -> list:
        # No se selecciona hash_contrasena: para listar no se necesita
        columnas = ("id_usuario", "nombre_usuario", "intentos_fallidos", "bloqueado", "rol", "id_empleado")
        sql = f"select {', '.join(columnas)} from usuario order by nombre_usuario"
        return filas_a_diccionarios(columnas, self._consultar_varios(sql))

    def actualizar(self, usuario: dict) -> bool:
        sql = """
            update usuario
               set nombre_usuario = :nombre_usuario, hash_contrasena = :hash_contrasena, rol = :rol
             where id_usuario = :id_usuario
        """
        return self._modificar(sql, {
            "id_usuario": usuario["id_usuario"],
            "nombre_usuario": usuario["nombre_usuario"],
            "hash_contrasena": usuario["hash_contrasena"],
            "rol": usuario["rol"],
        })

    def actualizar_intentos(self, id_usuario: int, intentos_fallidos: int, bloqueado: bool) -> bool:
        """ Guarda los intentos fallidos y el bloqueo (3 intentos → bloqueado) (RF8) """
        sql = """
            update usuario set intentos_fallidos = :intentos, bloqueado = :bloqueado
             where id_usuario = :id_usuario
        """
        return self._modificar(sql, {
            "id_usuario": id_usuario,
            "intentos": intentos_fallidos,
            "bloqueado": 1 if bloqueado else 0,  # Oracle no tiene booleano: se guarda 0/1
        })

    def eliminar(self, id: int) -> bool:
        return self._modificar("delete from usuario where id_usuario = :id", {"id": id})


# ---------------------------------------------------------------------------
class RepositorioDatoExterno(RepositorioCRUD):
    """
    Guarda lo que traen las APIs en DATO_CLIMA e INDICADOR_ECONOMICO.
    Los métodos del CRUD base trabajan sobre DATO_CLIMA; los indicadores
    tienen sus propios métodos (guardar_indicador, buscar_indicador).
    """

    __COLUMNAS_CLIMA = ("id_clima", "id_proyecto", "ciudad", "temperatura", "humedad",
                        "estado", "fecha_consulta")
    __COLUMNAS_INDICADOR = ("id_indicador", "codigo", "valor", "fecha")

    def __init__(self, conexion: ConexionBD):
        super().__init__(conexion, "DATO_EXTERNO")

    # --- DATO_CLIMA ---
    def insertar(self, dato_clima: dict) -> int:
        return self.guardar_clima(dato_clima)

    def guardar_clima(self, dato_clima: dict) -> int:
        # Humedad fuera de 0..100 → ORA-02290. fecha_consulta la pone Oracle (SYSTIMESTAMP)
        sql = """
            insert into dato_clima (id_proyecto, ciudad, temperatura, humedad, estado)
            values (:id_proyecto, :ciudad, :temperatura, :humedad, :estado)
            returning id_clima into :id_generado
        """
        return self._insertar_con_id(sql, {
            "id_proyecto": dato_clima["id_proyecto"],
            "ciudad": dato_clima["ciudad"],
            "temperatura": dato_clima.get("temperatura"),
            "humedad": dato_clima.get("humedad"),
            "estado": dato_clima.get("estado"),
        })

    def buscar_por_id(self, id: int):
        sql = f"select {', '.join(self.__COLUMNAS_CLIMA)} from dato_clima where id_clima = :id"
        fila = self._consultar_uno(sql, {"id": id})
        return dict(zip(self.__COLUMNAS_CLIMA, fila)) if fila else None

    def listar(self) -> list:
        sql = f"select {', '.join(self.__COLUMNAS_CLIMA)} from dato_clima order by fecha_consulta desc"
        return filas_a_diccionarios(self.__COLUMNAS_CLIMA, self._consultar_varios(sql))

    def ultimo_clima_proyecto(self, id_proyecto: int):
        """ Lectura de clima más reciente de un proyecto """
        sql = f"""
            select {', '.join(self.__COLUMNAS_CLIMA)} from dato_clima
             where id_proyecto = :id_proyecto
             order by fecha_consulta desc fetch first 1 row only
        """
        fila = self._consultar_uno(sql, {"id_proyecto": id_proyecto})
        return dict(zip(self.__COLUMNAS_CLIMA, fila)) if fila else None

    def actualizar(self, dato_clima: dict) -> bool:
        sql = """
            update dato_clima set temperatura = :temperatura, humedad = :humedad, estado = :estado
             where id_clima = :id_clima
        """
        return self._modificar(sql, {
            "id_clima": dato_clima["id_clima"],
            "temperatura": dato_clima.get("temperatura"),
            "humedad": dato_clima.get("humedad"),
            "estado": dato_clima.get("estado"),
        })

    def eliminar(self, id: int) -> bool:
        return self._modificar("delete from dato_clima where id_clima = :id", {"id": id})

    # --- INDICADOR_ECONOMICO ---
    def guardar_indicador(self, indicador: dict) -> bool:
        """
        Guarda el valor del día SOLO si no existe ese código para esa fecha (UQ1).
        Retorna True si lo insertó, False si ya estaba. Así la rutina de las 08:00
        puede ejecutarse varias veces sin duplicar ni mostrar errores.
        """
        sql = """
            merge into indicador_economico destino
            using (select :codigo codigo, trunc(:fecha) fecha, :valor valor from dual) origen
               on (destino.codigo = origen.codigo and destino.fecha = origen.fecha)
            when not matched then
                insert (codigo, valor, fecha) values (origen.codigo, origen.valor, origen.fecha)
        """
        cursor = self._ejecutar(sql, {
            "codigo": indicador["codigo"],
            "fecha": indicador["fecha"],
            "valor": indicador["valor"],
        })
        if not cursor:
            return False

        insertado = cursor.rowcount > 0
        cursor.close()
        print(f"[INFO] Indicador {indicador['codigo']} "
              f"{'guardado' if insertado else 'ya existía para esa fecha'}")
        return insertado

    def buscar_indicador(self, codigo: str, fecha):
        """ Valor de una moneda en una fecha (para calcular pagos internacionales) """
        sql = f"""
            select {', '.join(self.__COLUMNAS_INDICADOR)} from indicador_economico
             where codigo = :codigo and fecha = trunc(:fecha)
        """
        fila = self._consultar_uno(sql, {"codigo": codigo, "fecha": fecha})
        return dict(zip(self.__COLUMNAS_INDICADOR, fila)) if fila else None

    def listar_indicadores(self) -> list:
        sql = f"select {', '.join(self.__COLUMNAS_INDICADOR)} from indicador_economico order by fecha desc, codigo"
        return filas_a_diccionarios(self.__COLUMNAS_INDICADOR, self._consultar_varios(sql))


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: Los 7 repositorios concretos que heredan de
  RepositorioCRUD, con el SQL parametrizado de cada tabla y métodos extra del
  diagrama/manual (listar_por_proyecto, buscar_por_nombre, actualizar_intentos,
  guardar_clima, guardar_indicador).
- ¿Qué se adoptó?: Un repositorio por tabla, SQL con parámetros :nombre y uso de los
  métodos heredados (_insertar_con_id, _consultar_uno, _consultar_varios, _modificar).
- ¿Qué se modificó?: Se agregaron esta_asignado() (RF4: solo registrar horas en
  proyectos asignados) y total_horas_proyecto(); en RepositorioUsuario.listar() se
  quitó hash_contrasena porque no se necesita para listar.
- ¿Qué se descartó?: La primera versión de guardar_indicador (ver abajo).
- Justificación: Separar el SQL del dominio (patrón Repositorio) cumple el principio de
  responsabilidad única y permite que model/ no conozca a Oracle.

Código propuesto por la IA y DESCARTADO (guardar_indicador):

    def guardar_indicador(self, indicador: dict) -> bool:
        sql = "insert into indicador_economico (codigo, valor, fecha) values (:codigo, :valor, :fecha)"
        try:
            cursor = self._conexion.obtener_cursor()
            cursor.execute(sql, indicador)
            self._conexion.confirmar()
            return True
        except oracledb.IntegrityError as e:
            if e.args[0].code == 1:      # ORA-00001: ya existe → se ignora
                self._conexion.revertir()
                return False
            raise

Por qué se descartó:
  1. Usa el error como control de flujo: cada mañana se "provoca" un ORA-00001 a
     propósito, y en el registro de la BD queda como un error que no lo es.
  2. Repite el try/except que ya resuelve _ejecutar() en la clase padre.
  3. MERGE ... WHEN NOT MATCHED hace la verificación y la inserción en UNA sola
     sentencia atómica dentro de Oracle, sin error ni ventana de carrera.
"""
