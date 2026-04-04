from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import json

from ingest import ingest_sources
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


@app.post("/upload")
async def upload_documents(
    files: List[UploadFile] = File(default=[]),
    pasted_text: str = Form(default=""),
    reset_db: bool = Form(default=True)
):
    parsed_files = []

    for file in files:
        parsed_files.append({
            "filename": file.filename,
            "file_bytes": await file.read()
        })

    total_chunks = ingest_sources(
        uploaded_files=parsed_files,
        pasted_text=pasted_text,
        reset_db=reset_db
    )

    return {
        "message": "Ingestion complete",
        "total_chunks": total_chunks
    }


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