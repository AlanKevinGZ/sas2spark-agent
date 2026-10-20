import random
from pathlib import Path

import pandas as pd

random.seed(7)
DIR = Path("cases/03_merge_left/input")
DIR.mkdir(parents=True, exist_ok=True)

branches = ["CDMX", "GDL", "MTY", "PUE"]
segments = ["RETAIL", "PYME", "PREMIUM"]

# customers: C001..C025 (C021..C025 no tienen cuentas)
customers = []
for i in range(1, 26):
    customers.append({"customer_id": f"C{i:03d}", "name": f"Cliente {i}",
                      "segment": random.choice(segments),
                      "branch": random.choice(branches)})
customers[2]["branch"] = None        # Trampa 4: C003 con branch faltante
customers.append({"customer_id": None, "name": "SIN_ID", "segment": "RETAIL", "branch": "CDMX"})  # Trampa 2

# accounts: C001..C020 con 1 a 4 cuentas cada uno
accounts = []
n = 1
for i in range(1, 21):
    for _ in range(random.randint(1, 4)):
        accounts.append({"account_id": f"A{n:04d}", "customer_id": f"C{i:03d}",
                         "branch": random.choice(branches),
                         "balance": round(random.uniform(100, 90000), 2)})
        n += 1
# Trampa 5: cuentas de un cliente que no existe
for _ in range(2):
    accounts.append({"account_id": f"A{n:04d}", "customer_id": "C030",
                     "branch": "GDL", "balance": 500.0}); n += 1
# Trampa 2: cuentas sin customer_id
for _ in range(2):
    accounts.append({"account_id": f"A{n:04d}", "customer_id": None,
                     "branch": "MTY", "balance": 50.0}); n += 1

random.shuffle(accounts)
random.shuffle(customers)
pd.DataFrame(accounts).to_csv(DIR / "accounts.csv", index=False)
pd.DataFrame(customers).to_csv(DIR / "customers.csv", index=False)
print(f"accounts: {len(accounts)} filas | customers: {len(customers)} filas")