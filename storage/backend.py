import os
import shutil
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

CACHE = Path(".cache/s3")     # aquí se descargan los casos en modo s3


def mode():
    return os.getenv("STORAGE", "local").lower()


def list_cases():
    """Rutas de todos los casos disponibles (local o S3)."""
    if mode() == "s3":
        from storage import s3
        names = sorted({k.split("/")[1] for k in s3.list_keys("cases/") if k.endswith("/case.json")})
        return [f"cases/{n}" for n in names]
    return sorted(str(c) for c in Path("cases").iterdir() if (c / "case.json").exists())


def prepare_case(case_arg):
    """Regresa la carpeta local del caso. En modo s3 primero la descarga."""
    if mode() != "s3":
        return str(case_arg)

    from storage import s3
    name = Path(case_arg).name
    local = CACHE / "cases" / name
    if local.exists():
        shutil.rmtree(local)          # siempre la versión más reciente de S3
    n = s3.download_prefix(f"cases/{name}", local)
    if n == 0:
        raise FileNotFoundError(f"No existe s3://{s3.bucket()}/cases/{name}/")
    print(f"☁️  Descargados {n} archivos de s3://{s3.bucket()}/cases/{name}/")
    return str(local)


def publish_results(case_name, run_id):
    """En modo s3 sube outputs/<caso>/ a runs/<run_id>/<caso>/."""
    if mode() != "s3":
        return None

    from storage import s3
    prefix = f"runs/{run_id}/{case_name}"
    n = s3.upload_dir(Path("outputs") / case_name, prefix)
    print(f"☁️  Subidos {n} archivos a s3://{s3.bucket()}/{prefix}/")
    return prefix