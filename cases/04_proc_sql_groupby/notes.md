from pathlib import Path

import numpy as np
import pandas as pd

src = Path("cases/01_data_step_basic/input/transactions.csv")
out = Path("cases/04_proc_sql_groupby/input/transactions.csv")
out.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(src)
rng = np.random.default_rng(4)

# Trampa 2: la mitad de los 'ATM' con espacio al final
atm = df.index[df["channel"] == "ATM"]
df.loc[atm[::2], "channel"] = "ATM "

# Trampa 1: más amounts nulos
df.loc[rng.choice(df.index, 6, replace=False), "amount"] = None

# Trampa 4: customer_id nulo en 3 filas, con amount chico para que pasen el WHERE
df.loc[df.index[:3], "customer_id"] = None
df.loc[df.index[:3], "amount"] = [100.0, None, 250.0]

df.to_csv(out, index=False)
print(f"Generado {out}: {len(df)} filas | amount nulos: {df['amount'].isna().sum()} "
      f"| 'ATM ': {(df['channel'] == 'ATM ').sum()}")