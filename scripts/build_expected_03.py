from pathlib import Path

import pandas as pd

CASE = Path("cases/03_merge_left")
acc = pd.read_csv(CASE / "input" / "accounts.csv")
cus = pd.read_csv(CASE / "input" / "customers.csv")


def sas_sort(df, by):
    """PROC SORT: nulos primero y orden estable."""
    df = df.copy()
    df["_row"] = range(len(df))
    df["_null"] = df[by].isna()
    return df.sort_values(["_null", by, "_row"], ascending=[False, True, True])


acc_s = sas_sort(acc, "customer_id")
cus_s = sas_sort(cus, "customer_id")

acc_vars = list(acc.columns)
cus_vars = list(cus.columns)
out_cols = acc_vars + [c for c in cus_vars if c not in acc_vars] + ["has_customer"]

NULL = "__NULL__"
key = lambda v: NULL if pd.isna(v) else v

# Agrupar por llave respetando el orden
ga_all, gb_all = {}, {}
for r in acc_s[acc_vars].to_dict("records"):
    ga_all.setdefault(key(r["customer_id"]), []).append(r)
for r in cus_s[cus_vars].to_dict("records"):
    gb_all.setdefault(key(r["customer_id"]), []).append(r)

todas = set(ga_all) | set(gb_all)
orden = ([NULL] if NULL in todas else []) + sorted(k for k in todas if k != NULL)

out = []
for k in orden:
    ga, gb = ga_all.get(k, []), gb_all.get(k, [])
    in_a, in_b = len(ga) > 0, len(gb) > 0
    pdv = {c: None for c in out_cols}            # nuevo grupo BY → todo a faltante
    for i in range(max(len(ga), len(gb))):
        if i < len(ga):
            pdv.update(ga[i])                    # lee accounts
        if i < len(gb):
            pdv.update(gb[i])                    # lee customers (sobrescribe comunes)
        if in_a:                                 # if a;
            fila = dict(pdv)
            fila["has_customer"] = int(in_b)     # has_customer = b;
            out.append(fila)

res = pd.DataFrame(out, columns=out_cols)
dest = CASE / "expected" / "acct_enriched.csv"
dest.parent.mkdir(parents=True, exist_ok=True)
res.to_csv(dest, index=False)

# Verificación de trampas
print(f"Cuentas: {len(acc)} → salida: {len(res)} (deben ser iguales por 'if a')")
print("\nPrimeras filas (customer_id nulo, deben tener name=SIN_ID):")
print(res.head(2).to_string(index=False))
print("\nC003 (primera fila branch vacío; siguientes, el de accounts):")
print(res[res["customer_id"] == "C003"].to_string(index=False))
print("\nC030 (cliente inexistente → has_customer=0, name vacío):")
print(res[res["customer_id"] == "C030"].to_string(index=False))
print("\nUn cliente con varias cuentas (ver branch):")
multi = res["customer_id"].value_counts()
cid = multi[multi > 2].index[0]
print(res[res["customer_id"] == cid].to_string(index=False))