from pathlib import Path

import pandas as pd

from comparator.compare import compare_csv, load_case_config

CASE = Path("cases/01_data_step_basic")
config = load_case_config(CASE)
esperado = CASE / "expected" / config["output_file"]

tmp = Path("outputs/test_compare")
tmp.mkdir(parents=True, exist_ok=True)
df = pd.read_csv(esperado)


def probar(nombre, ruta):
    r = compare_csv(esperado, ruta, config)
    print(f"[{'OK ' if r['ok'] else 'ERR'}] {nombre}\n      {r['reason']}\n")


# A) contra sí mismo → debe pasar
probar("Idéntico", esperado)

# B) filas en otro orden → debe pasar (se reordenan)
df.sample(frac=1, random_state=1).to_csv(tmp / "b.csv", index=False)
probar("Filas desordenadas", tmp / "b.csv")

# C) un valor cambiado → debe fallar en amount_mxn
d = df.copy(); d.loc[5, "amount_mxn"] += 100
d.to_csv(tmp / "c.csv", index=False)
probar("Valor cambiado", tmp / "c.csv")

# D) falta una columna → debe fallar en columnas
df.drop(columns=["segment"]).to_csv(tmp / "d.csv", index=False)
probar("Columna faltante", tmp / "d.csv")

# E) faltan filas → debe fallar en conteo
df.head(250).to_csv(tmp / "e.csv", index=False)
probar("Filas faltantes", tmp / "e.csv")

# F) archivo que no existe → debe fallar
probar("Sin archivo", tmp / "no_existe.csv")