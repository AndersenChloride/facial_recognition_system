import requests

data = {
    "config": {
        "topn": 6,
        "threshold": 100000
    },
    "s3_path": "s3://talismandocumentbucket/uploads/AgeDB/archive/AgeDB/225_ElvisPresley_39_m.jpg",
    "uuid": "2"
}
url = "http://localhost:4446/find_similar_images"
headers = {"Content-Type": "application/json"}

try:
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 200:
        result = response.json()
        print("Совпадения:")
        print(response.text)

    
    elif response.status_code == 404:
        print("Файл не найден в S3")

    else:
        print(f"Ошибка {response.status_code}: {response.text}")

except requests.exceptions.RequestException as e:
    print("Ошибка соединения:", str(e))