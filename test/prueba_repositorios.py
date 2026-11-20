"""
Prueba de los 7 repositorios contra Oracle FreeSQL.
Ejecutar desde la raíz del proyecto:  python -m test.prueba_repositorios

Crea datos de prueba, verifica el CRUD y las reglas de integridad, y al final
BORRA todo lo que creó (las tablas quedan como estaban).
"""

# Python
from datetime import date

# Proyecto
from database.conexion_bd import ConexionBD
from database.repositorios import (
    RepositorioAsignacion, RepositorioDatoExterno, RepositorioDepartamento,
    RepositorioEmpleado, RepositorioProyecto, RepositorioRegistroTiempo, RepositorioUsuario,
)

resultados = {"ok": 0, "fallo": 0}


def verificar(descripcion: str, condicion: bool):
    """ Muestra [OK] o [FALLO] y lleva la cuenta """
    if condicion:
        resultados["ok"] += 1
        print(f"  [OK] {descripcion}")
    else:
        resultados["fallo"] += 1
        print(f"  [FALLO] {descripcion}")


def ejecutar_pruebas(bd: ConexionBD):
    proyectos = RepositorioProyecto(bd)
    empleados = RepositorioEmpleado(bd)
    departamentos = RepositorioDepartamento(bd)
    asignaciones = RepositorioAsignacion(bd)
    registros = RepositorioRegistroTiempo(bd)
    usuarios = RepositorioUsuario(bd)
    externos = RepositorioDatoExterno(bd)

    print("\n1. PROYECTO")
    id_proyecto = proyectos.insertar({
        "nombre": "PRUEBA Parque Solar", "descripcion": "Dato de prueba",
        "fecha_inicio": date(2026, 11, 20), "pais": "Chile", "ciudad": "Puerto Montt", "moneda": "CLP",
    })
    verificar("insertar devuelve id", id_proyecto > 0)
    proyecto = proyectos.buscar_por_id(id_proyecto)
    proyecto["ciudad"] = "Osorno"
    verificar("actualizar", proyectos.actualizar(proyecto))
    verificar("buscar refleja el cambio", proyectos.buscar_por_id(id_proyecto)["ciudad"] == "Osorno")
    verificar("listar lo incluye", any(p["id_proyecto"] == id_proyecto for p in proyectos.listar()))

    print("\n2. EMPLEADO")
    id_empleado = empleados.insertar({
        "nombre": "PRUEBA Ana Soto", "correo": "prueba.ana@ecotech.cl",
        "fecha_inicio_contrato": date(2026, 1, 5),
        "salario_cifrado": b"salario-cifrado-de-prueba",  # en el sistema real lo cifra ServicioCifrado
    })
    verificar("insertar devuelve id", id_empleado > 0)
    verificar("salario se guarda como bytes",
              empleados.buscar_por_id(id_empleado)["salario_cifrado"] == b"salario-cifrado-de-prueba")
    print("  (se espera un WARNING de dato duplicado)")
    verificar("correo duplicado rechazado (ORA-00001)", empleados.insertar({
        "nombre": "Otra", "correo": "prueba.ana@ecotech.cl",
        "fecha_inicio_contrato": date(2026, 1, 5), "salario_cifrado": b"x",
    }) == 0)

    print("\n3. DEPARTAMENTO")
    id_departamento = departamentos.insertar({"nombre": "PRUEBA Energía", "id_gerente": id_empleado})
    verificar("insertar con gerente existente", id_departamento > 0)
    print("  (se espera un WARNING de clave foránea)")
    verificar("gerente inexistente rechazado (ORA-02291)",
              departamentos.insertar({"nombre": "PRUEBA Otro", "id_gerente": 999999}) == 0)
    empleado = empleados.buscar_por_id(id_empleado)
    empleado["id_departamento"] = id_departamento
    verificar("asignar empleado al departamento", empleados.actualizar(empleado))

    print("\n4. ASIGNACION")
    id_asignacion = asignaciones.insertar({
        "id_empleado": id_empleado, "id_proyecto": id_proyecto,
        "rol_en_proyecto": "Técnico", "fecha_asignacion": date(2026, 11, 20),
    })
    verificar("insertar", id_asignacion > 0)
    verificar("esta_asignado = True", asignaciones.esta_asignado(id_empleado, id_proyecto))
    verificar("listar_por_proyecto", len(asignaciones.listar_por_proyecto(id_proyecto)) == 1)
    print("  (se espera un WARNING de CHECK)")
    verificar("fecha_fin anterior rechazada (ORA-02290)", not asignaciones.actualizar({
        "id_asignacion": id_asignacion, "fecha_asignacion": date(2026, 11, 20), "fecha_fin": date(2026, 1, 1),
    }))

    print("\n5. REGISTRO_TIEMPO")
    id_registro = registros.insertar({
        "id_empleado": id_empleado, "id_proyecto": id_proyecto,
        "fecha": date(2026, 11, 20), "horas_trabajadas": 7.5, "descripcion": "Instalación",
    })
    verificar("insertar", id_registro > 0)
    verificar("total_horas_proyecto = 7.5", registros.total_horas_proyecto(id_proyecto) == 7.5)
    print("  (se espera un WARNING de CHECK)")
    verificar("25 horas rechazadas (ORA-02290)", registros.insertar({
        "id_empleado": id_empleado, "id_proyecto": id_proyecto,
        "fecha": date(2026, 11, 21), "horas_trabajadas": 25,
    }) == 0)
    print("  (se espera un WARNING de registros asociados)")
    verificar("borrar empleado con horas rechazado (ORA-02292)", not empleados.eliminar(id_empleado))

    print("\n6. USUARIO")
    id_usuario = usuarios.insertar({
        "nombre_usuario": "prueba_ana", "hash_contrasena": "hash-de-prueba",
        "rol": "EMPLEADO", "id_empleado": id_empleado,
    })
    verificar("insertar", id_usuario > 0)
    verificar("buscar_por_nombre", usuarios.buscar_por_nombre("prueba_ana")["id_usuario"] == id_usuario)
    verificar("actualizar_intentos (bloquear)", usuarios.actualizar_intentos(id_usuario, 3, True))
    verificar("queda bloqueado", usuarios.buscar_por_id(id_usuario)["bloqueado"] == 1)
    verificar("listar no expone el hash", "hash_contrasena" not in usuarios.listar()[0])

    print("\n7. DATO_EXTERNO")
    id_clima = externos.guardar_clima({
        "id_proyecto": id_proyecto, "ciudad": "Osorno", "temperatura": 14.5, "humedad": 80, "estado": "Nublado",
    })
    verificar("guardar_clima", id_clima > 0)
    verificar("ultimo_clima_proyecto", externos.ultimo_clima_proyecto(id_proyecto)["id_clima"] == id_clima)
    hoy = date.today()
    verificar("guardar_indicador primera vez = True",
              externos.guardar_indicador({"codigo": "ZZZ", "valor": 950.25, "fecha": hoy}))
    verificar("guardar_indicador repetido = False (sin error)",
              not externos.guardar_indicador({"codigo": "ZZZ", "valor": 951.00, "fecha": hoy}))
    verificar("buscar_indicador", float(externos.buscar_indicador("ZZZ", hoy)["valor"]) == 950.25)

    print("\n8. LIMPIEZA")
    verificar("eliminar registro de tiempo", registros.eliminar(id_registro))
    verificar("eliminar asignación", asignaciones.eliminar(id_asignacion))
    verificar("eliminar departamento (empleado queda sin depto)", departamentos.eliminar(id_departamento))
    verificar("ON DELETE SET NULL", empleados.buscar_por_id(id_empleado)["id_departamento"] is None)
    verificar("eliminar empleado (borra su usuario en cascada)", empleados.eliminar(id_empleado))
    verificar("ON DELETE CASCADE usuario", usuarios.buscar_por_id(id_usuario) is None)
    verificar("eliminar proyecto (borra su clima en cascada)", proyectos.eliminar(id_proyecto))
    verificar("ON DELETE CASCADE clima", externos.buscar_por_id(id_clima) is None)
    cursor = bd.obtener_cursor()
    cursor.execute("delete from indicador_economico where codigo = 'ZZZ'")
    bd.confirmar()
    cursor.close()


if __name__ == "__main__":
    print("--- Prueba de repositorios EcoTech ---")
    bd = ConexionBD()  # Sin "with" para que haya un solo intento de conexión

    try:
        if bd.conectar():
            ejecutar_pruebas(bd)
            print(f"\n--- Resultado: {resultados['ok']} OK, {resultados['fallo']} FALLO ---")
        else:
            print("[FALLO] Sin conexión: revisar el .env (python -m test.prueba_conexion)")
    finally:
        bd.cerrar()


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: Un recorrido por los 7 repositorios que inserta, busca,
  actualiza y elimina datos marcados como "PRUEBA", y luego los borra.
- ¿Qué se adoptó?: Probar también las reglas que debe rechazar Oracle (ORA-00001,
  02290, 02291, 02292) y las políticas ON DELETE del modelo entidad-relación.
- ¿Qué se modificó?: La limpieza se hace en orden inverso a las claves foráneas para
  no dejar datos de prueba en la BD del evaluador.
- ¿Qué se descartó?: Borrar todo con TRUNCATE al final (ver abajo).

Código propuesto por la IA y DESCARTADO:

    for tabla in ("registro_tiempo", "asignacion", "usuario", "dato_clima",
                  "indicador_economico", "departamento", "empleado", "proyecto"):
        cursor.execute(f"truncate table {tabla}")

Por qué se descartó: TRUNCATE borra TODOS los datos de la tabla, incluidos los reales
que el profesor o el equipo hayan cargado, y no se puede deshacer con rollback. La
prueba solo debe borrar lo que ella misma creó.
"""
