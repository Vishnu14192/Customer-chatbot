from app.services.chat_service import (
    ChatService
)


chat_service = ChatService()
user_id = "test-user"

while True:

    question = input(
        "\nAsk Question: "
    )

    if question.lower() == "exit":
        break

    result = (
        chat_service.chat(
            user_id=user_id,
            question=question
        )
    )
    
    print("\nANSWER\n")
    print(result["answer"])

    print("\nSOURCES\n")
    print(result["sources"])