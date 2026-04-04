import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

load_dotenv()

client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "rag_docs"

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def retrieve_chunks(question: str, k: int = 3):
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = chroma_client.get_collection(COLLECTION_NAME)

    question_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=k
    )
    return results["documents"][0]


def answer_question(question: str) -> str:
    chunks = retrieve_chunks(question, k=3)
    context = "\n\n".join(chunks)

    prompt = f"""
        You are a helpful document Q&A assistant.

        Answer using only the context below.
        If the answer is not in the context, say:
        "I could not find that in the document."

        Keep the answer short.

        Context:
        {context}

        Question:
        {question}
        """

    response = client.responses.create(
        model="gpt-4.1-nano",
        input=prompt,
        max_output_tokens=120
    )

    return response.output_text

def main():
    while True:
        question=input("\nAsk a question (type 'exit' to quit)\n")

        if question.lower() == "exit":
            break

        answer = answer_question(question)
        print("\nAnswer:")
        print(answer)


if __name__ == "__main__":
    main()