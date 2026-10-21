# Bitácora de experimentos

Modelo: gemini-2.5-flash · temperature=0 · max_attempts=3

## Resultados por caso (corridas manuales)

| Caso | Sin regla | Con regla | Notas |
|---|---|---|---|
| 01 DATA step básico | — | 1 intento | — |
| 02 PROC SORT NODUPKEY | 2 intentos (falló por orden) | 1 intento (R10, R11) | Sin AQE coalesce el orden se rompe |
| 03 MERGE con IN= | ❌ 0/3 (columna común `branch`) | 1–2 intentos (R12) | La regla ayuda, pero no garantiza; el loop rescata |
| 04 PROC SQL GROUP BY | — | 1 intento | R2 generalizó a PROC SQL sin cambios |

## Evaluación automática (run_all.py --runs 1)

| Caso | baseline | rules | rules_loop |
|---|---|---|---|
| 01_data_step_basic | 0/1 (perdió 10 filas por nulls) | 1/1 | 1/1 |
| 02_proc_sort_nodupkey | 0/1 (orden) | 1/1 | 1/1 |
| 03_merge_left | 0/1 | 0/1 (`branch`) | 1/1 · 2 int. |
| **TOTAL** | **0/3** | **2/3** | **3/3** |

## Hallazgos

- Un LLM solo (baseline) falla en las trampas semánticas de SAS: nulls, orden y MERGE.
- Las reglas suben la tasa de éxito al primer intento; el loop de corrección rescata lo que las reglas no cubren.
- Con archivos chicos, Spark junta todo en una partición y el código no determinista pasa por suerte.
  El ejecutor fuerza particiones (maxPartitionBytes, sin coalesce de AQE) para exponerlo.
- Con una sola corrida no basta: el LLM varía entre corridas aun con temperature=0.

## Pendiente
- Evaluación con --runs 3 (casos 01–05).