from pathlib import Path

from agent.executor import run_pyspark
from agent.llm import get_llm
from agent.prompts import build_translate_messages, describe_inputs, extract_code
from comparator.compare import compare_csv, load_case_config

CASE = Path("cases/01_data_step_basic")
config = load_case_config(CASE)
OUT = Path("outputs") / CASE.name

sas_code = (CASE / "program.sas").read_text(encoding="utf-8")
inputs_info = describe_inputs(CASE / "input", config["input_files"])
messages = build_translate_messages(sas_code, inputs_info, config["output_file"])

print("🤖 Llamando al LLM...")
respuesta = get_llm().invoke(messages)
codigo = extract_code(respuesta.content)

print("\n========== CÓDIGO GENERADO ==========")
print(codigo)

print("\n▶️ Ejecutando...")
r = run_pyspark(codigo, CASE / "input", OUT / config["output_file"], OUT / "llm_test.py")
print("Ejecución:", r["ok"], r["error"][-500:] if r["error"] else "")

if r["ok"]:
    c = compare_csv(CASE / "expected" / config["output_file"], OUT / config["output_file"], config)
    print("Comparación:", c)