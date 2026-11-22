import re

"""
Registro uso de IA:
- ¿Qué generó la herramienta?: Métodos básicos que solo verificaban que los textos no estuvieran vacíos, sin control de longitud máxima ni validación estricta para ciudades, monedas o tipos booleanos.
- ¿Qué se adoptó?: La estructura de clase utilitaria con decoradores @staticmethod y el uso del módulo estándar re (expresiones regulares).
- ¿Qué se modificó?: Se agregaron límites de longitud acordes a las columnas VARCHAR2 de Oracle, exclusión explícita de bool en validar_horas() y listas blancas (regex) para validar_ciudad() y validar_codigo_moneda().
- ¿Qué se descartó?: Validaciones genéricas permisivas que aceptaban símbolos especiales o inyección de parámetros en URLs.
- Justificación: Garantiza la integridad de los datos antes de interactuar con Oracle FreeSQL y previene la manipulación de consultas hacia las APIs externas.
"""


class Validador:
    """Clase utilizada para validación y control de entradas del usuario."""

    @staticmethod
    def validar_texto(texto: str, maximo: int) -> bool:
        if not isinstance(texto, str) or maximo <= 0:
            return False
        limpio = texto.strip()
        return 0 < len(limpio) <= maximo
    @staticmethod
    def validar_correo(correo: str) -> bool:
        if not isinstance(correo, str):
            return False
        patron = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(patron, correo.strip()))

    @staticmethod
    def validar_telefono(tel: str) -> bool:
        if not isinstance(tel, str):
            return False
        # Solo se permiten dígitos, espacios, guiones y un + inicial...
        if not re.match(r"^\+?[0-9\s-]+$", tel.strip()):
            return False
        # ...y se cuentan los dígitos reales: "--------" o puros espacios no son teléfonos
        digitos = re.sub(r"\D", "", tel)
        return 8 <= len(digitos) <= 15

    @staticmethod
    def validar_horas(horas: float) -> bool:
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            return False
        return 0 < horas <= 24
    @staticmethod
    def validar_ciudad(ciudad: str) -> bool:
        if not isinstance(ciudad, str):
            return False
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s'-]{2,80}$"  # 80 = VARCHAR2(80) de PROYECTO.ciudad
        return bool(re.match(patron, ciudad.strip()))

    @staticmethod
    def validar_codigo_moneda(codigo: str) -> bool:
        if not isinstance(codigo, str):
            return False
        return bool(re.match(r"^[A-Z]{3}$", codigo.strip().upper()))
    @staticmethod
    def sanitizar(texto: str) -> str:
        if not isinstance(texto, str):
            return ""
        # Se quitan caracteres de control y < > " ; (inyección en consola/URL).
        # El apóstrofe se conserva (O'Higgins): la inyección SQL ya la impiden
        # las consultas parametrizadas (:nombre), no este método.
        limpio = re.sub(r"[\x00-\x1f\x7f<>\";]", "", texto)
        return " ".join(limpio.split())


"""
Corrección de integración (auditoría):
- validar_telefono() contaba caracteres, no dígitos: aceptaba "--------". Ahora exige
  entre 8 y 15 dígitos reales.
- validar_ciudad() permitía hasta 60 caracteres, pero PROYECTO.ciudad y DATO_CLIMA.ciudad
  son VARCHAR2(80); se amplió a 80 y se aceptó el apóstrofe.
- sanitizar() ya no elimina el apóstrofe, para no romper nombres como O'Higgins.

Código propuesto por la IA y DESCARTADO:

    @staticmethod
    def validar_correo(correo: str) -> bool:
        return "@" in correo and "." in correo

Por qué se descartó: acepta valores como "@." o "a@b." y no limita los caracteres
permitidos. La expresión regular exige usuario, dominio y extensión de al menos 2 letras.
"""