# Reglas del contrato (obligatorias)

1. `spark`, `F` (pyspark.sql.functions), `Window`, `INPUT_DIR` y `OUTPUT_PATH` YA EXISTEN. No crees SparkSession, no hagas imports de pyspark y no redefinas esas variables.
2. Lee todos los inputs desde `f"{INPUT_DIR}/<archivo>.csv"`.
3. Guarda SOLO el dataset final del programa con:
   `df_final.toPandas().to_csv(OUTPUT_PATH, index=False)`
4. Nombres y orden de columnas iguales al `KEEP` del SAS. Si no hay `KEEP`, conserva todas en el orden en que se crean.
5. No uses `.show()`, `print()` ni `spark.stop()`.
6. Responde SOLO con código Python dentro de un bloque ```python```, sin explicaciones.