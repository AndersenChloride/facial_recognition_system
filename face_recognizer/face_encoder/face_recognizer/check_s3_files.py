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

response = s3.list_objects_v2(Bucket=bucket_name)

if 'Contents' in response:
    print("Файлы в бакете:")
    for obj in response['Contents']:
        print(obj['Key'])
else:
    print("Бакет пуст")