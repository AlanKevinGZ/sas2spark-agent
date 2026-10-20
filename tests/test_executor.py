import pytest

from agent.executor import run_pyspark

pytestmark = pytest.mark.spark


def _input(tmp_path):
    inp = tmp_path / "input"
    inp.mkdir()
    (inp / "d.csv").write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    return inp


def test_codigo_bueno_genera_csv(tmp_path):
    code = (
        'df = spark.read.option("header", True).csv(f"{INPUT_DIR}/d.csv")\n'
        "df.toPandas().to_csv(OUTPUT_PATH, index=False)\n"
    )
    out = tmp_path / "out" / "r.csv"
    r = run_pyspark(code, _input(tmp_path), out, tmp_path / "s.py")
    assert r["ok"], r["error"]
    assert out.exists()


def test_codigo_roto_captura_error(tmp_path):
    code = 'spark.read.option("header", True).csv(f"{INPUT_DIR}/d.csv").select("no_existe").show()\n'
    r = run_pyspark(code, _input(tmp_path), tmp_path / "r.csv", tmp_path / "s.py")
    assert not r["ok"]
    assert "no_existe" in r["error"]


def test_borra_output_viejo(tmp_path):
    out = tmp_path / "r.csv"
    out.write_text("viejo", encoding="utf-8")
    r = run_pyspark("x = 1\n", _input(tmp_path), out, tmp_path / "s.py")   # no escribe nada
    assert r["ok"]
    assert not out.exists()      # el CSV viejo no debe sobrevivir