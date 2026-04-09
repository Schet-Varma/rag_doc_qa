import json
import os
import uuid
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
DOCS_REGISTRY_PATH = "documents_registry.json"


def get_embedding(text: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def get_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        return chroma_client.get_collection(name=COLLECTION_NAME)
    except Exception:
        return chroma_client.create_collection(name=COLLECTION_NAME)


def split_text_into_chunks(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    return splitter.split_text(text)


def load_registry():
    if not os.path.exists(DOCS_REGISTRY_PATH):
        return []

    with open(DOCS_REGISTRY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_registry(registry):
    with open(DOCS_REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)


def add_doc_to_registry(doc_id, name, source_type):
    registry = load_registry()
    registry.append({
        "doc_id": doc_id,
        "name": name,
        "source_type": source_type
    })
    save_registry(registry)


def delete_doc_from_registry(doc_id):
    registry = load_registry()
    registry = [doc for doc in registry if doc["doc_id"] != doc_id]
    save_registry(registry)


def list_docs():
    return load_registry()


def extract_text_from_pdf(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    extracted = []

    for page_index, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if not page_text or not page_text.strip():
            continue

        page_chunks = split_text_into_chunks(page_text)

        for chunk in page_chunks:
            extracted.append({
                "text": chunk,
                "page_number": page_index + 1,
                "line_start": None,
                "line_end": None,
                "paragraph_start": None,
                "paragraph_end": None
            })

    return extracted


def extract_text_from_docx(file_bytes):
    doc = Document(BytesIO(file_bytes))
    extracted = []

    paragraphs = []
    for i, paragraph in enumerate(doc.paragraphs):
        text = paragraph.text.strip()
        if text:
            paragraphs.append((i + 1, text))

    for para_num, text in paragraphs:
        para_chunks = split_text_into_chunks(text)

        for chunk in para_chunks:
            extracted.append({
                "text": chunk,
                "page_number": None,
                "line_start": None,
                "line_end": None,
                "paragraph_start": para_num,
                "paragraph_end": para_num
            })

    return extracted


def extract_text_from_plain_file(file_bytes):
    text = file_bytes.decode("utf-8", errors="ignore")
    if not text:
        return []

    lines = text.splitlines()
    extracted = []

    current_lines = []
    current_start = None

    for i, line in enumerate(lines, start=1):
        if current_start is None:
            current_start = i

        current_lines.append(line)
        candidate_text = "\n".join(current_lines)

        if len(candidate_text) >= 500:
            extracted.append({
                "text": candidate_text,
                "page_number": None,
                "line_start": current_start,
                "line_end": i,
                "paragraph_start": None,
                "paragraph_end": None
            })

            overlap_lines = current_lines[-3:] if len(current_lines) >= 3 else current_lines[:]
            current_lines = overlap_lines
            current_start = i - len(overlap_lines) + 1

    if current_lines:
        extracted.append({
            "text": "\n".join(current_lines),
            "page_number": None,
            "line_start": current_start,
            "line_end": current_start + len(current_lines) - 1,
            "paragraph_start": None,
            "paragraph_end": None
        })

    return extracted


def extract_text(uploaded_file):
    filename = uploaded_file["filename"]
    extension = os.path.splitext(filename)[1].lower()
    file_bytes = uploaded_file["file_bytes"]

    if extension == ".pdf":
        chunks = extract_text_from_pdf(file_bytes)
    elif extension == ".docx":
        chunks = extract_text_from_docx(file_bytes)
    else:
        chunks = extract_text_from_plain_file(file_bytes)

    return filename, chunks


def store_chunks(collection, chunks, source_name, source_type, doc_id):
    stored_count = 0
    safe_source_name = source_name.replace(" ", "_")

    for i, chunk_data in enumerate(chunks):
        chunk_text = chunk_data["text"].strip()
        if not chunk_text:
            continue

        embedding = get_embedding(chunk_text)

        metadata = {
            "doc_id": doc_id,
            "source_name": source_name,
            "source_type": source_type,
            "chunk_id": i,
            "page_number": chunk_data["page_number"],
            "line_start": chunk_data["line_start"],
            "line_end": chunk_data["line_end"],
            "paragraph_start": chunk_data["paragraph_start"],
            "paragraph_end": chunk_data["paragraph_end"]
        }

        metadata = {k: v for k, v in metadata.items() if v is not None}

        collection.add(
            ids=[f"{doc_id}_{safe_source_name}_{i}"],
            documents=[chunk_text],
            metadatas=[metadata],
            embeddings=[embedding]
        )

        stored_count += 1

    return stored_count


def ingest_sources(uploaded_files=None, pasted_text=None, pasted_text_name="My Notes"):
    collection = get_collection()
    total_chunks = 0
    added_docs = []

    if pasted_text and pasted_text.strip():
        doc_id = str(uuid.uuid4())
        pasted_chunks = extract_text_from_plain_file(
            pasted_text.strip().encode("utf-8")
        )

        if pasted_chunks:
            total_chunks += store_chunks(
                collection=collection,
                chunks=pasted_chunks,
                source_name=pasted_text_name,
                source_type="pasted_text",
                doc_id=doc_id
            )
            add_doc_to_registry(doc_id, pasted_text_name, "pasted_text")
            added_docs.append({
                "doc_id": doc_id,
                "name": pasted_text_name,
                "source_type": "pasted_text"
            })

    if uploaded_files:
        for uploaded_file in uploaded_files:
            filename, chunks = extract_text(uploaded_file)

            if not chunks:
                continue

            doc_id = str(uuid.uuid4())

            total_chunks += store_chunks(
                collection=collection,
                chunks=chunks,
                source_name=filename,
                source_type="uploaded_file",
                doc_id=doc_id
            )

            add_doc_to_registry(doc_id, filename, "uploaded_file")
            added_docs.append({
                "doc_id": doc_id,
                "name": filename,
                "source_type": "uploaded_file"
            })

    return total_chunks, added_docs


def delete_document(doc_id: str):
    collection = get_collection()

    results = collection.get(
        where={"doc_id": doc_id}
    )

    ids_to_delete = results.get("ids", [])

    if ids_to_delete:
        collection.delete(ids=ids_to_delete)

    delete_doc_from_registry(doc_id)


def reset_all_documents():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    chroma_client.create_collection(name=COLLECTION_NAME)
    save_registry([])