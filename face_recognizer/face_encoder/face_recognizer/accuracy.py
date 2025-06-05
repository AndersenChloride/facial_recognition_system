import boto3
import re
import requests
from botocore.client import Config

s3 = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)
bucket = "talismandocumentbucket"
prefix = "uploads/AgeDB/archive/AgeDB/"
threshold = 25

def extract_id_from_filename(filename: str) -> str:
    match = re.match(r"(\d+)_", filename)
    return match.group(1) if match else None

def count_errors(arr, o=threshold):
    if not arr:
        return 0
    reference = arr[0]
    return sum(1 for x in arr[1:] if abs(x - reference) > o)

paginator = s3.get_paginator("list_objects_v2")
page_iterator = paginator.paginate(Bucket=bucket, Prefix=prefix)

total = 0
total_errors = 0

for page in page_iterator:
    for obj in page.get("Contents", []):
        key = obj["Key"]
        if not key.lower().endswith(".jpg"):
            continue

        uuid = extract_id_from_filename(key.split("/")[-1])
        if not uuid:
            continue

        s3_path = f"s3://{bucket}/{key}"

        response = requests.post("http://localhost:4446/find_similar_images", json={
            "config": {
                "topn": 6,
                "threshold": 100000
            },
            "s3_path": s3_path,
            "uuid": uuid
        })

        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and data and isinstance(data[0], list):
                    ids = [int(x) for x in data[0]]
                    errors = count_errors(ids)
                    total_errors += errors
                    total += 1
                    print(f"{key} — errors: {errors}")
            except Exception as e:
                print(f"Ошибка при обработке {key}: {str(e)}")

print(f"\nОбработано {total} изображений")
print(f"Всего ошибок: {total_errors}")
print(f"Точность: {((total * 5 - total_errors) / (total * 5)) * 100:.2f}%")
