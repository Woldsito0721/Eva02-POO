from __future__ import annotations

# Python
from datetime import date
from typing import TYPE_CHECKING, Callable

# Proyecto
from model.empleado import Empleado
from model.rol import Permiso
from report.informe import Informe
from security.sesion import AccesoDenegadoError

if TYPE_CHECKING:
    from model.indicador_economico import IndicadorEconomico
    from model.usuario import Usuario
    from security.servicio_cifrado import ServicioCifrado


class GeneradorInformes():
    """ Arma los 6 informes del menú de reportes a partir de los repositorios """

    # (número del menú, título) — el orden es el que ve el usuario
    INFORMES = (
        ("1", "Horas por proyecto"),
        ("2", "Horas de un empleado"),
        ("3", "Empleados por departamento"),
        ("4", "Asignaciones de un proyecto"),
        ("5", "Clima e indicadores guardados"),
        ("6", "Pagos en moneda extranjera"),
    )

    def __init__(self, repositorios: dict, cifrado: ServicioCifrado):
        self.__repositorios = repositorios
        self.__cifrado = cifrado

    # 1 ----------------------------------------------------------------
    def horas_por_proyecto(self, usuario: Usuario) -> Informe:
        filas, total_proyecto, proyecto_actual = [], 0.0, None
        for fila in self.__repositorios["registros"].horas_por_proyecto():
            if proyecto_actual is not None and fila["proyecto"] != proyecto_actual:
                filas.append((proyecto_actual, "TOTAL DEL PROYECTO", total_proyecto))
                total_proyecto = 0.0
            proyecto_actual = fila["proyecto"]
            total_proyecto += float(fila["horas"])
            filas.append((fila["proyecto"], fila["empleado"], float(fila["horas"])))
        if proyecto_actual is not None:
            filas.append((proyecto_actual, "TOTAL DEL PROYECTO", total_proyecto))

        return Informe("Horas por proyecto", ["Proyecto", "Empleado", "Horas"], filas,
                       usuario.nombre_usuario, "horas_por_proyecto")

    # 2 ----------------------------------------------------------------
    def horas_de_empleado(self, usuario: Usuario, id_empleado: int, desde: date, hasta: date) -> Informe:
        if hasta < desde:
            raise ValueError("La fecha final no puede ser anterior a la inicial")
        fila_empleado = self.__repositorios["empleados"].buscar_por_id(id_empleado)
        if not fila_empleado:
            raise ValueError("Empleado no encontrado")

        registros = self.__repositorios["registros"].horas_de_empleado(id_empleado, desde, hasta)
        filas = [(r["fecha"], r["proyecto"], float(r["horas"]), r["descripcion"]) for r in registros]
        if filas:
            filas.append(("", "TOTAL", sum(f[2] for f in filas), ""))

        return Informe("Horas de un empleado", ["Fecha", "Proyecto", "Horas", "Descripción"], filas,
                       usuario.nombre_usuario, "horas_empleado",
                       subtitulo=f"{fila_empleado['nombre']} | del {desde:%d-%m-%Y} al {hasta:%d-%m-%Y}")

    # 3 ----------------------------------------------------------------
    def empleados_por_departamento(self, usuario: Usuario) -> Informe:
        filas = [(f["departamento"], f["gerente"], f["empleado"] or "(sin empleados)", f["correo"])
                 for f in self.__repositorios["empleados"].empleados_por_departamento()]
        return Informe("Empleados por departamento", ["Departamento", "Gerente", "Empleado", "Correo"],
                       filas, usuario.nombre_usuario, "empleados_por_departamento")

    # 4 ----------------------------------------------------------------
    def asignaciones_de_proyecto(self, usuario: Usuario, id_proyecto: int) -> Informe:
        fila_proyecto = self.__repositorios["proyectos"].buscar_por_id(id_proyecto)
        if not fila_proyecto:
            raise ValueError("Proyecto no encontrado")

        hoy = date.today()
        filas = []
        for a in self.__repositorios["asignaciones"].detalle_por_proyecto(id_proyecto):
            fin = a["fecha_fin"].date() if a["fecha_fin"] else None
            estado = "Activa" if fin is None or fin > hoy else "Finalizada"  # misma regla que Asignacion
            filas.append((a["empleado"], a["rol_en_proyecto"] or "sin rol", a["fecha_asignacion"],
                          a["fecha_fin"], estado))

        return Informe("Asignaciones de un proyecto",
                       ["Empleado", "Rol en el proyecto", "Asignado el", "Finalizó el", "Estado"], filas,
                       usuario.nombre_usuario, "asignaciones_proyecto",
                       subtitulo=f"Proyecto {fila_proyecto['nombre']} ({fila_proyecto['ciudad']})")

    # 5 ----------------------------------------------------------------
    def clima_e_indicadores(self, usuario: Usuario) -> Informe:
        externos = self.__repositorios["externos"]
        filas = []
        for c in externos.ultimo_clima_por_ciudad():
            detalle = f"{c['temperatura']} °C, {c['humedad']}% humedad"
            filas.append(("Clima", c["ciudad"], detalle, c["estado"], c["fecha_consulta"]))
        for i in externos.listar_indicadores():
            filas.append(("Moneda", i["codigo"], f"{Informe.formatear(float(i['valor']))} CLP", "", i["fecha"]))

        return Informe("Clima e indicadores guardados", ["Tipo", "Ciudad / Moneda", "Valor", "Estado", "Fecha"],
                       filas, usuario.nombre_usuario, "clima_e_indicadores")

    # 6 ----------------------------------------------------------------
    def pagos_en_moneda(self, usuario: Usuario,
                        obtener_indicador: Callable[[str], IndicadorEconomico | None]) -> Informe:
        """ Descifra salarios: exige VER_SALARIOS (solo ADMINISTRADOR) """
        if not usuario.tiene_permiso(Permiso.VER_SALARIOS):
            raise AccesoDenegadoError("Informe de pagos sin permiso VER_SALARIOS")

        indicadores = {codigo: obtener_indicador(codigo) for codigo in ("USD", "EUR", "CLF")}
        filas = []
        for fila in self.__repositorios["empleados"].listar():
            empleado = Empleado(fila["nombre"], fila["direccion"], fila["telefono"], fila["correo"],
                                fila["fecha_inicio_contrato"], bytes(fila["salario_cifrado"]),
                                id_empleado=fila["id_empleado"])
            salario = empleado.obtener_salario(usuario, self.__cifrado)  # vuelve a revisar el permiso
            convertidos = [indicador.convertir_desde_clp(salario) if indicador else None
                           for indicador in indicadores.values()]
            filas.append((empleado.nombre, salario, *convertidos))

        valores = " | ".join(f"1 {codigo} = {Informe.formatear(ind.valor)} CLP ({ind.fecha:%d-%m-%Y})"
                             if ind else f"{codigo}: sin datos" for codigo, ind in indicadores.items())
        return Informe("Pagos en moneda extranjera",
                       ["Empleado", "Salario (CLP)", "Dólar (USD)", "Euro (EUR)", "UF (CLF)"], filas,
                       usuario.nombre_usuario, "pagos_moneda_extranjera", subtitulo=valores)


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase GeneradorInformes con un método por cada uno de los 6
  reportes; cada uno consulta su repositorio y devuelve un objeto Informe.
- ¿Qué se adoptó?: Los cálculos pesados (SUM, GROUP BY, JOIN) se hacen en Oracle desde los
  repositorios; aquí solo se agregan los totales por proyecto y se da formato a las filas.
- ¿Qué se modificó?: El informe de pagos descifra salarios, así que exige VER_SALARIOS dos
  veces: al inicio y en Empleado.obtener_salario() (si un GERENTE llegara a llamarlo, recibe
  AccesoDenegadoError). Los indicadores llegan como función para usar el valor de la API o,
  si no responde, el último guardado en Oracle.
- ¿Qué se descartó?: Calcular las horas en Python recorriendo todos los registros (ver abajo).

Código propuesto por la IA y DESCARTADO:

    totales = {}
    for r in repositorio_registros.listar():
        totales[r["id_proyecto"]] = totales.get(r["id_proyecto"], 0) + r["horas_trabajadas"]

Por qué se descartó: trae TODA la tabla REGISTRO_TIEMPO a Python para sumar; con
GROUP BY la base de datos entrega solo el resultado, y además con los nombres (JOIN)
en vez de solo los ids.
"""
