import os
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
import chromadb

load_dotenv()

client = OpenAI(api_key=os.getenv("OPEN_API_KEY"))

CHROMA_PATH = "chroma_db"
DATA_PATH =  "data/sample.txt"
COLLECTION_NAME = "rag_docs"

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def main():
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        text = f.read()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size = 400,
            chunk_overlap = 80
        )
        chunks = splitter.split_text(text)

        chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

        try:
            chroma_client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass

        collection = chroma_client.create_collection(name=COLLECTION_NAME)

        for i, chunk in enumerate(chunks):
            embedding = get_embedding(chunk)
            collection.add(
                ids=[f"chunk_{i}"],
                documents=[chunk],
                embeddings=[embedding]
            )
        
        print(f"Stored {len(chunks)} chunks in Chroma.")

if __name__ == "__main__":
    main()

