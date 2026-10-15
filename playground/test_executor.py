from pathlib import Path

from agent.executor import run_pyspark
from comparator.compare import compare_csv, load_case_config

CASE = Path("cases/01_data_step_basic")
config = load_case_config(CASE)
OUT_DIR = Path("outputs") / CASE.name

esperado = CASE / "expected" / config["output_file"]
generado = OUT_DIR / config["output_file"]

# ---- Código BUENO: usa spark, INPUT_DIR y OUTPUT_PATH ----
codigo_bueno = '''
trx = (spark.read.option("header", True).option("inferSchema", True)
       .csv(f"{INPUT_DIR}/transactions.csv"))

df = trx.filter((F.trim(F.col("status")) != "CANCELLED") | F.col("status").isNull())
df = df.withColumn("amount_mxn", F.col("amount") * F.col("fx_rate"))
df = df.withColumn("segment",
        F.when(F.col("amount_mxn") >= 10000, "HIGH")
         .when(F.col("amount_mxn") >= 1000, "MEDIUM")
         .otherwise("LOW"))
df = df.withColumn("trx_month", F.trunc("trx_date", "month"))
df = df.withColumn("flag_atm",
        F.when((F.col("channel") == "ATM") & (F.col("amount_mxn") > 8000), 1).otherwise(0))
df = df.select("trx_id", "customer_id", "trx_date", "trx_month", "amount_mxn",
               "segment", "channel", "status", "flag_atm")

df.toPandas().to_csv(OUTPUT_PATH, index=False)
'''

# ---- Código ROTO: columna que no existe ----
codigo_roto = '''
trx = spark.read.option("header", True).csv(f"{INPUT_DIR}/transactions.csv")
trx.select("columna_que_no_existe").show()
'''

print("=== Prueba 1: código bueno ===")
r = run_pyspark(codigo_bueno, CASE / "input", generado, OUT_DIR / "generated.py")
print("Ejecución:", r)
print("Comparación:", compare_csv(esperado, generado, config))

print("\n=== Prueba 2: código roto ===")
r = run_pyspark(codigo_roto, CASE / "input", generado, OUT_DIR / "generated.py")
print("Ejecución ok:", r["ok"])
print("Error capturado:\n", r["error"])