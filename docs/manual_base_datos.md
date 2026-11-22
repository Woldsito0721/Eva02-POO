# Manual de instalación de la base de datos (Oracle FreeSQL)

Guía para crear la base de datos de **EcoTech Solutions** en una cuenta propia de
[FreeSQL](https://freesql.com) y conectar el programa Python a ella.
Tiempo estimado: 10 minutos.

## Requisitos

- Cuenta Oracle (gratuita) para iniciar sesión en https://freesql.com
- Python 3.10 o superior
- Este repositorio descargado o descomprimido

> En FreeSQL cada cuenta tiene **su propio esquema**. Las tablas se crean dentro
> del esquema de quien inicia sesión, por lo que no se comparte la BD de los alumnos:
> cada evaluador crea la suya en su cuenta.

---

## Paso 1: crear las tablas

1. Entrar a https://freesql.com e iniciar sesión.
2. Abrir el editor SQL (*SQL Worksheet*).
3. Abrir el archivo [`sql/crear_tablas.sql`](../sql/crear_tablas.sql) del repositorio,
   copiar **todo** su contenido y pegarlo en el editor.
4. Ejecutarlo como **script** (botón *Run Script*), no sentencia por sentencia.
5. Verificar que se crearon las 8 tablas:

   ```sql
   SELECT table_name FROM user_tables ORDER BY table_name;
   ```

   Resultado esperado:

   | TABLE_NAME |
   |---|
   | ASIGNACION |
   | DATO_CLIMA |
   | DEPARTAMENTO |
   | EMPLEADO |
   | INDICADOR_ECONOMICO |
   | PROYECTO |
   | REGISTRO_TIEMPO |
   | USUARIO |

> El script se puede ejecutar más de una vez: su primer bloque borra las 8 tablas
> si ya existen y las vuelve a crear vacías (se pierden los datos cargados).

## Paso 2: obtener los datos de conexión

1. En FreeSQL, hacer clic en **Connect** (esquina superior derecha).
2. Hacer clic en **Regenerate** para generar la contraseña de conexión externa.
   (Es distinta a la contraseña de la cuenta Oracle.)
3. Copiar del cuadro de diálogo:
   - **Usuario / esquema** (ej. `MI_ESQUEMA`)
   - **Contraseña** generada
   - **Host, puerto y servicio**, que forman el DSN. Ejemplo de formato:
     `tcps://db.freesql.com:2484/<servicio>` (conexión cifrada, probada con oracledb en modo thin)

> El nombre del servicio puede cambiar entre cuentas o versiones de FreeSQL:
> copiarlo siempre desde el diálogo *Connect*, no desde este manual.

## Paso 3: configurar el archivo `.env`

1. En la raíz del proyecto, copiar `.env.example` y renombrar la copia a `.env`:

   ```powershell
   Copy-Item .env.example .env
   ```

2. Completar con los datos del Paso 2:

   ```ini
   DB_USER=MI_ESQUEMA
   DB_PASSWORD=contraseña_generada_en_connect
   DB_DSN=tcps://db.freesql.com:2484/nombre_servicio
   ```

3. Generar la clave de cifrado de salarios y pegarla en `FERNET_KEY`:

   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

Las APIs de clima (Open-Meteo) e indicadores (mindicador.cl) son públicas: no necesitan llave.

> El archivo `.env` está en `.gitignore`: **nunca** se sube al repositorio.

## Paso 4: instalar dependencias y probar la conexión

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Prueba de conexión, desde la raíz del proyecto (debe terminar en `--- Todo correcto ---`):

```powershell
python -m test.prueba_conexion
```

Si funciona, ejecutar el sistema:

```powershell
python main.py
```

## Paso 5: usuario inicial

El usuario administrador **no** se crea en el SQL: su empleado necesita el salario
cifrado con la `FERNET_KEY` de cada instalación, y su contraseña un hash SHA-512 (PBKDF2).
Lo crea `main.py` la primera vez que se ejecuta con la tabla USUARIO vacía:

1. Pide nombre, correo y salario del primer empleado (el salario se guarda cifrado).
2. Pide nombre de usuario y contraseña (mínimo 8 caracteres, no se muestra en pantalla).
3. Crea la cuenta con rol **ADMINISTRADOR** y luego muestra el inicio de sesión.

Desde el menú **6. Usuarios**, el administrador puede crear cuentas GERENTE o EMPLEADO
y desbloquear cuentas bloqueadas por 3 intentos fallidos.

---

## Problemas frecuentes

| Error | Causa | Solución |
|---|---|---|
| `ORA-01017: invalid username/password` | Contraseña equivocada o se usó la de la cuenta Oracle | Usar la contraseña generada con **Regenerate** en *Connect* |
| `DPY-6005` / `timed out` | Red bloquea el puerto 1521 (ej. Wi-Fi institucional) | Probar con otra red o datos móviles |
| `DPY-4027` / `no configuration directory` | DSN mal escrito | Revisar formato `host:puerto/servicio` sin espacios |
| `ORA-00942: table or view does not exist` | No se ejecutó el Paso 1 en ese mismo esquema | Ejecutar `sql/crear_tablas.sql` con la misma cuenta del `.env` |
| `ORA-00955: name is already used` | Tablas ya creadas | Ejecutar el bloque de borrado y repetir el script |
| `ModuleNotFoundError: oracledb` | Dependencias no instaladas | `pip install -r requirements.txt` con el venv activo |
