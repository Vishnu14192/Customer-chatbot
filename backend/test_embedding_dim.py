import os

from openai import OpenAI


client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

response = client.embeddings.create(
    model="text-embedding-3-small",
    input="hello world"
)

embedding = response.data[0].embedding

print("Dimension:", len(embedding))