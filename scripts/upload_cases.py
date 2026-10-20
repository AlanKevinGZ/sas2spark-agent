from storage import s3

n = s3.upload_dir("cases", "cases")
print(f"✅ Subidos {n} archivos a s3://{s3.bucket()}/cases/")