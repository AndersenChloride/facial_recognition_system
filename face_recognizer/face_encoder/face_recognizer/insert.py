import boto3
import re
import requests
import boto3
from botocore.client import Config

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

bucket_name = 'talismandocumentbucket'
prefix = 'uploads/AgeDB/' 

url = "http://localhost:4446/insert_embeddings_to_db"
headers = {"Content-Type": "application/json"}


response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, )

paginator = s3.get_paginator("list_objects_v2")
page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

found = False
for page in page_iterator:
    for obj in page.get("Contents", []):
        found = True
        key = obj['Key']
        if key.endswith(".jpg"):
            match = re.match(r".*/(\d+)_.*\.jpg$", key)
            if match:
                uuid = match.group(1)
                s3_path = f"s3://{bucket_name}/{key}"

                payload = {
                    
                    "s3_path": s3_path,
                    "uuid": uuid
                }

                try:
                    response = requests.post(url, headers=headers, json=payload)
                    if response.status_code == 200:
                        print(f"[OK] {uuid} -> {key}")
                    else:
                        print(f"[ERROR] {uuid}: {response.status_code} — {response.text}")
                except Exception as e:
                    print(f"[EXCEPTION] {uuid}: {str(e)}")

if not found:
    print("Нет файлов в указанной папке.")

