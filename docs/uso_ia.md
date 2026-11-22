# Uso de herramientas de IA

El detalle completo (fecha, herramienta, prompt, qué propuso y qué se adoptó, modificó o
descartó) está en la sección 8 del manual técnico. Además, **cada archivo `.py` termina con
un bloque "Registro uso de IA" y el código propuesto por la IA que se descartó**, comentado y
con su justificación técnica.

## Decisiones principales

| Archivo | Propuesta de la IA descartada | Por qué |
|---|---|---|
| `main.py` | Login con SQL armado con f-string y contraseña en texto plano | Inyección SQL (`' or '1'='1`) y contraseña sin hash |
| `security/servicio_cifrado.py` | SHA-512 de una pasada sin sal; luego bcrypt | Sin sal es vulnerable; el profesor exige SHA-512 → PBKDF2-HMAC-SHA512 |
| `security/sesion.py` | Sesión sin expiración y mensajes con el rol y permiso | Sesiones eternas y fuga de información |
| `security/validador.py` | Validar correo solo con `"@" in correo` | Acepta valores como `"@."` |
| `database/conexion_bd.py` | Pool de conexiones | Un solo usuario por ejecución; FreeSQL limita sesiones |
| `database/repositorio_crud.py` | `eliminar()` genérico con f-string | SQL armado con texto y nombres de id distintos por tabla |
| `database/repositorios.py` | Capturar ORA-00001 para no duplicar indicadores | Error como control de flujo; se usa `MERGE` |
| `model/empleado.py` | Setter público del salario | Permitía leerlo sin el permiso VER_SALARIOS |
| `model/indicador_economico.py` | Convertir multiplicando por el valor | Conversión al revés; lo correcto es dividir |
| `service/servicio_api.py` | `except HTTPError` | Código inalcanzable sin `raise_for_status()` |
| `service/servicio_clima.py` | Cambiar `self._url_base` temporalmente | Error entre hilos (menú y rutina de las 08:00) |
| `service/servicio_indicadores.py` | Concatenar el código en la URL | Inyección de rutas y códigos ISO no soportados |
| `service/tarea_programada.py` | Leer `_Proyecto__ciudad` y silenciar errores con `pass` | Rompe el encapsulamiento y oculta fallos |
| `test/` | `unittest` / `mock` / `TRUNCATE` | No vistos en clases; TRUNCATE borra datos reales |
