from pathlib import Path

import pandas as pd

CASE = Path("cases/05_retain_first_last")
df = pd.read_csv(CASE / "input" / "transactions.csv")

# PROC SORT BY customer_id trx_date: faltantes primero, estable
df["_row"] = range(len(df))
df["_cn"] = df["customer_id"].isna()
df["_dn"] = df["trx_date"].isna()
df = df.sort_values(
    ["_cn", "customer_id", "_dn", "trx_date", "_row"],
    ascending=[False, True, False, True, True],
).reset_index(drop=True)

# Llave de grupo (los nulos cuentan como un grupo)
key = df["customer_id"].fillna("__NULL__")
g = df.groupby(key, sort=False)

# running_total = sum(running_total, amount), iniciando en 0 → faltantes cuentan como 0
df["running_total"] = df["amount"].fillna(0).groupby(key, sort=False).cumsum()
df["n_seq"] = g.cumcount() + 1
df["is_last"] = (df["n_seq"] == g["trx_id"].transform("size")).astype(int)

cols = ["customer_id", "trx_id", "trx_date", "amount", "running_total", "n_seq", "is_last"]
res = df[cols]

dest = CASE / "expected" / "cust_running.csv"
dest.parent.mkdir(parents=True, exist_ok=True)
res.to_csv(dest, index=False)

# Verificación
print(f"Filas: {len(res)}")
print("\nGrupo nulo (va primero):")
print(res[res["customer_id"].isna()].to_string(index=False))
print("\nPrimeras filas con amount nulo (running_total NO debe ser nulo):")
print(res[res["amount"].isna()].head(5).to_string(index=False))
print("\nC005 (fecha nula primero) y C003 (empate):")
print(res[res["customer_id"].isin(["C005", "C003"])].head(8).to_string(index=False))