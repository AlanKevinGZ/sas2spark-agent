import random
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

random.seed(42)
OUT = Path("cases/02_proc_sort_nodupkey/input/customer_snapshots.csv")
OUT.parent.mkdir(parents=True, exist_ok=True)

plans = ["BASIC", "GOLD", "PLATINUM"]
start = date(2026, 1, 1)
rows = []

# Datos normales: 40 clientes con 1 a 5 versiones cada uno
for i in range(1, 41):
    cid = f"C{i:03d}"
    for _ in range(random.randint(1, 5)):
        d = start + timedelta(days=random.randint(0, 180))
        rows.append({"customer_id": cid, "updated_at": d.isoformat(),
                     "plan": random.choice(plans),
                     "balance": round(random.uniform(0, 50000), 2)})

# Trampa 2: empate en la fecha más reciente
for cid in ["C005", "C012", "C027"]:
    rows.append({"customer_id": cid, "updated_at": "2026-12-31", "plan": "TIE_A", "balance": 1.0})
    rows.append({"customer_id": cid, "updated_at": "2026-12-31", "plan": "TIE_B", "balance": 2.0})

# Trampa 3: customer_id nulo (3 filas → SAS deja solo 1)
for p in ["NULL_1", "NULL_2", "NULL_3"]:
    rows.append({"customer_id": None, "updated_at": "2026-05-01", "plan": p, "balance": 0.0})

# Trampa 4: updated_at nulo
rows.append({"customer_id": "C041", "updated_at": None, "plan": "ONLY_NULL_DATE", "balance": 10.0})
rows.append({"customer_id": "C042", "updated_at": None, "plan": "NULL_DATE", "balance": 20.0})
rows.append({"customer_id": "C042", "updated_at": "2026-02-01", "plan": "WITH_DATE", "balance": 30.0})

random.shuffle(rows)   # desordenar: el orden original importa para los empates
pd.DataFrame(rows).to_csv(OUT, index=False)
print(f"Generado {OUT} con {len(rows)} filas")