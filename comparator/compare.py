from pathlib import Path
import json

import numpy as np
import pandas as pd



def load_case_config(case_dir):
    """Lee el case.json de un caso."""
    with open(Path(case_dir) / "case.json", encoding="utf-8") as f:
        return json.load(f)


def _sort_rows(df, keys, check_order):
    """Ordena las filas para poder comparar sin importar el orden."""
    if check_order:                      # el orden importa: no tocar
        return df.reset_index(drop=True)

    if keys:                             # hay llave: ordenar por ella
        return df.sort_values(keys, na_position="last").reset_index(drop=True)

    # Sin llave: ordenar por TODAS las columnas.
    # Se usa una copia con números redondeados solo para decidir el orden,
    # así 1000.0000001 y 1000.0 quedan en la misma posición.
    tmp = df.copy()
    for c in tmp.select_dtypes("number").columns:
        tmp[c] = tmp[c].round(6)
    order = tmp.sort_values(list(tmp.columns), na_position="last").index
    return df.loc[order].reset_index(drop=True)


def _diff_mask(s_exp, s_gen):
    """Regresa True en las filas donde la columna es distinta."""
    if pd.api.types.is_numeric_dtype(s_exp) and pd.api.types.is_numeric_dtype(s_gen):
        iguales = np.isclose(
            s_exp.to_numpy(dtype=float),
            s_gen.to_numpy(dtype=float),
            rtol=1e-6, atol=1e-6,
            equal_nan=True,              # NaN == NaN cuenta como igual
        )
    else:
        a = s_exp.astype("string")
        b = s_gen.astype("string")
        iguales = ((a == b) | (a.isna() & b.isna())).fillna(False).to_numpy()
    return ~iguales


def compare_csv(csv_esperado, csv_generado, config=None):
    config = config or {}
    keys = config.get("keys") or []
    check_order = config.get("check_order", False)

    # 1) ¿Existe el archivo generado?
    if not Path(csv_generado).exists():
        return {"ok": False, "reason": f"No se generó el archivo de salida: {csv_generado}"}

    try:
        df_exp = pd.read_csv(csv_esperado)
        df_gen = pd.read_csv(csv_generado)
    except Exception as e:
        return {"ok": False, "reason": f"No se pudo leer un CSV: {e}"}

    # 2) ¿Mismas columnas?
    cols_exp, cols_gen = set(df_exp.columns), set(df_gen.columns)
    if cols_exp != cols_gen:
        faltan = sorted(cols_exp - cols_gen)
        sobran = sorted(cols_gen - cols_exp)
        return {"ok": False, "reason": f"Columnas distintas. Faltan: {faltan}. Sobran: {sobran}"}

    # 3) ¿Mismo número de filas?
    n_exp, n_gen = len(df_exp), len(df_gen)
    if n_exp != n_gen:
        dif = n_gen - n_exp
        detalle = f"sobran {dif}" if dif > 0 else f"faltan {-dif}"
        return {"ok": False, "reason": f"Filas esperadas: {n_exp}, obtenidas: {n_gen} ({detalle})"}

    # Validar que las llaves existan
    llaves_invalidas = [k for k in keys if k not in cols_exp]
    if llaves_invalidas:
        return {"ok": False, "reason": f"Las keys de case.json no existen en el CSV: {llaves_invalidas}"}

    # 4) ¿Mismos valores?
    cols = sorted(cols_exp)
    df_exp = _sort_rows(df_exp[cols], keys, check_order)
    df_gen = _sort_rows(df_gen[cols], keys, check_order)

    problemas = []
    for c in cols:
        mask = _diff_mask(df_exp[c], df_gen[c])
        n = int(mask.sum())
        if n:
            i = int(np.argmax(mask))     # primera fila distinta
            ident = f"{keys[0]}={df_exp.loc[i, keys[0]]}" if keys else f"fila {i}"
            problemas.append(
                f"'{c}' difiere en {n} filas "
                f"(ej. {ident}: esperado={df_exp.loc[i, c]}, obtenido={df_gen.loc[i, c]})"
            )

    if problemas:
        if check_order:
            exp_s = _sort_rows(df_exp, keys, False)
            gen_s = _sort_rows(df_gen, keys, False)
            mismo_contenido = not any(
                _diff_mask(exp_s[c], gen_s[c]).any() for c in cols
            )
            if mismo_contenido:
                col_orden = keys[0] if keys else cols[0]
                return {
                    "ok": False,
                    "reason": (
                        "Las filas y los valores son CORRECTOS, pero el ORDEN no coincide. "
                        f"Los primeros 5 '{col_orden}' esperados: {df_exp[col_orden].head(5).tolist()}; "
                        f"obtenidos: {df_gen[col_orden].head(5).tolist()}. "
                        "Ordena el resultado final como lo hace SAS (los faltantes van primero)."
                    ),
                }

        return {"ok": False, "reason": "Valores distintos: " + "; ".join(problemas)}

    return {"ok": True, "reason": "Los CSV son iguales"}
