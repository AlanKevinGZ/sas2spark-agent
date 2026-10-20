import re
from pathlib import Path

import pandas as pd

RULES_DIR = Path("rules")


# ---------- PLANTILLAS ----------
SYSTEM_TEMPLATE = """Eres un ingeniero de datos experto en migrar código SAS a PySpark.
Tu objetivo: que el código PySpark produzca EXACTAMENTE el mismo dataset que el
programa SAS: mismas filas, mismas columnas y mismos valores.

Sigue estas reglas:

{rules}
"""

TRANSLATE_TEMPLATE = """Traduce este programa SAS a PySpark.

## Programa SAS
```sas
{sas_code}
```

## Archivos de entrada (disponibles en INPUT_DIR)
{inputs_info}

## Salida
Guarda el dataset final en OUTPUT_PATH. El archivo esperado se llama `{output_file}`.

Responde solo con el bloque ```python```.
"""

FIX_TEMPLATE = """Tu traducción anterior NO produce el resultado correcto.
## Intentos anteriores que también fallaron (NO repitas estos errores)
{previous_problems}

## Programa SAS original
```sas
{sas_code}
```

## Tu código anterior
```python
{previous_code}
```

## Problema detectado
{problem}

## Archivos de entrada (disponibles en INPUT_DIR)
{inputs_info}

Analiza la causa del problema. Revisa sobre todo las reglas de nulls, espacios
y redondeos. Regresa el código COMPLETO corregido.
Responde solo con el bloque ```python```.
"""


# ---------- HELPERS ----------
def load_rules(use_rules=True):
    """Contrato siempre; reglas SAS solo si use_rules=True."""
    contract = (RULES_DIR / "contract.md").read_text(encoding="utf-8")
    if not use_rules:
        return contract
    semantics = (RULES_DIR / "sas_semantics.md").read_text(encoding="utf-8")
    return semantics + "\n\n" + contract

def describe_inputs(input_dir, files, sample_rows=3):
    """Resume cada CSV de entrada: columnas, tipos, nulls y ejemplos."""
    partes = []
    for name in files:
        df = pd.read_csv(Path(input_dir) / name, nrows=5000)
        cols = "\n".join(
            f"  - {c}: {df[c].dtype}, nulls={int(df[c].isna().sum())}"
            for c in df.columns
        )
        partes.append(
            f"### {name}\nColumnas:\n{cols}\n"
            f"Ejemplo de filas:\n```\n{df.head(sample_rows).to_string(index=False)}\n```"
        )
    return "\n\n".join(partes)


def extract_code(text):
    """Saca el código del bloque ```python ... ``` de la respuesta del LLM."""
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    return (match.group(1) if match else text).strip()


# ---------- CONSTRUCTORES DE MENSAJES ----------
def build_translate_messages(sas_code, inputs_info, output_file, use_rules=True):
    return [
        ("system", SYSTEM_TEMPLATE.format(rules=load_rules(use_rules))),
        ("human", TRANSLATE_TEMPLATE.format(
            sas_code=sas_code,
            inputs_info=inputs_info,
            output_file=output_file,
        )),
    ]


def build_fix_messages(sas_code, inputs_info, previous_code, problem,
                       previous_problems="Ninguno", use_rules=True):
    return [
        ("system", SYSTEM_TEMPLATE.format(rules=load_rules(use_rules))),
        ("human", FIX_TEMPLATE.format(
            sas_code=sas_code,
            inputs_info=inputs_info,
            previous_code=previous_code,
            problem=problem,
            previous_problems=previous_problems,
        )),
    ]