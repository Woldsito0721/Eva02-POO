"""
Prueba de las clases de model/ (no usa la base de datos).
Ejecutar desde la raíz del proyecto:  python -m test.prueba_modelos
"""

# Python
from datetime import date, timedelta

# Librerías
from cryptography.fernet import Fernet

# Proyecto
from model.asignacion import Asignacion
from model.dato_clima import DatoClima
from model.departamento import Departamento
from model.empleado import Empleado
from model.indicador_economico import IndicadorEconomico
from model.proyecto import Proyecto
from model.rol import Permiso, Rol
from model.usuario import Usuario
from security.servicio_cifrado import ServicioCifrado
from security.sesion import AccesoDenegadoError, Sesion

resultados = {"ok": 0, "fallo": 0}


def verificar(descripcion: str, condicion: bool):
    if condicion:
        resultados["ok"] += 1
        print(f"  [OK] {descripcion}")
    else:
        resultados["fallo"] += 1
        print(f"  [FALLO] {descripcion}")


def lanza_error(funcion, tipo_error=ValueError) -> bool:
    """ True si la función lanza el error esperado """
    try:
        funcion()
        return False
    except tipo_error:
        return True


def ejecutar_pruebas():
    # Clave de prueba: no depende del .env
    cifrado = ServicioCifrado(Fernet.generate_key())

    print("\n1. ROL Y PERMISO")
    admin_rol = Rol.desde_nombre("administrador")
    empleado_rol = Rol.desde_nombre("EMPLEADO")
    verificar("ADMINISTRADOR concede VER_SALARIOS", admin_rol.concede(Permiso.VER_SALARIOS))
    verificar("EMPLEADO no concede VER_SALARIOS", not empleado_rol.concede(Permiso.VER_SALARIOS))
    verificar("rol inexistente rechazado", lanza_error(lambda: Rol.desde_nombre("JEFE")))

    print("\n2. EMPLEADO")
    ana = Empleado.crear("Ana Soto", "Av. Costanera 123", "+56 9 1234 5678", "ana@ecotech.cl",
                         date(2025, 3, 1), 1200000, cifrado)
    verificar("salario se guarda cifrado (bytes, no el número)",
              isinstance(ana.salario_cifrado, bytes) and b"1200000" not in ana.salario_cifrado)
    verificar("correo inválido rechazado", lanza_error(lambda: Empleado.crear(
        "X", None, None, "no-es-correo", date.today(), 1000, cifrado)))
    verificar("salario 0 rechazado", lanza_error(lambda: Empleado.crear(
        "X", None, None, "x@x.cl", date.today(), 0, cifrado)))

    print("\n3. USUARIO, SESION Y SALARIO")
    admin = Usuario.crear("admin", "Clave_Segura1", admin_rol, id_empleado=1)
    pedro = Usuario.crear("pedro", "Clave_Segura2", empleado_rol, id_empleado=2)
    verificar("hash SHA-512 con sal, no texto plano", admin.hash_contrasena.startswith("pbkdf2_sha512$"))
    verificar("autenticar con clave correcta", admin.autenticar("Clave_Segura1"))
    verificar("admin ve el salario", ana.obtener_salario(admin, cifrado) == 1200000.0)
    verificar("empleado NO ve el salario (AccesoDenegadoError)",
              lanza_error(lambda: ana.obtener_salario(pedro, cifrado), AccesoDenegadoError))
    sesion = Sesion(pedro)
    verificar("Sesion.exigir_permiso bloquea sin permiso",
              lanza_error(lambda: sesion.exigir_permiso(Permiso.GESTIONAR_PROYECTOS), AccesoDenegadoError))
    for _ in range(3):
        pedro.autenticar("incorrecta")
    verificar("3 intentos fallidos → bloqueado", pedro.bloqueado)
    verificar("bloqueado no entra ni con la clave correcta", not pedro.autenticar("Clave_Segura2"))
    verificar("bloqueado pierde sus permisos", not pedro.tiene_permiso(Permiso.REGISTRAR_HORAS))

    print("\n4. DEPARTAMENTO")
    luis = Empleado.crear("Luis Rojas", None, None, "luis@ecotech.cl", date(2024, 1, 2), 900000, cifrado)
    energia = Departamento("Energía", gerente=luis)
    agua = Departamento("Agua", gerente=luis)
    energia.agregar_empleado(ana)
    agua.agregar_empleado(ana)
    verificar("empleado está en un solo departamento (0..1)",
              ana.departamento is agua and ana not in energia.empleados)
    verificar("lista de empleados es de solo lectura", isinstance(agua.empleados, tuple))

    print("\n5. PROYECTO, ASIGNACION Y HORAS")
    solar = Proyecto("Parque Solar", "Paneles", date(2026, 1, 10), "Chile", "Puerto Montt", "clp")
    verificar("moneda se normaliza a mayúsculas", solar.moneda == "CLP")
    verificar("moneda inválida rechazada", lanza_error(lambda: Proyecto(
        "P", None, date.today(), "Chile", "Osorno", "PESOS")))
    verificar("ciudad con símbolos rechazada (se envía a la API)", lanza_error(lambda: Proyecto(
        "P", None, date.today(), "Chile", "Osorno&lat=0", "CLP")))
    verificar("no asignado no puede registrar horas",
              lanza_error(lambda: ana.registrar_horas(solar, date.today(), 8)))
    solar.asignar_empleado(ana, "Técnica")
    verificar("doble asignación rechazada", lanza_error(lambda: solar.asignar_empleado(ana)))
    ana.registrar_horas(solar, date.today(), 7.5, "Instalación")
    ana.registrar_horas(solar, date.today(), 2)
    verificar("calcular_horas_totales = 9.5", solar.calcular_horas_totales() == 9.5)
    verificar("25 horas rechazadas", lanza_error(lambda: ana.registrar_horas(solar, date.today(), 25)))
    verificar("fecha futura rechazada",
              lanza_error(lambda: ana.registrar_horas(solar, date.today() + timedelta(days=1), 3)))
    solar.desasignar_empleado(ana)
    verificar("desasignar finaliza (conserva historial)",
              not solar.tiene_asignado(ana) and len(solar.asignaciones) == 1)
    verificar("fecha_fin anterior rechazada", lanza_error(lambda: Asignacion(
        ana, solar, None, date(2026, 5, 1), date(2026, 1, 1))))

    print("\n6. DATO_CLIMA E INDICADOR")
    verificar("clima templado es apto", DatoClima("Osorno", 14, 80, "Nublado").es_apto_para_trabajo())
    verificar("tormenta no es apta", not DatoClima("Osorno", 14, 80, "Tormenta eléctrica").es_apto_para_trabajo())
    verificar("humedad 120 rechazada", lanza_error(lambda: DatoClima("Osorno", 14, 120, "Nublado")))
    dolar = IndicadorEconomico("usd", 1008.79, date.today())
    verificar("1.000.000 CLP = 991.29 USD", dolar.convertir_desde_clp(1000000) == 991.29)
    verificar("pago de Ana en USD (admin)",
              ana.calcular_pago_en_moneda(admin, dolar, cifrado) == round(1200000 / 1008.79, 2))
    verificar("valor 0 rechazado (división por cero)",
              lanza_error(lambda: IndicadorEconomico("USD", 0, date.today())))


if __name__ == "__main__":
    print("--- Prueba de modelos EcoTech ---")
    ejecutar_pruebas()
    print(f"\n--- Resultado: {resultados['ok']} OK, {resultados['fallo']} FALLO ---")


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: Un recorrido por las 9 clases de model/ que verifica
  reglas de negocio, validaciones y la integración con Sesion y ServicioCifrado.
- ¿Qué se adoptó?: Usar una clave Fernet generada en la prueba, para no depender del
  .env ni tocar la base de datos.
- ¿Qué se descartó?: Comprobar los errores con un try/except en cada caso (ver abajo).

Código propuesto por la IA y DESCARTADO:

    try:
        Rol.desde_nombre("JEFE")
        print("[FALLO] rol inexistente aceptado")
    except ValueError:
        print("[OK] rol inexistente rechazado")

Por qué se descartó: repetido 15 veces el archivo sería tres veces más largo. La
función lanza_error() hace lo mismo una sola vez y cada prueba queda en una línea.
"""
