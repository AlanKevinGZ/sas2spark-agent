from pathlib import Path

import pandas as pd

CASE = Path("cases/04_proc_sql_groupby")
df = pd.read_csv(CASE / "input" / "transactions.csv")

# WHERE amount < 1000 → en SAS el faltante es el menor valor: SÍ cumple
f = df[(df["amount"] < 1000) | df["amount"].isna()].copy()

# channel = 'ATM' → SAS ignora espacios al final
f["_is_atm"] = (f["channel"].str.rstrip() == "ATM").astype(int)

g = f.groupby("customer_id", dropna=False)          # nulo = un grupo
res = pd.DataFrame({
    "n_trx":         g.size(),
    "n_with_amount": g["amount"].count(),
    "total_amount":  g["amount"].sum(min_count=1),  # todo faltante → faltante
    "avg_amount":    g["amount"].mean(),
    "last_trx":      g["trx_date"].max(),
    "n_atm":         g["_is_atm"].sum(),
}).reset_index()

res = res[res["n_trx"] >= 2]                                         # HAVING
res = res.sort_values("customer_id", na_position="first")            # ORDER BY

dest = CASE / "expected" / "cust_summary.csv"
dest.parent.mkdir(parents=True, exist_ok=True)
res.to_csv(dest, index=False)

# Verificación
sin_null = df[df["amount"] < 1000]
print(f"Filas que pasan el WHERE: SAS={len(f)} vs SQL estándar={len(sin_null)} "
      f"(diferencia = {len(f) - len(sin_null)} nulos)")
print(f"Clientes en el resumen: {len(res)}")
print("\nPrimeras filas:")
print(res.head(5).to_string(index=False))