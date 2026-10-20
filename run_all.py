import argparse
import csv
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

from agent.graph import run_case

MODES = {
    "baseline":   {"use_rules": False, "max_attempts": 1},
    "rules":      {"use_rules": True,  "max_attempts": 1},
    "rules_loop": {"use_rules": True,  "max_attempts": 3},
}

def build_summary(rows, modes):
    df = pd.DataFrame(rows)
    valid = df[df["error"] == ""]           # solo corridas donde el agente sí trabajó

    def cell(case, mode):
        sub = valid[(valid["case"] == case) & (valid["mode"] == mode)]
        errs = len(df[(df["case"] == case) & (df["mode"] == mode) & (df["error"] != "")])
        if sub.empty:
            return f"— ({errs} err)" if errs else "—"
        txt = f"{int(sub['passed'].sum())}/{len(sub)} · {sub['attempts'].mean():.1f} int."
        return txt + (f" ({errs} err)" if errs else "")

    cases = sorted(df["case"].unique())
    lines = ["| Caso | " + " | ".join(modes) + " |",
             "|" + "---|" * (len(modes) + 1)]
    for c in cases:
        lines.append(f"| {c} | " + " | ".join(cell(c, m) for m in modes) + " |")

    tot = []
    for m in modes:
        sub = valid[valid["mode"] == m]
        tot.append(f"**{int(sub['passed'].sum())}/{len(sub)}**" if len(sub) else "—")
    lines.append("| **TOTAL** | " + " | ".join(tot) + " |")

    n_err = int((df["error"] != "").sum())
    if n_err:
        lines.append(f"\n_{n_err} corrida(s) excluidas por errores de infraestructura (LLM/red)._")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description="Evalúa el agente sobre todos los casos")
    p.add_argument("--runs", type=int, default=3, help="corridas por caso y modo")
    p.add_argument("--modes", nargs="+", default=list(MODES), choices=list(MODES))
    p.add_argument("--cases", nargs="+", default=None, help="rutas de casos (default: todos)")
    p.add_argument("--pause", type=float, default=5, help="segundos entre corridas")
    args = p.parse_args()

    cases = args.cases or sorted(
        str(c) for c in Path("cases").iterdir() if (c / "case.json").exists()
    )
    total = len(cases) * len(args.modes) * args.runs
    rows, k = [], 0

    for case in cases:
        for mode in args.modes:
            for run in range(1, args.runs + 1):
                k += 1
                print(f"\n{'#' * 60}\n[{k}/{total}] {Path(case).name} | {mode} | corrida {run}")
                t0 = time.time()
                try:
                    r = run_case(case, **MODES[mode])
                    error = ""
                except Exception as e:      # un fallo no detiene la evaluación
                    r = {"case": Path(case).name, "passed": False, "attempts": 0}
                    error = f"{type(e).__name__}: {e}"[:200]
                rows.append({**r, "mode": mode, "run": run,
                             "seconds": round(time.time() - t0, 1), "error": error})
                time.sleep(args.pause)

    # Guardar resultados
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    reports = Path("reports")
    reports.mkdir(exist_ok=True)

    raw = reports / f"eval_{ts}.csv"
    with open(raw, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["case", "mode", "run", "passed",
                                          "attempts", "seconds", "error"])
        w.writeheader()
        w.writerows(rows)

    summary = build_summary(rows, args.modes)
    (reports / f"eval_{ts}.md").write_text(summary, encoding="utf-8")

    print("\n" + "=" * 60 + "\nRESUMEN\n")
    print(summary)
    print(f"\nGuardado en {raw} y {raw.with_suffix('.md')}")


if __name__ == "__main__":
    main()