import random
from typing import TypedDict

from langgraph.graph import END, StateGraph


# 1) STATE: el diccionario que viaja por todo el grafo
class State(TypedDict):
    attempt: int      # número de intento
    max_attempts: int
    success: bool
    log: list         # historial de lo que pasó


# 2) NODOS: funciones que reciben el state y regresan SOLO lo que cambian
def intentar(state: State):
    n = state["attempt"] + 1
    exito = random.random() < 0.3        # 30% de probabilidad de "pasar"
    print(f"Intento {n}: {'OK' if exito else 'falló'}")
    return {"attempt": n, "success": exito, "log": state["log"] + [f"intento {n}"]}


def reportar(state: State):
    estado = "PASÓ" if state["success"] else "FALLÓ"
    print(f"\nResultado: {estado} en {state['attempt']} intento(s)")
    print("Log:", state["log"])
    return {}


# 3) DECISIÓN: función que elige a qué nodo ir (no modifica el state)
def decidir(state: State):
    if state["success"]:
        return "reportar"
    if state["attempt"] >= state["max_attempts"]:
        return "reportar"
    return "intentar"


# 4) ARMAR EL GRAFO
graph = StateGraph(State)
graph.add_node("intentar", intentar)
graph.add_node("reportar", reportar)

graph.set_entry_point("intentar")                  # por dónde empieza
graph.add_conditional_edges("intentar", decidir)   # después de intentar, decide
graph.add_edge("reportar", END)                    # reportar termina

app = graph.compile()


# 5) EJECUTAR con el state inicial
app.invoke({"attempt": 0, "max_attempts": 3, "success": False, "log": []})