import pytest

from agent import graph

pytestmark = pytest.mark.spark

CASE = "cases/01_data_step_basic"

CODE_OK = '''
trx = (spark.read.option("header", True).option("inferSchema", True)
       .csv(f"{INPUT_DIR}/transactions.csv"))
df = trx.filter((F.rtrim(F.col("status")) != "CANCELLED") | F.col("status").isNull())
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

CODE_BUG = CODE_OK.replace(
    'F.col("amount") * F.col("fx_rate")',
    'F.round(F.col("amount") * F.col("fx_rate"), 0)',
)


def _fake(*codigos):
    """LLM falso: regresa los códigos en orden y guarda lo que recibió."""
    it = iter(codigos)
    llamadas = []

    def fake_llm(messages):
        llamadas.append(messages)
        return f"```python\n{next(it)}\n```"

    return fake_llm, llamadas


def test_loop_corrige_en_el_intento_2(monkeypatch):
    fake, llamadas = _fake(CODE_BUG, CODE_OK)
    monkeypatch.setattr(graph, "invoke_llm", fake)

    r = graph.run_case(CASE, max_attempts=3)

    assert r["passed"]
    assert r["attempts"] == 2
    assert len(llamadas) == 2                      # translate + 1 fix
    assert "amount_mxn" in llamadas[1][1][1]       # el fix recibió el reason del comparador


def test_se_rinde_al_llegar_al_maximo(monkeypatch):
    fake, _ = _fake(CODE_BUG, CODE_BUG, CODE_BUG)
    monkeypatch.setattr(graph, "invoke_llm", fake)

    r = graph.run_case(CASE, max_attempts=2)

    assert not r["passed"]
    assert r["attempts"] == 2