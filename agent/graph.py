from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, END

from agent.executor import run_pyspark
from comparator.compare import compare_csv, load_case_config

from agent.llm import invoke_llm


from agent.prompts import (
    build_translate_messages, build_fix_messages, describe_inputs, extract_code,
)


# ---------- STATE ----------
class State(TypedDict):
    case_dir: str
    config: dict
    sas_code: str
    pyspark_code: str
    exec_result: dict
    compare_result: dict
    attempt: int
    max_attempts: int
    history: list
    inputs_info: str
    problems_log: list
    use_rules: bool

# ---------- helpers de rutas ----------
def _paths(state):
    case = Path(state["case_dir"])
    out_dir = Path("outputs") / case.name
    out_file = state["config"]["output_file"]
    return {
        "input_dir": case / "input",
        "expected": case / "expected" / out_file,
        "generated": out_dir / out_file,
        "script": out_dir / f"generated_v{state['attempt'] + 1}.py",
    }


# ---------- NODOS ----------
def load_case(state: State):
    case = Path(state["case_dir"])
    config = load_case_config(case)
    print(f"📂 Cargando caso: {case.name}")
    return {
        "config": config,
        "sas_code": (case / "program.sas").read_text(encoding="utf-8"),
        "inputs_info": describe_inputs(case / "input", config["input_files"]),
    }


def translate(state: State):
    print("🤖 Traduciendo con LLM...")
    messages = build_translate_messages(
        state["sas_code"], state["inputs_info"], state["config"]["output_file"],
        use_rules=state.get("use_rules", True),
    )
    texto = invoke_llm(messages)
    return {"pyspark_code": extract_code(texto)}

def execute(state: State):
    p = _paths(state)
    n = state["attempt"] + 1
    print(f"▶️  Ejecutando intento {n}...")
    r = run_pyspark(state["pyspark_code"], p["input_dir"], p["generated"], p["script"])
    print(f"   ejecución ok={r['ok']}")
    return {
        "exec_result": r,
        "attempt": n,
        "history": state["history"] + [f"intento {n}: ejecución ok={r['ok']}"],
    }


def compare(state: State):
    p = _paths(state)
    r = compare_csv(p["expected"], p["generated"], state["config"])
    print(f"🔍 Comparación ok={r['ok']} → {r['reason']}")
    return {
        "compare_result": r,
        "history": state["history"] + [f"intento {state['attempt']}: comparación ok={r['ok']}"],
    }

def fix(state: State):
    # ¿Qué falló: la ejecución o la comparación?
    if not state["exec_result"]["ok"]:
        problem = f"El código falló al ejecutarse. Error:\n{state['exec_result']['error']}"
    else:
        problem = (
            "El código corrió, pero el resultado NO coincide con el esperado:\n"
            f"{state['compare_result']['reason']}"
        )

    # Problemas de intentos ANTERIORES (el actual va aparte, en "Problema detectado")
    anteriores = state.get("problems_log", [])
    previous_problems = (
        "\n".join(f"- Intento {i + 1}: {p}" for i, p in enumerate(anteriores))
        if anteriores else "Ninguno"
    )

    print("🛠️  Corrigiendo con LLM...")
    messages = build_fix_messages(
        state["sas_code"], state["inputs_info"], state["pyspark_code"],
        problem, previous_problems,
        use_rules=state.get("use_rules", True),
    )
    texto = invoke_llm(messages)
    return {
        "pyspark_code": extract_code(texto),
        "problems_log": anteriores + [problem],
    }

def report(state: State):
    ok = state.get("compare_result", {}).get("ok", False)
    print("\n" + "=" * 50)
    print(f"Caso: {state['config']['name']}")
    print(f"Resultado: {'✅ PASÓ' if ok else '❌ FALLÓ'} en {state['attempt']} intento(s)")
    for h in state["history"]:
        print("  -", h)
    return {}


# ---------- DECISIONES ----------
def after_execute(state: State):
    if state["exec_result"]["ok"]:
        return "compare"
    if state["attempt"] >= state["max_attempts"]:
        return "report"
    return "fix"


def after_compare(state: State):
    if state["compare_result"]["ok"]:
        return "report"
    if state["attempt"] >= state["max_attempts"]:
        return "report"
    return "fix"


# ---------- GRAFO ----------
def build_graph():
    g = StateGraph(State)
    g.add_node("load_case", load_case)
    g.add_node("translate", translate)
    g.add_node("execute", execute)
    g.add_node("compare", compare)
    g.add_node("fix", fix)
    g.add_node("report", report)

    g.set_entry_point("load_case")
    g.add_edge("load_case", "translate")
    g.add_edge("translate", "execute")
    g.add_conditional_edges("execute", after_execute)
    g.add_conditional_edges("compare", after_compare)
    g.add_edge("fix", "execute")
    g.add_edge("report", END)
    return g.compile()

def run_case(case_dir, max_attempts=3, use_rules=True):
    """Corre un caso y regresa un resumen del resultado."""
    app = build_graph()
    final = app.invoke({
        "case_dir": case_dir,
        "attempt": 0,
        "max_attempts": max_attempts,
        "history": [],
        "problems_log": [],
        "use_rules": use_rules,
    })
    return {
        "case": Path(case_dir).name,
        "passed": final.get("compare_result", {}).get("ok", False),
        "attempts": final["attempt"],
    }


if __name__ == "__main__":
    import sys

    case_dir = sys.argv[1] if len(sys.argv) > 1 else "cases/01_data_step_basic"
    print(run_case(case_dir))