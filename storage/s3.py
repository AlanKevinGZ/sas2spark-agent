import os
from pathlib import Path

import boto3
from dotenv import load_dotenv

load_dotenv()


def bucket():
    return os.environ["S3_BUCKET"]


def _client():
    return boto3.client("s3")


def upload_file(local_path, key):
    _client().upload_file(str(local_path), bucket(), key)


def upload_dir(local_dir, prefix):
    """Sube todos los archivos de una carpeta (recursivo). Regresa cuántos subió."""
    s3, b = _client(), bucket()
    local_dir = Path(local_dir)
    n = 0
    for f in local_dir.rglob("*"):
        if f.is_file():
            key = f"{prefix.rstrip('/')}/{f.relative_to(local_dir).as_posix()}"
            s3.upload_file(str(f), b, key)
            n += 1
    return n


def list_keys(prefix):
    """Lista todas las llaves bajo un prefijo (maneja paginación)."""
    s3 = _client()
    keys = []
    for page in s3.get_paginator("list_objects_v2").paginate(Bucket=bucket(), Prefix=prefix):
        keys += [o["Key"] for o in page.get("Contents", [])]
    return keys


def download_prefix(prefix, local_dir):
    """Descarga todo lo que está bajo un prefijo a una carpeta local."""
    s3, b = _client(), bucket()
    prefix = prefix.rstrip("/") + "/"
    local_dir = Path(local_dir)
    n = 0
    for key in list_keys(prefix):
        if key.endswith("/"):
            continue
        dest = local_dir / key[len(prefix):]
        dest.parent.mkdir(parents=True, exist_ok=True)
        s3.download_file(b, key, str(dest))
        n += 1
    return n