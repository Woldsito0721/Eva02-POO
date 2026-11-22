from __future__ import annotations

# Python
from datetime import date, datetime
from typing import TYPE_CHECKING

# Proyecto
from model.registro_tiempo import RegistroTiempo
from model.rol import Permiso
from security.sesion import AccesoDenegadoError
from security.validador import Validador

if TYPE_CHECKING:  # solo para las anotaciones: evita importaciones circulares
    from model.departamento import Departamento
    from model.indicador_economico import IndicadorEconomico
    from model.proyecto import Proyecto
    from model.usuario import Usuario
    from security.servicio_cifrado import ServicioCifrado


class Empleado():
    """ Trabajador de EcoTech. El salario solo existe cifrado dentro del objeto """

    def __init__(self, nombre: str, direccion: str, telefono: str, correo: str,
                 fecha_inicio_contrato: date, salario_cifrado: bytes,
                 id_empleado: int = None, departamento: Departamento = None):
        # oracledb entrega DATE como datetime: se convierte a date para poder comparar
        if isinstance(fecha_inicio_contrato, datetime):
            fecha_inicio_contrato = fecha_inicio_contrato.date()

        # Validación antes de guardar cualquier dato
        if not Validador.validar_texto(nombre, 100):
            raise ValueError("Nombre inválido (1 a 100 caracteres)")
        if direccion and not Validador.validar_texto(direccion, 200):
            raise ValueError("Dirección inválida (máximo 200 caracteres)")
        if telefono and not Validador.validar_telefono(telefono):
            raise ValueError("Teléfono inválido (8 a 15 dígitos)")
        if not Validador.validar_correo(correo) or len(correo) > 120:
            raise ValueError("Correo inválido")
        if not isinstance(fecha_inicio_contrato, date):
            raise ValueError("La fecha de inicio debe ser una fecha")
        if not isinstance(salario_cifrado, bytes):
            raise ValueError("El salario debe llegar cifrado (bytes)")

        self.__id_empleado = id_empleado
        self.__nombre = Validador.sanitizar(nombre)
        self.__direccion = Validador.sanitizar(direccion) if direccion else None
        self.__telefono = telefono.strip() if telefono else None
        self.__correo = correo.strip().lower()
        self.__fecha_inicio_contrato = fecha_inicio_contrato
        self.__salario_cifrado = salario_cifrado
        self.__departamento = departamento

    @classmethod
    def crear(cls, nombre: str, direccion: str, telefono: str, correo: str,
              fecha_inicio_contrato: date, salario: float, cifrado: ServicioCifrado):
        """ Empleado nuevo: recibe el salario en número y lo guarda cifrado con Fernet """
        if isinstance(salario, bool) or not isinstance(salario, (int, float)) or salario <= 0:
            raise ValueError("El salario debe ser un número mayor a 0")
        return cls(nombre, direccion, telefono, correo, fecha_inicio_contrato,
                   cifrado.cifrar(str(salario)))

    # --- Propiedades de solo lectura ---
    @property
    def id_empleado(self):
        return self.__id_empleado

    @property
    def nombre(self):
        return self.__nombre

    @property
    def direccion(self):
        return self.__direccion

    @property
    def telefono(self):
        return self.__telefono

    @property
    def correo(self):
        return self.__correo

    @property
    def fecha_inicio_contrato(self):
        return self.__fecha_inicio_contrato

    @property
    def salario_cifrado(self):
        """ Bytes cifrados: es lo que se guarda en EMPLEADO.salario_cifrado (RAW) """
        return self.__salario_cifrado

    @property
    def departamento(self):
        return self.__departamento

    @property
    def id_departamento(self):
        return self.__departamento.id_departamento if self.__departamento else None

    # --- Comportamiento ---
    def obtener_salario(self, solicitante: Usuario, cifrado: ServicioCifrado) -> float:
        """ Descifra el salario solo si el solicitante tiene el permiso VER_SALARIOS (RF9) """
        if not solicitante.tiene_permiso(Permiso.VER_SALARIOS):
            raise AccesoDenegadoError(f"{solicitante.nombre_usuario} sin permiso VER_SALARIOS")
        return float(cifrado.descifrar(self.__salario_cifrado))

    def calcular_pago_en_moneda(self, solicitante: Usuario, indicador: IndicadorEconomico,
                                cifrado: ServicioCifrado) -> float:
        """ Salario (CLP) convertido a la moneda del proyecto con el indicador del día """
        return indicador.convertir_desde_clp(self.obtener_salario(solicitante, cifrado))

    def registrar_horas(self, proyecto: Proyecto, fecha: date, horas: float,
                        descripcion: str = None) -> RegistroTiempo:
        """ Solo puede registrar horas en un proyecto donde está asignado (RF4) """
        if not proyecto.tiene_asignado(self):
            raise ValueError(f"{self.__nombre} no está asignado al proyecto {proyecto.nombre}")

        registro = RegistroTiempo(self, proyecto, fecha, horas, descripcion)
        proyecto.agregar_registro(registro)
        return registro

    def _cambiar_departamento(self, departamento: Departamento) -> None:
        """ Uso interno: lo llama Departamento para mantener la relación 0..1 """
        self.__departamento = departamento

    # Dos objetos Empleado leídos por separado desde Oracle son el mismo empleado si
    # tienen el mismo id; sin id (aún no guardado) se compara por identidad
    def __eq__(self, otro):
        if not isinstance(otro, Empleado):
            return NotImplemented
        if self.__id_empleado is not None and otro.id_empleado is not None:
            return self.__id_empleado == otro.id_empleado
        return self is otro

    def __hash__(self):
        return hash(self.__id_empleado) if self.__id_empleado is not None else id(self)

    def __str__(self):
        return f"Empleado {self.__nombre} | {self.__correo}"


"""
Registro uso de IA (Claude):
- ¿Qué generó la herramienta?: La clase Empleado con datos personales, salario
  cifrado, obtener_salario() con control de permiso y registrar_horas().
- ¿Qué se adoptó?: El salario nunca se guarda en texto: el objeto solo tiene los
  bytes cifrados; descifrar exige el permiso VER_SALARIOS (RF9).
- ¿Qué se modificó?: Se reutilizó el Validador del compañero en vez de validar a mano;
  ServicioCifrado se recibe como parámetro (dependencia «use» del diagrama) para no
  leer la clave en cada objeto; se agregó crear() para empleados nuevos.
- ¿Qué se descartó?: Un setter público para el salario (ver abajo).
- Justificación: Con atributos privados y sin setters, ninguna parte del programa
  puede leer o cambiar el salario saltándose el permiso.

Código propuesto por la IA y DESCARTADO:

    @property
    def salario(self) -> float:
        return float(self.__cifrado.descifrar(self.__salario_cifrado))

    @salario.setter
    def salario(self, nuevo: float):
        self.__salario_cifrado = self.__cifrado.cifrar(str(nuevo))

Por qué se descartó:
  1. empleado.salario se podría leer sin pasar por el permiso VER_SALARIOS.
  2. El diagrama pide get_salario(solicitante): el solicitante es justamente quien
     se valida antes de descifrar.
  3. El setter permitiría cambiar el sueldo desde cualquier menú sin control.
"""
