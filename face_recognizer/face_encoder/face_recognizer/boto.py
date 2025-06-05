import boto3
from botocore.client import Config
import os

local_folder = os.path.abspath("tests/data")
print(f"Абсолютный путь: {local_folder}")

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

bucket_name = 'talismandocumentbucket'
s3_folder = 'uploads/AgeDB'

if not os.path.exists(local_folder):
    raise FileNotFoundError(f"Папка {local_folder} не найдена")

for root, dirs, files in os.walk(local_folder):
    for file in files:
        local_path = os.path.join(root, file)

        relative_path = os.path.relpath(local_path, local_folder)
        s3_key = os.path.join(s3_folder, relative_path).replace("\\", "/")

        content_type = 'image/jpeg' if file.lower().endswith(('.jpg', '.jpeg')) else 'application/octet-stream'

        # Загрузка файла
        s3.upload_file(
            Filename=local_path,
            Bucket=bucket_name,
            Key=s3_key,
            ExtraArgs={'ContentType': content_type}
        )
        print(f"Загружен: {local_path} → s3://{bucket_name}/{s3_key}")
