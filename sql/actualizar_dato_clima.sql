-- =====================================================================
-- EcoTech Solutions - Actualización de DATO_CLIMA (23-11)
-- Para una base que YA tiene las tablas creadas: NO borra ningún dato.
-- El clima ahora se consulta por ciudad, así que id_proyecto pasa a ser opcional.
-- Ejecutar una sola vez en FreeSQL (SQL Worksheet → Run Script).
-- =====================================================================

ALTER TABLE dato_clima MODIFY (id_proyecto NULL);

-- Verificación: la columna ID_PROYECTO debe mostrar NULLABLE = Y
SELECT column_name, nullable FROM user_tab_columns
WHERE table_name = 'DATO_CLIMA' AND column_name = 'ID_PROYECTO';
