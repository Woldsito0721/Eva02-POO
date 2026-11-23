# Sistema de Gestión EcoTech Solutions

Evaluación Sumativa Unidades 2 y 3 · Programación Orientada a Objeto Seguro (TI3V21) · INACAP Puerto Montt

Programa de consola en Python (POO) que gestiona empleados, departamentos, proyectos,
asignaciones y horas trabajadas en **Oracle FreeSQL**, con inicio de sesión (contraseñas
SHA-512), permisos por rol, salarios cifrados (Fernet) y consumo de APIs de clima
(Open-Meteo) e indicadores económicos (mindicador.cl) con una rutina automática a las 08:00.

## 1. Instalar

Requisito: Python 3.10 o superior.

```powershell
git clone https://github.com/Woldsito0721/Eva02-POO.git
```

```powershell
cd Eva02-POO
```

```powershell
pip install -r requirements.txt
```

## 2. Conectar a su base de datos de FreeSQL

1. **Crear las tablas:** en FreeSQL abrir **SQL Worksheet**, pegar todo
   [`sql/crear_tablas.sql`](sql/crear_tablas.sql) y presionar **Run Script**.
2. **Copiar los datos de conexión:** en FreeSQL presionar **Connect** y copiar
   *Username*, *Password* y *Service Name*. Si la contraseña ya no se ve, presionar
   **Regenerate**.
3. **Crear el archivo `.env`** en la carpeta `Eva02-POO`:

   ```powershell
   Copy-Item .env.example .env
   ```

   Abrirlo y completarlo así:

   ```
   DB_USER=<Username>
   DB_PASSWORD=<Password>
   DB_DSN=tcps://db.freesql.com:2484/<Service Name>
   FERNET_KEY=<clave generada con el comando de abajo>
   ```

   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

4. **Probar la conexión:**

   ```powershell
   python -m database.conexion_bd
   ```

   Debe mostrar `[INFO] Conexión OK`.

**Si falla la conexión:** si se queda esperando o muestra `timed out`, la red (por ejemplo,
el Wi-Fi de la universidad) bloquea el puerto 2484. Conectarse a otra red (compartir
internet desde un celular) y probar de nuevo.

## 3. Ejecutar el sistema

```powershell
python main.py
```

1. **Primera vez:** como la BD está vacía, el sistema pide nombre, correo, salario, usuario
   y contraseña para crear el **ADMINISTRADOR**. Luego iniciar sesión con ese usuario.
2. **Menú principal:**

   | Opción | Qué hace |
   |---|---|
   | 1. Proyectos | Crear, listar, editar y eliminar proyectos |
   | 2. Departamentos | Crear departamentos y asignar gerente |
   | 3. Empleados y salarios | Crear empleados (salario cifrado) |
   | 4. Asignaciones | Asignar empleados a proyectos |
   | 5. Registro de horas | Registrar horas trabajadas |
   | 6. Usuarios | Crear cuentas GERENTE / EMPLEADO y desbloquear cuentas |
   | 7. Clima e indicadores | Consultar las APIs |
   | 9 / 0 | Cerrar sesión / Salir |

> Todo se ejecuta **desde la terminal, en la carpeta `Eva02-POO`**. No usar el botón ▶ de
> VS Code: ejecuta el archivo desde otra carpeta y falla con `No module named 'config'`.

| Error | Solución |
|---|---|
| `No module named 'config'` | Ejecutar desde la terminal en la carpeta `Eva02-POO`, no con ▶ |
| `timed out` / `DPY-6005` | Cambiar de red |
| `ORA-01017` | Usuario o contraseña incorrectos en el `.env` |
| `ORA-28000` | Cuenta bloqueada: **Regenerate** en FreeSQL y actualizar el `.env` |
| `ORA-00942` | Faltan las tablas: ejecutar `sql/crear_tablas.sql` |
| `No module named 'oracledb'` | `pip install -r requirements.txt` |

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
