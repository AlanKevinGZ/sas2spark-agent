from pathlib import Path

import numpy as np
import pandas as pd

src = Path("cases/01_data_step_basic/input/transactions.csv")
out = Path("cases/05_retain_first_last/input/transactions.csv")
out.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(src)

# Trampa 3: customer_id nulo
df.loc[df.index[:3], "customer_id"] = None

# Trampa 1: amount nulo en la PRIMERA transacción (por fecha) de 5 clientes
con_id = df.dropna(subset=["customer_id"])
primeras = con_id.sort_values("trx_date", kind="stable").groupby("customer_id").head(1).index[:5]
df.loc[primeras, "amount"] = np.nan

# Trampa 2: empates de fecha dentro de un cliente
for cid in ["C003", "C007", "C011"]:
    idx = df.index[df["customer_id"] == cid]
    if len(idx) >= 2:
        df.loc[idx[1], "trx_date"] = df.loc[idx[0], "trx_date"]

# Trampa 6: fecha nula
idx5 = df.index[df["customer_id"] == "C005"]
if len(idx5):
    df.loc[idx5[0], "trx_date"] = None

df.to_csv(out, index=False)
print(f"Generado {out}: {len(df)} filas | amount nulos: {df['amount'].isna().sum()} "
      f"| trx_date nulas: {df['trx_date'].isna().sum()}")