import pandas as pd

from comparator.compare import compare_csv

BASE = {"id": ["A", "B", "C"], "x": [1.0, 2.0, None], "s": ["a", None, "c"]}


def _csv(tmp_path, name, data):
    p = tmp_path / name
    pd.DataFrame(data).to_csv(p, index=False)
    return p


def test_identico(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    assert compare_csv(e, e)["ok"]


def test_filas_desordenadas_con_keys(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {"id": ["C", "A", "B"], "x": [None, 1.0, 2.0], "s": ["c", "a", None]})
    assert compare_csv(e, g, {"keys": ["id"]})["ok"]


def test_filas_desordenadas_sin_keys(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {"id": ["B", "C", "A"], "x": [2.0, None, 1.0], "s": [None, "c", "a"]})
    assert compare_csv(e, g)["ok"]


def test_columnas_en_otro_orden(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {"s": BASE["s"], "x": BASE["x"], "id": BASE["id"]})
    assert compare_csv(e, g)["ok"]


def test_check_order_detecta_orden(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {"id": ["C", "A", "B"], "x": [None, 1.0, 2.0], "s": ["c", "a", None]})
    r = compare_csv(e, g, {"keys": ["id"], "check_order": True})
    assert not r["ok"]
    assert "ORDEN" in r["reason"]


def test_tolerancia_decimales(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {**BASE, "x": [1.0000000001, 2.0, None]})
    assert compare_csv(e, g, {"keys": ["id"]})["ok"]


def test_valor_distinto(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {**BASE, "x": [1.0, 2.5, None]})
    r = compare_csv(e, g, {"keys": ["id"]})
    assert not r["ok"]
    assert "'x'" in r["reason"]


def test_null_vs_valor(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {**BASE, "x": [1.0, 2.0, 3.0]})
    assert not compare_csv(e, g, {"keys": ["id"]})["ok"]


def test_columna_faltante(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {"id": BASE["id"], "x": BASE["x"]})
    r = compare_csv(e, g)
    assert not r["ok"]
    assert "Faltan: ['s']" in r["reason"]


def test_filas_faltantes(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    g = _csv(tmp_path, "g.csv", {k: v[:2] for k, v in BASE.items()})
    r = compare_csv(e, g)
    assert not r["ok"]
    assert "faltan 1" in r["reason"]


def test_sin_archivo(tmp_path):
    e = _csv(tmp_path, "e.csv", BASE)
    r = compare_csv(e, tmp_path / "no_existe.csv")
    assert not r["ok"]
    assert "No se generó" in r["reason"]