import os

from app.services.chat_service import (
    ChatService
)


chat_service = ChatService()
user_id = "test-user"

model_name = os.getenv(
    "OLLAMA_MODEL",
    "Qwen3:1.7b"
)

print(f"Using local Ollama model: {model_name}")
print("Type 'exit' to quit.")

while True:

    try:
        question = input(
            "\nAsk Question: "
        )
    except KeyboardInterrupt:
        print("\nStopped.")
        break

    if question.lower() == "exit":
        break

    try:
        result = (
            chat_service.chat(
                user_id=user_id,
                question=question
            )
        )
    except Exception as exc:
        print("\nERROR\n")
        print(str(exc))
        print("\nLocal LLM checklist:")
        print("1. Ensure Ollama app/service is running")
        print(f"2. Pull the model if needed: ollama pull {model_name}")
        print("3. Optionally set OLLAMA_BASE_URL if Ollama is remote")
        continue
    
    print("\nANSWER\n")
    print(result["answer"])

    print("\nSOURCES\n")
    print(result["sources"])