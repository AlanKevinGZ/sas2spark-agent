from pathlib import Path
from typing import TypedDict

from langgraph.graph import StateGraph, END

from agent.executor import run_pyspark
from comparator.compare import compare_csv, load_case_config


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


# ---------- CÓDIGO FALSO (en la Fase 4 lo reemplaza el LLM) ----------
CODE_OK = '''
trx = (spark.read.option("header", True).option("inferSchema", True)
       .csv(f"{INPUT_DIR}/transactions.csv"))
df = trx.filter((F.trim(F.col("status")) != "CANCELLED") | F.col("status").isNull())
df = df.withColumn("amount_mxn", F.col("amount") * F.col("fx_rate"))
df = df.withColumn("segment",
        F.when(F.col("amount_mxn") >= 10000, "HIGH")
         .when(F.col("amount_mxn") >= 1000, "MEDIUM")
         .otherwise("LOW"))
df = df.withColumn("trx_month", F.trunc("trx_date", "month"))
df = df.withColumn("flag_atm",
        F.when((F.col("channel") == "ATM") & (F.col("amount_mxn") > 8000), 1).otherwise(0))
df = df.select("trx_id", "customer_id", "trx_date", "trx_month", "amount_mxn",
               "segment", "channel", "status", "flag_atm")
df.toPandas().to_csv(OUTPUT_PATH, index=False)
'''

# Bug a propósito: redondear sin decimales
CODE_BUG = CODE_OK.replace(
    'F.col("amount") * F.col("fx_rate")',
    'F.round(F.col("amount") * F.col("fx_rate"), 0)',
)


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
    print(f"📂 Cargando caso: {case.name}")
    return {
        "config": load_case_config(case),
        "sas_code": (case / "program.sas").read_text(encoding="utf-8"),
    }


def translate(state: State):
    print("🔤 Traduciendo (FALSO: código con bug)")
    return {"pyspark_code": CODE_BUG}


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
    print("🛠️  Corrigiendo (FALSO: regresa código correcto)")
    return {"pyspark_code": CODE_OK}


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


if __name__ == "__main__":
    app = build_graph()
    app.invoke({
        "case_dir": "cases/01_data_step_basic",
        "attempt": 0,
        "max_attempts": 3,
        "history": [],
    })