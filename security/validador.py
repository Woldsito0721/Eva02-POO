import re

"""
Rgistro uso de IA:
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
        patron = r"^\+?[0-9\s-]{8,15}$"
        return bool(re.match(patron, tel.strip()))

    @staticmethod
    def validar_horas(horas: float) -> bool:
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            return False
        return 0 < horas <= 24
    @staticmethod
    def validar_ciudad(ciudad: str) -> bool:
        if not isinstance(ciudad, str):
            return False
        patron = r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s-]{2,60}$"
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
        limpio = re.sub(r"[\x00-\x1f\x7f<>\"';]", "", texto)
        return " ".join(limpio.split())