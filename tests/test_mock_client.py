import requests
import json

url = "http://localhost:8000/v1/chat/completions"
payload = {
    "model": "test",
    "messages": [
        {"role": "user", "content": "123|Alice|Hello world"}
    ]
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print("Response Body:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print(f"Error: {e}")
