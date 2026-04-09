from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json

from ingest import ingest_sources, list_docs, delete_document
from rag import answer_question

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Backend is running"}


@app.get("/documents")
def get_documents():
    return {"documents": list_docs()}


@app.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(default=[]),
    pasted_text: str = Form(default=""),
    pasted_text_name: str = Form(default="My Notes")
):
    parsed_files = []

    for file in files:
        parsed_files.append({
            "filename": file.filename,
            "file_bytes": await file.read()
        })

    total_chunks, added_docs = ingest_sources(
        uploaded_files=parsed_files,
        pasted_text=pasted_text,
        pasted_text_name=pasted_text_name
    )

    return {
        "message": "Ingestion complete",
        "total_chunks": total_chunks,
        "added_docs": added_docs
    }


@app.delete("/documents/{doc_id}")
def remove_document(doc_id: str):
    delete_document(doc_id)
    return {"message": "Document deleted successfully"}


@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    history: str = Form(default="[]")
):
    chat_history = json.loads(history)

    result = answer_question(
        question=question,
        chat_history=chat_history
    )

    return result