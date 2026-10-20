from pathlib import Path

import pandas as pd

CASE = Path("cases/02_proc_sort_nodupkey")
df = pd.read_csv(CASE / "input" / "customer_snapshots.csv")
cols = list(df.columns)

# Columnas auxiliares para replicar el orden de SAS
df["_row"] = range(len(df))                   # orden original (SAS EQUALS)
df["_cid_null"] = df["customer_id"].isna()    # SAS: faltante va primero
df["_dt_null"] = df["updated_at"].isna()      # DESCENDING: faltante va al final

# BY customer_id DESCENDING updated_at
df = df.sort_values(
    ["_cid_null", "customer_id", "_dt_null", "updated_at", "_row"],
    ascending=[False, True, True, False, True],
)

# NODUPKEY BY customer_id: la primera de cada grupo (los nulos cuentan como un grupo)
latest = df.drop_duplicates(subset=["customer_id"], keep="first")[cols]

out = CASE / "expected" / "latest_customers.csv"
out.parent.mkdir(parents=True, exist_ok=True)
latest.to_csv(out, index=False)

# Verificación de las trampas
print("Filas de entrada:", len(df), "→ salida:", len(latest))
print("\nPrimera fila (debe ser customer_id nulo):")
print(latest.head(1).to_string(index=False))
print("\nEmpates (debe salir el que apareció primero en el archivo):")
print(latest[latest["customer_id"].isin(["C005", "C012", "C027"])].to_string(index=False))
print("\nNull dates:")
print(latest[latest["customer_id"].isin(["C041", "C042"])].to_string(index=False))