from app.rag.retriever import Retriever


retriever = Retriever()

query = input("Ask Question: ")

results = retriever.search(query)

print("\nRESULTS\n")

for i, doc in enumerate(
    results["documents"][0]
):
    print(f"\nChunk {i+1}")
    print("-" * 50)
    print(doc)

    print(
        "Source:",
        results["metadatas"][0][i]["source"]
    )
    print(
        "Distance:",
        results["distances"][0][i]
    )

if results.get("reranked_chunks"):
    print("\nRERANK SCORES\n")
    for idx, item in enumerate(results["reranked_chunks"], start=1):
        print(
            f"{idx}. score={item.get('rerank_score')} "
            f"cross_encoder={item.get('cross_encoder_score')} "
            f"source={item.get('metadata', {}).get('source')}"
        )

print(results)
