from agent.prompts import build_translate_messages, extract_code, load_rules


def test_extract_code_con_bloque():
    texto = "Claro:\n```python\nx = 1\n```\nListo."
    assert extract_code(texto) == "x = 1"


def test_extract_code_sin_bloque():
    assert extract_code("x = 1") == "x = 1"


def test_load_rules_con_y_sin_reglas():
    con = load_rules(use_rules=True)
    sin = load_rules(use_rules=False)
    assert "R1." in con
    assert "R1." not in sin                      # baseline no ve las reglas SAS
    assert "Reglas del contrato" in sin          # pero sí el contrato


def test_translate_incluye_el_sas():
    msgs = build_translate_messages("data a; set b; run;", "info inputs", "out.csv")
    assert msgs[0][0] == "system"
    assert "data a; set b; run;" in msgs[1][1]
    assert "out.csv" in msgs[1][1]