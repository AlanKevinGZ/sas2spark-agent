import random
from typing import TypedDict

from langgraph.graph import END, StateGraph


class State(TypedDict):
    attempt: int
    max_attempts: int
    success: bool
    log: list
    sas_code: str
    pyspark_code: str


# ---------- NODOS ----------
def translate(state: State):
    print("Traduciendo código SAS...")
    return {"pyspark_code": "código v1"}


def execute(state: State):
    n = state["attempt"] + 1
    exito = random.random() < 0.3
    print(f"Ejecutando {state['pyspark_code']} (intento {n}): {'OK' if exito else 'falló'}")
    return {
        "attempt": n,
        "success": exito,
        "log": state["log"] + [f"intento {n}"],
    }


def fix(state: State):
    codigo = f"código v{state['attempt'] + 1}"  
    print(f"Corrigiendo → {codigo}")
    return {"pyspark_code": codigo}


def report(state: State):
    print(f"\nResultado: {'PASÓ' if state['success'] else 'FALLÓ'}")
    print(f"Código final: {state['pyspark_code']}")
    print("Log:", state["log"])
    return {}


# ---------- DECISIÓN ----------                 # ← nueva
def decidir(state: State):
    if state["success"]:
        return "report"
    if state["attempt"] >= state["max_attempts"]:
        return "report"
    return "fix"


# ---------- GRAFO ----------
graph = StateGraph(State)

graph.add_node("translate", translate)          # ← nombres = función
graph.add_node("execute", execute)
graph.add_node("fix", fix)                      # ← faltaba
graph.add_node("report", report)                # ← faltaba

graph.set_entry_point("translate")
graph.add_edge("translate", "execute")          # siempre
graph.add_conditional_edges("execute", decidir) # ← decide: fix o report
graph.add_edge("fix", "execute")                # el loop
graph.add_edge("report", END)

app = graph.compile()


# ---------- EJECUTAR ----------
app.invoke({
    "attempt": 0,
    "max_attempts": 3,
    "success": False,
    "log": [],
    "sas_code": "data a; set b; where x > 5; run;",   # ← faltaba
    "pyspark_code": "",                               # ← faltaba
})