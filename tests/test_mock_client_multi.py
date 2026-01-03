import requests
import json

url = "http://localhost:8000/v1/chat/completions"
payload = {
    "model": "test-caching",
    "messages": [
        {"role": "system", "content": "Translate"},
        {"role": "user", "content": "0|System|Example"},
        {"role": "assistant", "content": "0|System|[0] Example"},
        {"role": "user", "content": "1|Alice|Hello\n2|Bob|Hi\n3|Charlie|Hey"},
        {"role": "assistant", "content": "1|Alice|[1] Hello\n2|Bob|[2] Hi\n3|Charlie|[3] Hey"},
        {"role": "user", "content": "4|Alice|Next line\n5|Bob|Another one"}
    ]
}

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Response Content (Last Message):")
        print(response.json()['choices'][0]['message']['content'])
    else:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
