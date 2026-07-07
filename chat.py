import requests

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:1b"

print("Ollama Chat (type 'exit' to quit)")
print("-" * 40)

while True:
    user_input = input("\nYou: ")

    if user_input.lower() in ["exit", "quit"]:
        print("Goodbye!")
        break

    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": user_input,
            "stream": False
        }
    )

    if response.status_code == 200:
        result = response.json()
        print("\nOllama:", result["response"])
    else:
        print("Error:", response.status_code)
        print(response.text)