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

def split_text_into_chunks(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )
    return splitter.split_text(text)

def extract_text_from_pdf(file_bytes):
    reader = PdfReader(BytesIO(file_bytes))
    extracted = []

    for page_index, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if not page_text or not page_text.strip():
            continue
        page_chunks = split_text_into_chunks(page_text)

        for chunks in page_chunks:
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
        text = paragraph.text.strip():
        if text:
            paragraphs.append((i + 1, text))
    
    for para_num, text in paragraphs:
        para_chunks = split_text_into_chunks(text)
    
        for chunks in para_chunks:
            extracted.append({
                "page_number": page_index + 1,
                "line_start": None,
                "line_end": None,
                "paragraph_start": para_num,
                "paragraph_end": para_num
            })

    return "\n".join(paragraphs)


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


def store_chunks(collection, chunks, source_name, source_type):
    stored_count = 0
    safe_source_name = source_name.replace(" ", "_")

    for i, chunk in enumerate(chunks):
        chunk_text = chunk_data["text"].strip()
        if not chunk_text:
            continue
        embedding = get_embedding(chunk)

        collection.add(
            ids=[f"{safe_source_name}_{i}"],
            documents=[chunk],
            metadatas={
                "source_name": source_name,
                "source_type": source_type,
                "chunk_id": i,
                "page_number": chunk_data["page_number"],
                "line_start": chunk_data["line_start"],
                "line_end": chunk_data["line_end"],
                "paragraph_start": chunk_data["paragraph_start"],
                "paragraph_end": chunk_data["paragraph_end"]
            }

            collection.add(
                ids=[f"{safe_source_name}_{i}"],
                documents=[chunk_text],
                metadatas=[metadata],
                embeddings=[embedding]
            )
        )
        stored_count += 1
    return stored_count


def ingest_sources(uploaded_files=None, pasted_text=None, reset_db=True):
    collection = get_collection(reset_db=reset_db)
    total_chunks = 0

    if pasted_text and pasted_text.strip():
        pasted_chunks = split_text_into_chunks(pasted_text.encode("utf-8"))
        total_chunks += store_chunks(
            collection=collection,
            chunks=pasted_chunks,
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

