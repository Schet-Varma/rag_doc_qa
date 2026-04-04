import os
from dotenv import load_dotenv
from openai import OpenAI
import chromadb

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "rag_docs"


def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def get_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return chroma_client.get_collection(name=COLLECTION_NAME)


def retrieve_chunks(question, k=4):
    collection = get_collection()
    question_embedding = get_embedding(question)

    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=k
    )

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]

    chunks = []
    for i in range(len(documents)):
        chunks.append({
            "text": documents[i],
            "metadata": metadatas[i]
        })

    return chunks


def build_context(retrieved_chunks):
    context_parts = []

    for i, chunk in enumerate(retrieved_chunks, start=1):
        source_name = chunk["metadata"].get("source_name", "unknown source")
        chunk_text = chunk["text"]
        context_parts.append(f"[Source {i}] ({source_name})\n{chunk_text}")

    return "\n\n".join(context_parts)


def build_history(chat_history):
    if not chat_history:
        return ""

    parts = []
    for turn in chat_history[-6:]:
        parts.append(f"User: {turn['question']}")
        parts.append(f"Assistant: {turn['answer']}")

    return "\n".join(parts)


def answer_question(question, chat_history=None, k=4):
    retrieved_chunks = retrieve_chunks(question, k)
    context = build_context(retrieved_chunks)
    history_text = build_history(chat_history)

    prompt = f"""
        You are a helpful document Q&A assistant.

        Answer the question using ONLY the context below.
        If the answer is not present in the context, say:
        "I could not find that in the uploaded content."

        Keep the answer clear and short.

        Previous conversation:
        {history_text}

        Context:
        {context}

        Question:
        {question}
        """

    response = client.responses.create(
        model="gpt-4.1-nano",
        input=prompt,
        max_output_tokens=180
    )

    return {
        "answer": response.output_text,
        "sources": retrieved_chunks
    }