# Guía de revisión e integración a `main`

**Para:** Arnoldo Mena
**De:** Fernando Valderas Ojeda
**Fecha:** 21-11-2026
**Entrega final:** lunes 23-11-2026, 23:00 (AAI)

Arnoldo, esta guía es tu tarea para las próximas horas: **revisar el proyecto completo
archivo por archivo** e **integrarlo a `main` sin romper nada**. No es un merge rápido:
la idea es que al terminar conozcas cada archivo tan bien como yo, porque en la defensa
oral (50 % de la nota) a cualquiera de los dos le pueden preguntar por cualquier parte.

Tómate el tiempo que haga falta. Es preferible avanzar despacio y anotar dudas a aprobar
algo que no entendiste. Al final de cada fase hay un **punto de control**: no pases a la
siguiente hasta cumplirlo.

---

## 0. Contexto: en qué estado está cada rama

| Rama | Último commit | Qué tiene |
|---|---|---|
| `main` | `259466b` | Tu trabajo: `security/` (Validador, ServicioCifrado con bcrypt, Sesion) y `service/` (ServicioAPI, clima, indicadores, TareaProgramada). Los archivos de `model/`, `database/`, `main.py` y `sql/` están **vacíos**. |
| `Fernando-Valderas` | `04d7621` | Todo el sistema funcionando: config, database, sql, model, main.py, test, docs, **más ajustes a tus archivos** de `security/` y `service/`. Ya incluye tus commits (hice merge de `main` en `e54be84`). |

`main` no tiene ningún commit que no esté en `Fernando-Valderas`, así que **no debería haber
conflictos de Git**. Lo que sí hay que revisar es que estés de acuerdo con los cambios que
hice sobre tu código (sección 3.5 y 3.6), porque eso Git no lo va a preguntar.

### Cambios que hice en tus archivos (léelos primero)

| Archivo | Cambio | Motivo |
|---|---|---|
| `security/servicio_cifrado.py` | bcrypt → **PBKDF2-HMAC-SHA512** (hashlib, sal 16 bytes, 210.000 iteraciones, `hmac.compare_digest`) | El profesor exige SHA-512 |
| `security/servicio_cifrado.py` | `AppConfig` → `ConfiguracionApp` | El import apuntaba a una clase que no existía |
| `security/sesion.py` | `get_usuario()` → `obtener_usuario()` | Regla del proyecto: identificadores solo en español |
| `security/validador.py` | Teléfono: 8 a 15 dígitos reales; ciudad hasta 80 caracteres y con apóstrofe; `sanitizar` conserva el apóstrofe | `"--------"` pasaba como teléfono válido; `O'Higgins` era rechazada |
| `security/requirements.txt` | Eliminado | Queda un solo `requirements.txt` en la raíz |
| `service/servicio_api.py` | `consultar()` pasa a ser el método abstracto; `_obtener_json(ruta, parametros, url_base)`; se quita `except HTTPError` | `ServicioAPI` se podía instanciar; el `except HTTPError` era inalcanzable sin `raise_for_status()` |
| `service/servicio_clima.py` | `consultar()` → llama a `obtener_clima()`; la geocodificación pasa la URL por parámetro | Antes se cambiaba `self._url_base` temporalmente, y eso falla con dos hilos (menú y rutina 08:00) |
| `service/servicio_indicadores.py` | `consultar()` → `obtener_indicador()` | Mismo patrón polimórfico |
| `service/tarea_programada.py` | Recibe `repositorio`; agrega `configurar_proyectos()`, `detener()`; `ejecutar()` devuelve `{clima, indicadores, errores}` | Leía `_Proyecto__ciudad` (rompía encapsulamiento) y silenciaba errores con `pass` |
| `requirements.txt` | Se quita `bcrypt` | Ya no se usa |

Cada archivo termina con un bloque **"Registro uso de IA"** y el **código descartado comentado**.
Eso lo pide el profesor y suma puntos (criterios 2.1.5 y 3.1.4): **no lo borres**.

---

## Fase 1. Preparar tu entorno (≈ 45 min)

1. Actualiza tu copia local:
   ```powershell
   git fetch origin
   git switch main
   git pull origin main
   git status
   ```
   `git status` debe decir *working tree clean*. Si tienes cambios sin subir, haz commit en
   tu rama antes de seguir.

2. Crea **tu propia** base de datos en **tu** cuenta de FreeSQL siguiendo
   `docs/manual_base_datos.md` (pasos 1 a 4). No uses mis credenciales: cada uno prueba con
   su esquema.

3. Crea tu `.env` desde `.env.example` y genera **tu propia** `FERNET_KEY`:
   ```powershell
   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```
   ⚠️ El `.env` **nunca** se sube. Verifícalo con `git check-ignore -v .env` (debe responder
   con la línea de `.gitignore`).

4. Entorno virtual y dependencias:
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

**Punto de control 1:** `python -m test.prueba_conexion` termina en `--- Todo correcto ---`
(esto lo podrás correr cuando tengas la rama de integración, en la Fase 2).

---

## Fase 2. Crear la rama de integración (≈ 15 min)

**No se integra directo a `main`.** Se trabaja en una rama intermedia y al final se abre un
Pull Request que revisamos los dos.

```powershell
git switch main
git switch -c integracion-main
git merge --no-ff --no-commit origin/Fernando-Valderas
```

- `--no-commit` deja todos los cambios **preparados pero sin confirmar**, para que los
  revises uno por uno antes del commit.
- Para ver la lista completa: `git status` y `git diff --cached --stat main`.
- Para revisar un archivo: `git diff --cached main -- ruta/del/archivo.py`
  (o ábrelo en VS Code, pestaña *Source Control*, que muestra el antes y el después).

Si en algún momento quieres empezar de cero: `git merge --abort`.

**Punto de control 2:** `git status` muestra *"All conflicts fixed but you are still
merging"* y la lista de archivos.

---

## Fase 3. Revisión archivo por archivo (≈ 6 a 8 horas)

Revisa **en este orden** (de la capa más baja a la más alta: cada capa depende solo de las
anteriores). Por cada archivo:

1. Léelo **completo**, incluido el bloque de IA del final.
2. Compáralo con el **diagrama de clases** (`diagrama final de POO.drawio`): nombre de la
   clase, atributos (`-` privado = `__atributo`, `#` protegido = `_atributo`), métodos y
   parámetros.
3. Responde las preguntas de la tabla de esa sección.
4. Ejecuta la prueba indicada.
5. Anota el resultado en la **tabla de registro** (sección 6 de esta guía).

### Lista de verificación general (aplica a TODOS los archivos)

- [ ] Todos los nombres (clases, métodos, variables, parámetros) están en **español**, sin
      mezclas como `get_`, `set_`, `data`, `user`.
- [ ] Imports agrupados como en las clases del profesor: `# Python`, `# Librerías`, `# Proyecto`.
- [ ] Atributos sensibles privados (`__`) y expuestos con `@property` **sin setter**.
- [ ] Ningún `print` muestra contraseñas, salarios en claro, la `FERNET_KEY`, URLs internas
      ni trazas completas. Los mensajes usan `[INFO]`, `[WARNING]`, `[ERROR]`.
- [ ] Ningún SQL armado con f-string o `+`: siempre parámetros `:nombre` o `:1`.
- [ ] Ningún `except: pass` ni `except Exception` que oculte el error.
- [ ] Termina con el bloque **"Registro uso de IA"** y el **código descartado** con su
      justificación.

### 3.1 Raíz y configuración (≈ 30 min)

| Archivo | Qué verificar |
|---|---|
| `requirements.txt` | Solo `oracledb`, `python-dotenv`, `requests`, `cryptography`. Sin `bcrypt`. |
| `.env.example` | Solo nombres de variables, **sin valores reales**. Sin API keys (Open-Meteo y mindicador.cl no usan). |
| `.gitignore` | Contiene `.env`, `venv/` y `__pycache__/`. |
| `config/__init__.py` | Vacío (marca la carpeta como paquete). En `main` se llamaba `app_config.py` y estaba vacío: Git lo muestra como renombrado. |
| `config/configuracion_app.py` | ¿Lee las 4 variables? ¿Qué pasa si falta `DB_DSN`? (debe dar `ValueError` con el **nombre** de la variable, nunca el valor). ¿Por qué no hay setters? |

### 3.2 Base de datos: `sql/` y `database/` (≈ 1 h 30 min)

| Archivo | Qué verificar |
|---|---|
| `sql/crear_tablas.sql` | Las 8 tablas coinciden con el diagrama ER (nombres de columna, tipos, `NOT NULL`, `UNIQUE`, `CHECK`, `ON DELETE`). `salario_cifrado RAW(2000)`. `horas_trabajadas > 0 AND <= 24`. `UNIQUE(codigo, fecha)` en `indicador_economico`. |
| `database/conexion_bd.py` | ¿Por qué `__fallo_conexion` impide reintentar? (bloqueo ORA-28000 de FreeSQL). ¿Para qué sirve el `candado` (`RLock`)? ¿Qué hace `__exit__` si hubo error? |
| `database/repositorio_crud.py` | Clase abstracta con 5 `@abstractmethod`. Entender `_ejecutar()` línea por línea: cuándo hace `commit`, cuándo `rollback`, qué devuelve si falla (`None`). Revisar el diccionario `MENSAJES_ORA` (00001, 02290, 02291, 02292). |
| `database/repositorios.py` | Los 7 repositorios. Para cada uno: ¿implementa los 5 métodos? ¿El SQL usa parámetros? ¿`listar()` de usuarios **no** devuelve el hash? ¿Por qué `guardar_indicador` usa `MERGE`? ¿Qué hace `esta_asignado()` con `fecha_fin`? |

**Prueba:** `python -m test.prueba_conexion` y luego `python -m test.prueba_repositorios`
(debe dar **36 OK**). Esta segunda crea y borra datos de prueba en **tu** BD.

### 3.3 Modelos: `model/` (≈ 2 h)

Revisa una clase a la vez contra el diagrama. Son 9 archivos.

| Archivo | Qué verificar |
|---|---|
| `rol.py` | Enum `Permiso` con 6 valores (se quitó `GENERAR_INFORMES`). Tabla `PERMISOS_POR_ROL`: ADMINISTRADOR todos; GERENTE proyectos, horas y APIs; EMPLEADO solo horas. |
| `usuario.py` | `crear()` guarda solo el hash. `autenticar()`: bloquea al tercer intento fallido; si está bloqueado, devuelve `False` aunque la clave sea correcta. |
| `empleado.py` | **Nunca** guarda el salario en texto. `obtener_salario(solicitante, cifrado)` lanza `AccesoDenegadoError` sin `VER_SALARIOS`. `registrar_horas` exige estar asignado al proyecto. |
| `departamento.py` | Agregación con Empleado (0..1). `agregar_empleado` saca al empleado de su departamento anterior. |
| `proyecto.py` | Valida ciudad y moneda con `Validador`. `desasignar_empleado` **no borra**: finaliza la asignación (historial). |
| `asignacion.py` | `esta_activa()`: `fecha_fin` vacía o **posterior** a hoy. |
| `registro_tiempo.py` | Horas entre 0 y 24 y fecha no futura. |
| `dato_clima.py` | `es_apto_para_trabajo()`: 0 a 35 °C y sin tormenta/nieve. |
| `indicador_economico.py` | `convertir_desde_clp(monto)` **divide** por el valor (no multiplica). Ejemplo a mano: 1.000.000 CLP con dólar 1000 = 1000 USD. |

**Prueba:** `python -m test.prueba_modelos` (debe dar **32 OK**).

### 3.4 Seguridad: `security/` (≈ 1 h)

Aquí están los cambios sobre tu código. Revísalos con calma y **decide si estás de acuerdo**.

| Archivo | Qué verificar |
|---|---|
| `servicio_cifrado.py` | Formato guardado: `pbkdf2_sha512$210000$<sal>$<hash>`. ¿Por qué la sal es distinta en cada usuario? ¿Por qué `compare_digest` y no `==`? ¿Qué pasa si `FERNET_KEY` falta o es inválida? |
| `sesion.py` | Expira a los 30 minutos. `exigir_permiso()` revisa primero la sesión y después el permiso. `mensaje_seguro()` no dice qué rol o permiso faltó. |
| `validador.py` | Prueba a mano en la consola de Python: `validar_telefono("--------")` → `False`; `validar_ciudad("Osorno&lat=0")` → `False`; `validar_ciudad("O'Higgins")` → `True`; `validar_horas(True)` → `False`. |

### 3.5 Servicios: `service/` (≈ 1 h)

| Archivo | Qué verificar |
|---|---|
| `servicio_api.py` | `ServicioAPI("https://x")` debe dar `TypeError` (es abstracta). Todas las llamadas con `timeout`. Qué excepciones se convierten en `ErrorServicioExterno`. |
| `servicio_clima.py` | Dos llamadas (geocodificación + pronóstico). Ciudad inexistente → error 404 controlado. |
| `servicio_indicadores.py` | USD → `dolar`, EUR → `euro`, CLF → `uf`; CLP = 1.0; JPY → error controlado. |
| `tarea_programada.py` | Hilo daemon. Si una ciudad falla, sigue con las demás. Cada moneda se consulta una sola vez por ejecución. |

**Prueba:** `python -m test.prueba_servicios` (debe dar **13 OK**, necesita internet).

### 3.6 Programa principal: `main.py` (≈ 1 h 30 min)

Es el archivo más largo (≈ 700 líneas). Léelo por bloques: arranque → administrador inicial
→ login → menú → cada submenú → cierre en `finally`.

Luego haz esta **prueba manual completa** con `python main.py` y marca cada caso:

- [ ] 1. Con la tabla USUARIO vacía pide crear el administrador inicial.
- [ ] 2. La contraseña no se ve al escribirla (`getpass`).
- [ ] 3. Usuario inexistente y clave incorrecta muestran **el mismo** mensaje.
- [ ] 4. Tres claves incorrectas bloquean la cuenta (y sigue bloqueada al reiniciar el programa).
- [ ] 5. Crear un departamento, un proyecto (ciudad real, moneda USD) y un empleado con salario.
- [ ] 6. Correo repetido → `[WARNING] El registro ya existe` y el programa sigue.
- [ ] 7. Ver salario como ADMINISTRADOR → se muestra.
- [ ] 8. Crear un usuario GERENTE: no ve las opciones de empleados ni usuarios.
- [ ] 9. Crear un usuario EMPLEADO: solo ve registro de horas.
- [ ] 10. Registrar horas en un proyecto donde **no** está asignado → rechazado.
- [ ] 11. Registrar 25 horas → rechazado.
- [ ] 12. Consultar clima de la ciudad del proyecto → muestra si es apto.
- [ ] 13. Calcular pago en USD → muestra el monto convertido.
- [ ] 14. Ejecutar la rutina de las 08:00 dos veces → la segunda no duplica indicadores.
- [ ] 15. Eliminar un proyecto con horas registradas → mensaje de ORA-02292, no se cae.
- [ ] 16. Desbloquear la cuenta del caso 4 desde el menú Usuarios.
- [ ] 17. Ctrl+C cierra sin mostrar traceback.

### 3.7 Pruebas y documentación (≈ 45 min)

| Archivo | Qué verificar |
|---|---|
| `test/*.py` | Entender qué prueba cada script y qué hace `lanza_error()`. No usan `unittest` ni `pytest` (no vistos en clases). |
| `README.md` | Instrucciones correctas para alguien que recién descarga el proyecto. |
| `docs/manual_base_datos.md` | Sigue los pasos tal como están escritos: si algo no te funciona, corrígelo. |
| `docs/uso_ia.md` | Concuerda con los bloques de IA de cada `.py` y con la sección 8 del manual. |
| Manual técnico (Google Docs) | Secciones 3 a 7 coinciden con el código real (nombres de métodos, paquetes, tablas). |

**Punto de control 3:** las 4 pruebas en verde y los 17 casos manuales marcados.

---

## Fase 4. Corregir lo que encuentres (tiempo variable)

- Si encuentras un error, **corrígelo en la misma rama `integracion-main`** (después del
  commit del merge, ver Fase 5) con un commit pequeño por cada corrección, y anótalo en la
  tabla de la sección 6.
- Si **no estás de acuerdo** con un cambio que hice en tu código, **no lo reviertas solo**:
  anótalo y lo conversamos. Lo mismo al revés: yo no voy a cambiar nada tuyo sin avisarte.
- Después de cada corrección, vuelve a correr la prueba de esa capa.
- Si una IA te ayuda a corregir algo, agrega la fila en el bloque "Registro uso de IA" del
  archivo y en la sección 8 del manual.

---

## Fase 5. Confirmar la integración y abrir el Pull Request (≈ 30 min)

1. Con todo revisado, confirma el merge:
   ```powershell
   git commit -m "Integra rama Fernando-Valderas en main tras revision completa"
   ```
2. Sube la rama de integración:
   ```powershell
   git push -u origin integracion-main
   ```
3. En GitHub abre un **Pull Request** de `integracion-main` → `main`. En la descripción
   pega la tabla de la sección 6 con tus resultados.
4. **No hagas merge del PR todavía.** Lo revisamos juntos en llamada y lo aprobamos entre
   los dos. Nadie hace `push` directo a `main`.

**Punto de control 5:** PR abierto, con la tabla de revisión completa y sin conflictos.

---

## Fase 6. Documentación del manual (≈ 30 min)

En el manual técnico (Google Docs):

- **Sección 9 (Bitácora):** agrega tu fila con fecha, "Revisión completa del código e
  integración a main", archivos, el hash del commit del merge, problemas encontrados y
  criterios de rúbrica.
- **Sección 12.1:** actualiza el estado de cada criterio (los desplegables se cambian a mano).
- **Sección 12.3:** marca las tareas de integración como `[LISTO]`.

---

## 6. Tabla de registro de la revisión

Cópiala en el PR y complétala. Estado: ✅ correcto · ⚠️ corregido · ❓ para conversar.

| # | Archivo | Coincide con el diagrama | Lista general | Prueba | Estado | Observaciones |
|---|---|---|---|---|---|---|
| 1 | `requirements.txt` | — | | — | | |
| 2 | `.env.example` / `.gitignore` | — | | — | | |
| 3 | `config/configuracion_app.py` | | | conexión | | |
| 4 | `sql/crear_tablas.sql` | (ER) | | conexión | | |
| 5 | `database/conexion_bd.py` | | | conexión | | |
| 6 | `database/repositorio_crud.py` | | | repositorios | | |
| 7 | `database/repositorios.py` | | | repositorios | | |
| 8 | `model/rol.py` | | | modelos | | |
| 9 | `model/usuario.py` | | | modelos | | |
| 10 | `model/empleado.py` | | | modelos | | |
| 11 | `model/departamento.py` | | | modelos | | |
| 12 | `model/proyecto.py` | | | modelos | | |
| 13 | `model/asignacion.py` | | | modelos | | |
| 14 | `model/registro_tiempo.py` | | | modelos | | |
| 15 | `model/dato_clima.py` | | | modelos | | |
| 16 | `model/indicador_economico.py` | | | modelos | | |
| 17 | `security/servicio_cifrado.py` | | | modelos | | |
| 18 | `security/sesion.py` | | | modelos | | |
| 19 | `security/validador.py` | | | manual | | |
| 20 | `service/servicio_api.py` | | | servicios | | |
| 21 | `service/servicio_clima.py` | | | servicios | | |
| 22 | `service/servicio_indicadores.py` | | | servicios | | |
| 23 | `service/tarea_programada.py` | | | servicios | | |
| 24 | `main.py` | | | 17 casos | | |
| 25 | `test/` (4 scripts) | — | | todas | | |
| 26 | `README.md` y `docs/` | — | | — | | |

---

## Preguntas para preparar la defensa mientras revisas

Si puedes responder estas preguntas sin mirar el código, la revisión está bien hecha:

1. ¿Qué diferencia hay entre el hash de la contraseña y el cifrado del salario? ¿Por qué uno
   se puede revertir y el otro no?
2. ¿Qué pasa en Oracle y en Python si intento borrar un proyecto que tiene horas registradas?
3. ¿Por qué `RepositorioCRUD` y `ServicioAPI` son abstractas? ¿Qué pasa si las instancio?
4. ¿Dónde está el polimorfismo en el proyecto?
5. ¿Qué hace el `candado` de `ConexionBD` y por qué hace falta?
6. ¿Cómo evita la rutina de las 08:00 guardar dos veces el dólar del mismo día?
7. ¿Qué responde el sistema si Open-Meteo tarda más de 10 segundos?
8. ¿Por qué el login muestra el mismo mensaje si el usuario no existe o la clave está mal?
9. Nombra tres propuestas de la IA que se descartaron y explica por qué.
10. ¿Por qué `Empleado` no hereda de `Usuario`?

Cualquier duda me llamas. ¡Gracias, compañero!
