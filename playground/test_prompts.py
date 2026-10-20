from pathlib import Path

from agent.prompts import build_translate_messages, describe_inputs, extract_code
from comparator.compare import load_case_config

CASE = Path("cases/01_data_step_basic")
config = load_case_config(CASE)
sas_code = (CASE / "program.sas").read_text(encoding="utf-8")
inputs_info = describe_inputs(CASE / "input", config["input_files"])

messages = build_translate_messages(sas_code, inputs_info, config["output_file"])

print("=" * 30, "HUMAN", "=" * 30)
print(messages[1][1])
print("\nLargo total del prompt (caracteres):", sum(len(m[1]) for m in messages))

# Prueba de extract_code
respuesta_falsa = "Claro, aquí está:\n```python\ndf = spark.read.csv('x')\n```\nEspero que sirva."
print("\nextract_code →", repr(extract_code(respuesta_falsa)))