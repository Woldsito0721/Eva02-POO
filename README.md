# Sistema de Gestión EcoTech Solutions

Evaluación Sumativa Unidades 2 y 3 · Programación Orientada a Objeto Seguro (TI3V21) · INACAP Puerto Montt

Programa de consola en Python (POO) que gestiona empleados, departamentos, proyectos,
asignaciones y horas trabajadas en **Oracle FreeSQL**, con inicio de sesión (contraseñas
SHA-512), permisos por rol, salarios cifrados (Fernet), consumo de APIs de clima
(Open-Meteo, 10 ciudades de Chile) y monedas (mindicador.cl, con respaldo open.er-api.com),
y reportes exportables a **PDF** o **Excel**.

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

4. **Solo si sus tablas ya existían antes del 23-11:** ejecutar una vez
   [`sql/actualizar_dato_clima.sql`](sql/actualizar_dato_clima.sql) en el SQL Worksheet
   (**Run Script**). Deja opcional el proyecto en DATO_CLIMA y **no borra datos**.
   No vuelva a ejecutar `crear_tablas.sql`: ese script borra todas las tablas.
5. **Probar la conexión:**

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
2. **Carga de datos de internet:** cada vez que se ejecuta, antes del inicio de sesión, el
   sistema trae el clima actual de las 10 ciudades y el valor del dólar y el euro, y los
   guarda en Oracle (`[INFO] Datos cargados: 10 ciudades y 2 monedas`). Si no hay
   internet, avisa y continúa normalmente.
3. **Inicio de sesión:** la contraseña no se muestra al escribirla. Con 3 contraseñas
   incorrectas la cuenta queda **bloqueada** hasta que un administrador la desbloquee
   (menú 6). La sesión dura 30 minutos.
4. **Menú principal** (cada rol ve solo sus opciones):

   | Opción | Qué hace | ADMIN | GERENTE | EMPLEADO |
   |---|---|:-:|:-:|:-:|
   | 1. Proyectos | Crear, listar, editar y eliminar proyectos | ✅ | ✅ | |
   | 2. Departamentos | Crear departamentos, asignar gerente y empleados | ✅ | | |
   | 3. Empleados y salarios | Crear empleados (salario cifrado), ver salario y pago en USD/EUR | ✅ | | |
   | 4. Asignaciones | Asignar empleados a proyectos y finalizar asignaciones | ✅ | ✅ | |
   | 5. Registro de horas | Registrar y ver sus propias horas | ✅ | ✅ | ✅ |
   | 6. Usuarios | Crear cuentas y desbloquear cuentas | ✅ | | |
   | 7. Clima y monedas | Clima de 10 ciudades y valor del dólar y euro | ✅ | ✅ | |
   | 8. Reportes | 6 reportes en PDF o Excel | ✅ | ✅ | |
   | 9 / 0 | Cerrar sesión / Salir | ✅ | ✅ | ✅ |

### 7. Clima y monedas

- **1. Clima:** se elige una de 10 ciudades (Arica, Antofagasta, La Serena, Valparaíso,
  Santiago, Concepción, Temuco, Valdivia, Puerto Montt, Punta Arenas). Muestra el clima de
  **ahora** (según el día y la hora de la consulta), si se recomienda trabajar en terreno y
  una tabla **hora por hora** con lo que queda del día (temperatura, humedad, probabilidad
  de lluvia y estado).
- **2. Monedas:** valor del **dólar** y del **euro** en pesos chilenos. Usa mindicador.cl;
  si no responde, usa open.er-api.com, y si tampoco hay internet, el último valor guardado.

### 8. Reportes (PDF o Excel)

Se elige el reporte y luego el formato: **1. PDF** o **2. Excel**. El archivo queda en la
carpeta `reportes/` (se crea sola) con la fecha y hora en el nombre.

| Reporte | Contenido |
|---|---|
| 1. Horas por proyecto | Horas de cada empleado en cada proyecto y total por proyecto |
| 2. Horas de un empleado | Detalle por fecha y proyecto entre dos fechas, con total |
| 3. Empleados por departamento | Departamento, gerente, empleados y correo |
| 4. Asignaciones de un proyecto | Empleados, rol, fechas y estado (activa / finalizada) |
| 5. Clima e indicadores guardados | Última lectura de cada ciudad e historial de monedas |
| 6. Pagos en moneda extranjera | Salario en CLP, USD y EUR (**solo ADMINISTRADOR**) |

> Todo se ejecuta **desde la terminal, en la carpeta `Eva02-POO`**. No usar el botón ▶ de
> VS Code: ejecuta el archivo desde otra carpeta y falla con `No module named 'config'`.

| Error | Solución |
|---|---|
| `No module named 'config'` | Ejecutar desde la terminal en la carpeta `Eva02-POO`, no con ▶ |
| `timed out` / `DPY-6005` | Cambiar de red |
| `ORA-01017` | Usuario o contraseña incorrectos en el `.env` |
| `ORA-28000` | Cuenta bloqueada: **Regenerate** en FreeSQL y actualizar el `.env` |
| `ORA-00942` | Faltan las tablas: ejecutar `sql/crear_tablas.sql` |
| `No module named 'oracledb'`, `'openpyxl'` o `'fpdf'` | `pip install -r requirements.txt` |
| `DATO_CLIMA \| Error de base de datos` al iniciar | Falta ejecutar `sql/actualizar_dato_clima.sql` |
| Monedas o clima con `[WARNING] Servicio externo...` | Sin internet o la API no responde: se usan los últimos datos guardados |
| `No se pudo guardar el archivo` en reportes | Cerrar el archivo si está abierto en Excel y reintentar |

## Estructura

| Carpeta | Contenido |
|---|---|
| `main.py` | `SistemaEcoTech`: carga de datos, login y menú por permisos |
| `config/` | `ConfiguracionApp`: único lugar que lee el `.env` |
| `model/` | Clases del dominio (una por archivo) |
| `security/` | `Sesion`, `ServicioCifrado`, `Validador`, `AccesoDenegadoError` |
| `database/` | `ConexionBD`, `RepositorioCRUD` (abstracta) y los 7 repositorios |
| `service/` | `ServicioAPI` (abstracta), `ServicioClima`, `ServicioIndicadores` y `CargaInicial` |
| `report/` | `Informe`, `Exportador` (abstracta), `ExportadorPDF`, `ExportadorExcel` y `GeneradorInformes` |
| `sql/` | `crear_tablas.sql` (BD nueva) y `actualizar_dato_clima.sql` (BD existente) |
| `reportes/` | PDF y Excel generados (no se suben a git) |
| `docs/` | Diagrama de clases y modelo entidad-relación |

## Seguridad

| Medida | Cómo se aplica |
|---|---|
| Contraseñas | Hash PBKDF2-HMAC-SHA512 con sal aleatoria y 210.000 iteraciones; nunca en texto |
| Salarios | Cifrados con Fernet en Oracle; solo el ADMINISTRADOR (permiso VER_SALARIOS) los descifra |
| Inicio de sesión | Contraseña oculta, mensaje genérico, bloqueo a los 3 intentos y sesión de 30 minutos |
| Permisos por rol | Cada menú exige su permiso, también dentro de los submenús |
| Inyección SQL | Todas las consultas son parametrizadas (`:nombre`), sin SQL armado con texto |
| Entradas | `Validador` y los constructores del modelo validan todo antes de llegar a Oracle |
| APIs | Ciudades y monedas de una lista cerrada; los errores se muestran sin URLs ni detalles internos |
| Reportes | El nombre del archivo lo arma el sistema (sin `../`); en Excel un texto con `=` no se ejecuta como fórmula |
| Secretos | Credenciales y clave Fernet solo en `.env`, que no se sube a git |

## Diagramas

| Diagrama | Imagen | Fuente editable (draw.io) |
|---|---|---|
| Clases (paquetes = carpetas del proyecto) | [docs/diagrama_clases.svg](docs/diagrama_clases.svg) | [docs/diagrama_clases.drawio](docs/diagrama_clases.drawio) |
| Entidad-relación (Oracle FreeSQL) | [docs/modelo_er.svg](docs/modelo_er.svg) | [docs/modelo_er.drawio](docs/modelo_er.drawio) |

Cada recuadro de color del diagrama de clases corresponde a una carpeta (`main.py`, `config/`,
`model/`, `security/`, `database/`, `service/`), y cada clase indica el archivo donde está.

> Cambios del 23-11 aún no dibujados en el diagrama: `TareaProgramada` pasó a `CargaInicial`
> (sin rutina de las 08:00) y se agregó el paquete `report/` con `Informe`, `Exportador`,
> `ExportadorPDF`, `ExportadorExcel` y `GeneradorInformes`.

## Uso de IA

Cada archivo `.py` termina con un bloque **Registro uso de IA** (qué generó la herramienta,
qué se adoptó, modificó y descartó) y el **código propuesto por la IA que se descartó**,
comentado y con su justificación técnica.
