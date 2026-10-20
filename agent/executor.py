import subprocess
import sys
from pathlib import Path

# Lo que va ANTES del código del LLM: tú lo controlas
HEADER = '''\
from pyspark.sql import SparkSession, functions as F, Window
spark = SparkSession.builder.appName("sas2spark").master("local[*]").getOrCreate()
spark.sparkContext.setLogLevel("ERROR")
INPUT_DIR = "{input_dir}"
OUTPUT_PATH = "{output_path}"
spark.conf.set("spark.sql.files.maxPartitionBytes", "1024")
spark.conf.set("spark.sql.adaptive.coalescePartitions.enabled", "false")
spark.conf.set("spark.sql.shuffle.partitions", "8")

# ===== CÓDIGO GENERADO =====
'''

# Lo que va DESPUÉS
FOOTER = '''

# ===== FIN =====
spark.stop()
'''


def run_pyspark(code, input_dir, output_path, script_path, timeout=180):
    """Corre código PySpark (texto) en un proceso aparte."""
    script_path = Path(script_path)
    output_path = Path(output_path)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Borra el output anterior: si no, el comparador podría
    # aprobar un CSV viejo aunque el código nuevo no genere nada.
    if output_path.exists():
        output_path.unlink()

    # 1) Armar el script completo
    script = (
        HEADER.format(
            input_dir=Path(input_dir).resolve().as_posix(),
            output_path=output_path.resolve().as_posix(),
        )
        + code
        + FOOTER
    )
    script_path.write_text(script, encoding="utf-8")

    # 2) Ejecutarlo en otro proceso, con timeout
    try:
        proc = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Timeout: el código tardó más de {timeout} segundos"}

    # 3) Revisar el resultado
    if proc.returncode != 0:
        ultimas = "\n".join(proc.stderr.strip().splitlines()[-30:])
        return {"ok": False, "error": ultimas}

    return {"ok": True, "error": ""}