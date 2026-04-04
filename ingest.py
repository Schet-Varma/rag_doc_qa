import os
from io import BytesIO

from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
import chromadb
from pypdf import PdfReader
from docx import Document

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHROMA_PATH = "chroma_db"
COLLECTION_NAME = "rag_docs"

TEXT_FILE_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx",
    ".json", ".csv", ".html", ".css", ".sql", ".java",
    ".c", ".cpp", ".xml", ".yaml", ".yml"
}

def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def get_collection(reset_db=True):
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

    if reset_db:
        try:
            chroma_client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        return chroma_client.create_collection(name=COLLECTION_NAME)

    try:
        return chroma_client.get_collection(name=COLLECTION_NAME)
    except Exception:
        return chroma_client.create_collection(name=COLLECTION_NAME)

def extract_text_from_pdf(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    pages = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages.append(page_text)

    return "\n".join(pages)


def extract_text_from_docx(file_bytes):
    doc = Document(BytesIO(file_bytes))
    paragraphs = []

    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            paragraphs.append(paragraph.text)

    return "\n".join(paragraphs)


def extract_text_from_plain_file(file_bytes):
    return file_bytes.decode("utf-8", errors="ignore")

def extract_text(uploaded_file):
    filename = uploaded_file.name
    extension = os.path.splitext(filename)[1].lower()
    file_bytes = uploaded_file.read()

    if extension == ".pdf":
        text = extract_text_from_pdf(file_bytes)
    elif extension == ".docx":
        text = extract_text_from_docx(file_bytes)
    elif extension in TEXT_FILE_EXTENSIONS:
        text = extract_text_from_plain_file(file_bytes)
    else:
        text = extract_text_from_plain_file(file_bytes)

    return filename, text.strip()


def split_text_into_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    return splitter.split_text(text)

def store_chunks(collection, chunks, source_name, source_type):
    stored_count = 0
    safe_source_name = source_name.replace(" ", "_")

    for i, chunk in enumerate(chunks):
        embedding = get_embedding(chunk)

        collection.add(
            ids=[f"{safe_source_name}_{i}"],
            documents=[chunk],
            metadatas=[{
                "source_name": source_name,
                "source_type": source_type,
                "chunk_id": i
            }],
            embeddings=[embedding]
        )

        stored_count += 1

    return stored_count


def ingest_sources(uploaded_files=None, pasted_text=None, reset_db=True):
    collection = get_collection(reset_db=reset_db)
    total_chunks = 0

    if pasted_text and pasted_text.strip():
        chunks = split_text_into_chunks(pasted_text.strip())
        total_chunks += store_chunks(
            collection=collection,
            chunks=chunks,
            source_name="Pasted Text",
            source_type="pasted_text"
        )

    if uploaded_files:
        for uploaded_file in uploaded_files:
            filename, text = extract_text(uploaded_file)

            if not text:
                continue

            chunks = split_text_into_chunks(text)
            total_chunks += store_chunks(
                collection=collection,
                chunks=chunks,
                source_name=filename,
                source_type="uploaded_file"
            )

    return total_chunks

