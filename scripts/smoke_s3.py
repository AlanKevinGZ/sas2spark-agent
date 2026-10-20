import os

import boto3
from dotenv import load_dotenv

load_dotenv()
bucket = os.environ["S3_BUCKET"]
s3 = boto3.client("s3")     # lee las keys y la región del .env automáticamente

s3.put_object(Bucket=bucket, Key="smoke/hola.txt", Body=b"hola desde sas2spark-agent")
print("✅ Subido")

resp = s3.list_objects_v2(Bucket=bucket, Prefix="smoke/")
print("Archivos:", [o["Key"] for o in resp.get("Contents", [])])

body = s3.get_object(Bucket=bucket, Key="smoke/hola.txt")["Body"].read()
print("Contenido:", body.decode())