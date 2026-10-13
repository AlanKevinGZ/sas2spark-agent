from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("build_expected_01").master("local[*]").getOrCreate()

trx = (spark.read
       .option("header", True)
       .option("inferSchema", True)
       .csv("cases/01_data_step_basic/input/transactions.csv"))

# CAMBIO 1: trim en status
trx_clean = trx.filter(
    (F.trim(F.col("status")) != "CANCELLED") | F.col("status").isNull()
)

# CAMBIO 2: sin round
trx_clean = trx_clean.withColumn("amount_mxn", F.col("amount") * F.col("fx_rate"))

trx_clean = trx_clean.withColumn(
    "segment",
    F.when(F.col("amount_mxn") >= 10000, "HIGH")
     .when(F.col("amount_mxn") >= 1000, "MEDIUM")
     .otherwise("LOW")
)

trx_clean = trx_clean.withColumn("trx_month", F.trunc(F.col("trx_date"), "month"))

trx_clean = trx_clean.withColumn(
    "flag_atm",
    F.when((F.col("channel") == "ATM") & (F.col("amount_mxn") > 8000), 1).otherwise(0)
)

trx_clean = trx_clean.select(
    "trx_id", "customer_id", "trx_date", "trx_month", "amount_mxn",
    "segment", "channel", "status", "flag_atm"
)

# Verificación
print("Total:", trx_clean.count())                      # esperado 265
trx_clean.groupBy("segment").count().show()             # HIGH 42 · MEDIUM 123 · LOW 100
print("flag_atm:", trx_clean.filter(F.col("flag_atm") == 1).count())  # esperado 13

# CAMBIO 3: guardar con pandas (evita winutils en Windows)
trx_clean.toPandas().to_csv("cases/01_data_step_basic/expected/trx_clean.csv", index=False)
print("CSV guardado")

spark.stop()