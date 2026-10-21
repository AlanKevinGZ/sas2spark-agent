# Reglas de traducción SAS → PySpark

Estas reglas describen diferencias de comportamiento entre SAS y PySpark.
Aplícalas SIEMPRE que el código SAS use la construcción indicada.

---

## R1. `ne` / `^=` con texto faltante

**SAS:** un texto faltante (blank) CUMPLE `ne 'X'`, así que la fila se conserva.
**PySpark:** `!=` con null da null y la fila se descarta. Hay que agregar `isNull()`.

```sas
where status ne 'CANCELLED';
```
```python
df = df.filter((F.rtrim(F.col("status")) != "CANCELLED") | F.col("status").isNull())
```

---

## R2. Numérico faltante (`.`) en comparaciones

**SAS:** `.` es MENOR que cualquier número.
- `x < 5` o `x <= 5` → el faltante SÍ cumple.
- `x > 5` o `x >= 5` → el faltante NO cumple.

**PySpark:** null nunca cumple ninguna comparación.
Para `<` y `<=` agrega `| F.col("x").isNull()`. Para `>` y `>=` no hace falta.

```sas
if amount < 100 then flag = 1; else flag = 0;
```
```python
df = df.withColumn("flag",
    F.when((F.col("amount") < 100) | F.col("amount").isNull(), 1).otherwise(0))
```

En un `IF / ELSE IF / ELSE`, un faltante cae en la primera rama donde cumpla la regla anterior, o en el `ELSE`. En `F.when(...).otherwise(...)` un null cae en `otherwise`.

---

## R3. Espacios al final en textos

**SAS:** ignora los espacios al final al comparar (`'ATM '` = `'ATM'`).
**PySpark:** no los ignora. Usa `F.rtrim()` (quita solo los espacios al final) en las comparaciones de texto. No uses `F.trim()`, porque también quita los del inicio y SAS no lo hace.

```sas
if channel = 'ATM' then ...
```
```python
F.when(F.rtrim(F.col("channel")) == "ATM", ...)
```

---

## R4. `intnx('month', fecha, 0, 'b')`

**SAS:** regresa el primer día del mes de la fecha.
**PySpark:** `F.trunc(F.col("fecha"), "month")`.
Si la columna llega como texto, conviértela antes con `F.to_date(...)`.

---

## R5. No redondear si el SAS no redondea

**SAS:** `amount_mxn = amount * fx_rate;` NO redondea.
**PySpark:** NO agregues `F.round()` por tu cuenta, porque cambia valores y puede mover filas de segmento en los límites (999.6 → 1000).
Usa `F.round()` solo si el SAS usa `round()`.

---

## R6. `IF / ELSE IF / ELSE`

**SAS:** se evalúa en orden y la primera condición verdadera gana.
**PySpark:** usa una cadena de `F.when(...).when(...).otherwise(...)` en el MISMO orden.

```sas
if x >= 10000 then seg = 'HIGH';
else if x >= 1000 then seg = 'MEDIUM';
else seg = 'LOW';
```
```python
F.when(F.col("x") >= 10000, "HIGH").when(F.col("x") >= 1000, "MEDIUM").otherwise("LOW")
```

---

## R7. `KEEP` / `DROP`

**SAS:** `keep a b c;` conserva solo esas columnas; `drop` las elimina.
**PySpark:** `KEEP` → `df.select("a", "b", "c")` en el orden del `KEEP`. `DROP` → `df.drop(...)`.

---

## R8. `LENGTH` y `FORMAT`

**SAS:** `length x $6;` define el tamaño del texto; `format f yymmdd10.;` solo cambia cómo se muestra.
**PySpark:** ignóralos. No trunques textos ni conviertas fechas a texto por un `FORMAT`.
Una fecha con `yymmdd10.` se queda como tipo fecha (se escribe como `2026-01-01`).

---

## R9. `PROC IMPORT` con CSV

**SAS:**
```sas
proc import datafile="data/x.csv" out=work.x dbms=csv; getnames=yes; run;
```
**PySpark:**
```python
x = spark.read.option("header", True).option("inferSchema", True).csv(f"{INPUT_DIR}/x.csv")
```
Ignora la ruta original del SAS: usa siempre `INPUT_DIR` + el nombre del archivo.


## R10. `PROC SORT` y orden de los nulos

**SAS:** el output de `PROC SORT` queda ORDENADO por las variables del `BY`.
Los faltantes son el valor MENOR:
- `BY x` (ascendente) → faltantes PRIMERO.
- `BY DESCENDING x` → faltantes AL FINAL.

El sort de SAS es ESTABLE: con valores iguales en el `BY`, conserva el orden original del archivo.

**PySpark:** ordena el resultado final de forma explícita, en el mismo orden del `BY`:
- ascendente → `F.col("x").asc_nulls_first()`
- descendente → `F.col("x").desc_nulls_last()`

Para la estabilidad, agrega al leer una columna con el orden original y úsala como último criterio:
```python
df = df.withColumn("_row", F.monotonically_increasing_id())
```

---

## R11. `PROC SORT NODUPKEY`

**SAS:** conserva la PRIMERA fila de cada grupo del `BY`, según el orden que traía el dataset. Los faltantes del `BY` cuentan como UN solo grupo.

**PySpark:** NO uses `dropDuplicates()`, porque no garantiza cuál fila conserva. Usa una `Window` con el orden del sort anterior más `_row` como desempate:
```sas
proc sort data=a out=b; by id descending fecha; run;
proc sort data=b out=c nodupkey; by id; run;
```
```python
df = df.withColumn("_row", F.monotonically_increasing_id())
w = Window.partitionBy("id").orderBy(F.col("fecha").desc_nulls_last(), F.col("_row"))
c = (df.withColumn("_rn", F.row_number().over(w))
       .filter(F.col("_rn") == 1)
       .orderBy(F.col("id").asc_nulls_first())
       .drop("_rn", "_row"))
```

---

## R12. `MERGE` con `BY` (uno a muchos)

**SAS:** `MERGE` NO es un join normal. Lee las filas de cada tabla en orden, dentro de cada grupo del `BY`:

1. **Llaves nulas:** un faltante en el `BY` SÍ empata con otro faltante.
2. **`IN=`:** `in=a` vale 1 si la tabla `a` tiene filas en ese grupo del `BY` (en TODO el grupo).
   - `if a;` → left join; `if a and b;` → inner; sin `if` → full outer.
3. **Columnas en común (no `BY`):** la tabla que se lee DESPUÉS sobrescribe.
   En uno a muchos (`a` = muchos, `b` = uno):
   - en la PRIMERA fila del grupo gana el valor de `b`, AUNQUE sea faltante;
   - en las SIGUIENTES filas del grupo gana el valor de `a` (porque `b` ya no se vuelve a leer).
4. **Orden:** el output sale ordenado por el `BY` (faltantes primero) y, dentro del grupo, en el orden original de `a`.

**PySpark** (asumiendo que `b` tiene máximo una fila por llave):
```sas
data out; merge a(in=ina) b(in=inb); by id; if ina; flag = inb; run;
```
```python
a = a.withColumn("_row", F.monotonically_increasing_id())
b2 = (b.withColumnRenamed("id", "_b_id")
        .withColumnRenamed("col_comun", "_b_col_comun")
        .withColumn("_in_b", F.lit(1)))

j = a.join(b2, a["id"].eqNullSafe(b2["_b_id"]), "left")   # eqNullSafe: null empata con null

w = Window.partitionBy("id").orderBy("_row")
j = j.withColumn("_first", F.row_number().over(w) == 1)

j = (j.withColumn("col_comun",
          F.when(F.col("_first") & F.col("_in_b").isNotNull(), F.col("_b_col_comun"))
           .otherwise(F.col("col_comun")))
      .withColumn("flag", F.when(F.col("_in_b").isNotNull(), 1).otherwise(0)))

out = (j.orderBy(F.col("id").asc_nulls_first(), F.col("_row"))
        .drop("_b_id", "_b_col_comun", "_in_b", "_first", "_row"))
```
NO uses `coalesce` para las columnas comunes: SAS sí sobrescribe con faltante.

---

## R13. `RETAIN`, `FIRST.` / `LAST.` y acumulados

**SAS:** un DATA step con `BY` recorre las filas EN ORDEN. `FIRST.x` / `LAST.x` marcan la primera y la última fila de cada grupo. `RETAIN` (y los sum statements como `n + 1;`) conserva el valor entre filas.

**Funciones vs operadores con faltantes:**
- `a + b` → faltante si alguno es faltante.
- `sum(a, b)` → IGNORA faltantes (`sum(0, .) = 0`).

Un acumulado `total = sum(total, x)` que se reinicia en `first.` a 0 NUNCA es faltante: los faltantes cuentan como 0.

**PySpark:** usa una `Window` ordenada EXACTAMENTE como el `PROC SORT` previo, con `_row` para los empates (ver R10):
```sas
proc sort data=a out=s; by id fecha; run;
data out; set s; by id;
  retain total;
  if first.id then total = 0;
  total = sum(total, monto);
  n + 1;  if first.id then n = 1;
  es_ultimo = last.id;
run;
```
```python
df = df.withColumn("_row", F.monotonically_increasing_id())
w_order = [F.col("fecha").asc_nulls_first(), F.col("_row")]
w = Window.partitionBy("id").orderBy(*w_order)
w_acum = w.rowsBetween(Window.unboundedPreceding, Window.currentRow)

out = (df
    .withColumn("total", F.sum(F.coalesce(F.col("monto"), F.lit(0.0))).over(w_acum))  # sum() ignora faltantes
    .withColumn("n", F.row_number().over(w))
    .withColumn("_cnt", F.count(F.lit(1)).over(Window.partitionBy("id")))
    .withColumn("es_ultimo", F.when(F.col("n") == F.col("_cnt"), 1).otherwise(0))
    .orderBy(F.col("id").asc_nulls_first(), *w_order)
    .drop("_row", "_cnt"))
```
Usa `rowsBetween` (no `rangeBetween`): con empates en la fecha, `range` sumaría las filas empatadas juntas.

---

# Reglas del contrato (obligatorias)

1. `spark`, `F` (pyspark.sql.functions), `Window`, `INPUT_DIR` y `OUTPUT_PATH` YA EXISTEN. No crees SparkSession, no hagas imports de pyspark y no redefinas esas variables.
2. Lee todos los inputs desde `f"{INPUT_DIR}/<archivo>.csv"`.
3. Guarda SOLO el dataset final del programa con:
   `df_final.toPandas().to_csv(OUTPUT_PATH, index=False)`
4. Nombres y orden de columnas iguales al `KEEP` del SAS. Si no hay `KEEP`, conserva todas en el orden en que se crean.
5. No uses `.show()`, `print()` ni `spark.stop()`.
6. Responde SOLO con código Python dentro de un bloque ```python```, sin explicaciones.