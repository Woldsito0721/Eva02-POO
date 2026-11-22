# Sistema de Gestión EcoTech Solutions

Evaluación Sumativa Unidades 2 y 3 · Programación Orientada a Objeto Seguro (TI3V21) · INACAP Puerto Montt

Programa de consola en Python (POO) que gestiona empleados, departamentos, proyectos,
asignaciones y horas trabajadas en **Oracle FreeSQL**, con inicio de sesión (contraseñas
SHA-512), permisos por rol, salarios cifrados (Fernet) y consumo de APIs de clima
(Open-Meteo) e indicadores económicos (mindicador.cl) con una rutina automática a las 08:00.

## Puesta en marcha

Requisitos: Python 3.10 o superior y una cuenta gratuita en [FreeSQL](https://freesql.com).
En FreeSQL cada cuenta tiene su propio esquema, así que cada uno crea las tablas en la suya.

1. **Crear las tablas.** En FreeSQL abrir *SQL Worksheet*, pegar todo el contenido de
   [`sql/crear_tablas.sql`](sql/crear_tablas.sql) y ejecutarlo con **Run Script**.
   Se crean 8 tablas (el script se puede repetir: borra y vuelve a crear las tablas vacías).
2. **Datos de conexión.** En FreeSQL: **Connect** → **Regenerate**. Copiar el usuario
   (esquema), la contraseña generada (no es la de la cuenta Oracle) y el DSN
   (`tcps://db.freesql.com:2484/<servicio>`).
3. **Archivo `.env`.** Copiar `.env.example` como `.env` y completarlo:

   ```powershell
   Copy-Item .env.example .env
   ```

   Para `FERNET_KEY` (clave que cifra los salarios), generar una clave y pegarla:

   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

   El `.env` está en `.gitignore`: nunca se sube al repositorio.
4. **Dependencias:**

   ```powershell
   pip install -r requirements.txt
   ```

5. **Probar la conexión y ejecutar** desde la raíz del proyecto:

   ```powershell
   python -m test.prueba_conexion
   ```

   ```powershell
   python main.py
   ```

   La primera vez (tabla USUARIO vacía) el programa pide los datos del primer empleado y
   crea su cuenta ADMINISTRADOR. Desde **6. Usuarios** se crean cuentas GERENTE o EMPLEADO
   y se desbloquean cuentas bloqueadas por 3 intentos fallidos.

| Error | Solución |
|---|---|
| `ORA-01017: invalid username/password` | Usar la contraseña generada con **Regenerate**, no la de la cuenta Oracle |
| `DPY-6005` / `timed out` | La red bloquea el puerto (ej. Wi-Fi institucional): probar con otra red |
| `ORA-00942: table or view does not exist` | Ejecutar `sql/crear_tablas.sql` con la misma cuenta del `.env` |
| `ModuleNotFoundError: oracledb` | `pip install -r requirements.txt` |

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
| `docs/` | Diagrama de clases y modelo entidad-relación |

## Diagramas

| Diagrama | Imagen | Fuente editable (draw.io) |
|---|---|---|
| Clases (paquetes = carpetas del proyecto) | [docs/diagrama_clases.svg](docs/diagrama_clases.svg) | [docs/diagrama_clases.drawio](docs/diagrama_clases.drawio) |
| Entidad-relación (Oracle FreeSQL) | [docs/modelo_er.svg](docs/modelo_er.svg) | [docs/modelo_er.drawio](docs/modelo_er.drawio) |

Cada recuadro de color del diagrama de clases corresponde a una carpeta (`main.py`, `config/`,
`model/`, `security/`, `database/`, `service/`), y cada clase indica el archivo donde está.

## Uso de IA

Cada archivo `.py` termina con un bloque **Registro uso de IA** (qué generó la herramienta,
qué se adoptó, modificó y descartó) y el **código propuesto por la IA que se descartó**,
comentado y con su justificación técnica.
