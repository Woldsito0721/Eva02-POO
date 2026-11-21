-- =====================================================================
-- EcoTech Solutions - Creación de las 8 tablas (Oracle FreeSQL)
-- Ejecutar completo con "Run Script". Se puede ejecutar varias veces:
-- el bloque inicial borra las tablas si ya existen.
-- =====================================================================

-- 1. Borrado previo (solo las tablas del sistema, si existen)
BEGIN
    FOR t IN (
        SELECT table_name FROM user_tables
        WHERE table_name IN (
            'INDICADOR_ECONOMICO', 'DATO_CLIMA', 'REGISTRO_TIEMPO', 'ASIGNACION',
            'USUARIO', 'PROYECTO', 'EMPLEADO', 'DEPARTAMENTO'
        )
    ) LOOP
        EXECUTE IMMEDIATE 'DROP TABLE ' || t.table_name || ' CASCADE CONSTRAINTS PURGE';
    END LOOP;
END;
/

-- 2. DEPARTAMENTO (la FK al gerente se agrega después de crear EMPLEADO)
CREATE TABLE departamento (
    id_departamento NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre          VARCHAR2(100) NOT NULL,
    id_gerente      NUMBER        NOT NULL,
    CONSTRAINT uq_departamento_nombre UNIQUE (nombre)
);

-- 3. EMPLEADO
CREATE TABLE empleado (
    id_empleado           NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre                VARCHAR2(100) NOT NULL,
    direccion             VARCHAR2(200),
    telefono              VARCHAR2(20),
    correo                VARCHAR2(120) NOT NULL,
    fecha_inicio_contrato DATE          NOT NULL,
    salario_cifrado       RAW(2000)     NOT NULL,
    id_departamento       NUMBER,
    CONSTRAINT uq_empleado_correo UNIQUE (correo),
    -- Borrar un departamento deja a sus empleados sin departamento
    CONSTRAINT fk_empleado_departamento FOREIGN KEY (id_departamento)
        REFERENCES departamento (id_departamento) ON DELETE SET NULL
);

-- Gerente: sin ON DELETE, Oracle impide borrar a un gerente (ORA-02292)
ALTER TABLE departamento ADD CONSTRAINT fk_departamento_gerente
    FOREIGN KEY (id_gerente) REFERENCES empleado (id_empleado);

-- 4. USUARIO (cuenta de acceso de un empleado)
CREATE TABLE usuario (
    id_usuario        NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_usuario    VARCHAR2(50)  NOT NULL,
    hash_contrasena   VARCHAR2(255) NOT NULL,
    intentos_fallidos NUMBER(2)     DEFAULT 0 NOT NULL,
    bloqueado         NUMBER(1)     DEFAULT 0 NOT NULL,
    rol               VARCHAR2(30)  NOT NULL,
    id_empleado       NUMBER        NOT NULL,
    CONSTRAINT uq_usuario_nombre   UNIQUE (nombre_usuario),
    CONSTRAINT uq_usuario_empleado UNIQUE (id_empleado),
    CONSTRAINT ck_usuario_bloqueado CHECK (bloqueado IN (0, 1)),
    CONSTRAINT ck_usuario_rol CHECK (rol IN ('ADMINISTRADOR', 'GERENTE', 'EMPLEADO')),
    -- Borrar un empleado borra su cuenta de usuario
    CONSTRAINT fk_usuario_empleado FOREIGN KEY (id_empleado)
        REFERENCES empleado (id_empleado) ON DELETE CASCADE
);

-- 5. PROYECTO
CREATE TABLE proyecto (
    id_proyecto  NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre       VARCHAR2(100) NOT NULL,
    descripcion  VARCHAR2(500),
    fecha_inicio DATE          NOT NULL,
    pais         VARCHAR2(60)  NOT NULL,
    ciudad       VARCHAR2(80)  NOT NULL,
    moneda       VARCHAR2(10)  NOT NULL
);

-- 6. ASIGNACION (empleado <-> proyecto). Sin ON DELETE: protege el historial
CREATE TABLE asignacion (
    id_asignacion    NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_empleado      NUMBER       NOT NULL,
    id_proyecto      NUMBER       NOT NULL,
    rol_en_proyecto  VARCHAR2(60),
    fecha_asignacion DATE         NOT NULL,
    fecha_fin        DATE,
    CONSTRAINT ck_asignacion_fechas CHECK (fecha_fin IS NULL OR fecha_fin >= fecha_asignacion),
    CONSTRAINT fk_asignacion_empleado FOREIGN KEY (id_empleado) REFERENCES empleado (id_empleado),
    CONSTRAINT fk_asignacion_proyecto FOREIGN KEY (id_proyecto) REFERENCES proyecto (id_proyecto)
);

-- 7. REGISTRO_TIEMPO. Sin ON DELETE: protege las horas registradas
CREATE TABLE registro_tiempo (
    id_registro      NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_empleado      NUMBER        NOT NULL,
    id_proyecto      NUMBER        NOT NULL,
    fecha            DATE          NOT NULL,
    horas_trabajadas NUMBER(4,2)   NOT NULL,
    descripcion      VARCHAR2(300),
    CONSTRAINT ck_registro_horas CHECK (horas_trabajadas > 0 AND horas_trabajadas <= 24),
    CONSTRAINT fk_registro_empleado FOREIGN KEY (id_empleado) REFERENCES empleado (id_empleado),
    CONSTRAINT fk_registro_proyecto FOREIGN KEY (id_proyecto) REFERENCES proyecto (id_proyecto)
);

-- 8. DATO_CLIMA (rutina de las 08:00)
CREATE TABLE dato_clima (
    id_clima       NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_proyecto    NUMBER       NOT NULL,
    ciudad         VARCHAR2(80) NOT NULL,
    temperatura    NUMBER(5,2),
    humedad        NUMBER(3),
    estado         VARCHAR2(60),
    fecha_consulta TIMESTAMP    DEFAULT SYSTIMESTAMP NOT NULL,
    CONSTRAINT ck_clima_humedad CHECK (humedad BETWEEN 0 AND 100),
    -- Borrar un proyecto borra su historial de clima
    CONSTRAINT fk_clima_proyecto FOREIGN KEY (id_proyecto)
        REFERENCES proyecto (id_proyecto) ON DELETE CASCADE
);

-- 9. INDICADOR_ECONOMICO (sin FK; un valor por código y fecha)
CREATE TABLE indicador_economico (
    id_indicador NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo       VARCHAR2(10)  NOT NULL,
    valor        NUMBER(14,4)  NOT NULL,
    fecha        DATE          NOT NULL,
    CONSTRAINT uq_indicador_codigo_fecha UNIQUE (codigo, fecha)
);

-- Verificación: deben aparecer 8 tablas
SELECT table_name FROM user_tables
WHERE table_name IN ('DEPARTAMENTO', 'EMPLEADO', 'USUARIO', 'PROYECTO', 'ASIGNACION',
                     'REGISTRO_TIEMPO', 'DATO_CLIMA', 'INDICADOR_ECONOMICO')
ORDER BY table_name;
