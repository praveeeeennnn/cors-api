import requests

url = "http://localhost:11434/api/generate"

data = {
    "model": "llama3.2:1b",
    "prompt": "Explain machine learning in simple words",
    "stream": False
}

response = requests.post(url, json=data)

if response.status_code == 200:
    result = response.json()
    print(result["response"])
else:
    print("Error:", response.status_code)
    print(response.text)