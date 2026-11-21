# Sistema de Gestión EcoTech Solutions

Evaluación Sumativa Unidades 2 y 3 · Programación Orientada a Objeto Seguro (TI3V21) · INACAP Puerto Montt

Programa de consola en Python (POO) que gestiona empleados, departamentos, proyectos,
asignaciones y horas trabajadas en **Oracle FreeSQL**, con inicio de sesión (contraseñas
SHA-512), permisos por rol, salarios cifrados (Fernet) y consumo de APIs de clima
(Open-Meteo) e indicadores económicos (mindicador.cl) con una rutina automática a las 08:00.

## Puesta en marcha

1. Crear la base de datos y el `.env`: seguir [docs/manual_base_datos.md](docs/manual_base_datos.md).
2. Instalar dependencias:

   ```powershell
   pip install -r requirements.txt
   ```

3. Ejecutar desde la raíz del proyecto:

   ```powershell
   python main.py
   ```

   La primera vez se crea el usuario ADMINISTRADOR.

## Pruebas

Se ejecutan desde la raíz del proyecto y muestran `[OK]` / `[FALLO]` por cada verificación.

| Comando | Qué prueba | Requiere |
|---|---|---|
| `python -m test.prueba_conexion` | `.env`, conexión y las 8 tablas | Oracle |
| `python -m test.prueba_repositorios` | CRUD de los 7 repositorios y reglas de Oracle (borra sus datos al final) | Oracle |
| `python -m test.prueba_modelos` | Las 9 clases de `model/`, sesión, permisos y cifrado | Nada |
| `python -m test.prueba_servicios` | APIs de clima e indicadores y la rutina de las 08:00 | Internet |

## Estructura

| Carpeta | Contenido |
|---|---|
| `main.py` | `SistemaEcoTech`: login, menú por permisos y rutina de las 08:00 |
| `config/` | `ConfiguracionApp`: único lugar que lee el `.env` |
| `model/` | Clases del dominio (una por archivo) |
| `security/` | `Sesion`, `ServicioCifrado`, `Validador`, `AccesoDenegadoError` |
| `database/` | `ConexionBD`, `RepositorioCRUD` (abstracta) y los 7 repositorios |
| `service/` | `ServicioAPI` (abstracta), clima, indicadores y `TareaProgramada` |
| `sql/` | `crear_tablas.sql` |
| `test/` | Scripts de prueba |
| `docs/` | Manual de base de datos, uso de IA y diagramas |

## Uso de IA

Cada archivo `.py` termina con un bloque **Registro uso de IA** y el **código propuesto por la
IA que se descartó**, con su justificación. Resumen en [docs/uso_ia.md](docs/uso_ia.md).
