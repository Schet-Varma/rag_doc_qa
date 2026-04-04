# RAG Document Q&A

A full-stack **Retrieval-Augmented Generation (RAG)** application that allows users to upload documents or paste raw text, store semantically searchable chunks in a local vector database, and ask grounded questions about the uploaded content through a **React frontend** and **FastAPI backend**.

This project was built to explore how modern LLM applications work end-to-end in practice — not just calling an API, but actually building the full workflow of:

- document ingestion
- text extraction
- chunking
- embeddings
- vector search
- prompt grounding
- answer generation
- frontend/backend integration

---

## What This Project Does

This app allows a user to:

- upload files such as PDFs, DOCX files, and text/code files
- paste raw text directly into the UI
- convert uploaded content into smaller chunks
- create embeddings for those chunks
- store those embeddings in **ChromaDB**
- ask questions about the uploaded content
- retrieve the most relevant chunks
- generate answers based only on the retrieved content
- view the retrieved sources that the answer came from

In simple words, instead of asking a language model to answer from general knowledge, this project first **looks through the uploaded content**, finds the most relevant pieces, and only then asks the model to answer using those pieces.

That is the core idea behind **RAG**.

---

## What Is RAG?

**RAG** stands for **Retrieval-Augmented Generation**.

It is a pattern used in LLM applications where the model is given helpful external information before answering a question.

### Normal LLM flow

Without RAG, a language model may:

- guess
- rely on training data
- hallucinate
- answer without knowing anything about the user’s uploaded document

### RAG flow

With RAG, the app does this:

1. read the document
2. split it into smaller chunks
3. turn those chunks into embeddings
4. store them in a vector database
5. embed the user’s question too
6. retrieve the most similar chunks
7. send those chunks as context to the model
8. generate a more grounded answer

This makes the answer far more useful for document-based Q&A.

---

## Why I Built This

The aim of this project was to move beyond a simple “call OpenAI and print output” setup and build something closer to a real AI product.

I wanted to understand:

- how documents are prepared for semantic search
- how embeddings and vector databases work together
- how retrieval improves answer quality
- how to structure an AI project as a full-stack application
- how to build a working MVP with a frontend and backend

This project was also a way to learn how to connect modern AI workflows with software engineering structure.

---

## Main Features

### Current features

- upload multiple files
- paste text directly into the app
- extract text from supported file types
- split large text into smaller chunks
- create embeddings using OpenAI
- store embeddings locally in ChromaDB
- retrieve relevant chunks for a user query
- generate grounded answers
- display retrieved sources in the UI
- maintain lightweight conversation history
- React frontend + FastAPI backend architecture

---

## Supported Input Types

The current version supports:

- `.pdf`
- `.docx`
- `.txt`
- `.md`

And also many plain-text-like/code-like files such as:

- `.py`
- `.js`
- `.ts`
- `.jsx`
- `.tsx`
- `.json`
- `.csv`
- `.html`
- `.css`
- `.sql`
- `.java`
- `.c`
- `.cpp`
- `.xml`
- `.yaml`
- `.yml`

It also supports directly pasted text from the frontend.

---

## Tech Stack

### Frontend

- React
- Vite
- Axios
- CSS

### Backend

- Python
- FastAPI
- Uvicorn

### RAG / NLP / Data

- OpenAI API
- ChromaDB
- LangChain text splitters
- PyPDF
- python-docx

## Project Architecture

React Frontend → FastAPI Backend → ChromaDB + OpenAI API

### Frontend responsibilities

The React frontend is responsible for:

- letting the user upload files
- letting the user paste text
- sending upload requests to the backend
- sending questions to the backend
- displaying answers
- showing retrieved source chunks
- showing simple conversation history

### Backend responsibilities

The FastAPI backend is responsible for:

- receiving files and text from the frontend
- extracting readable text from files
- splitting text into chunks
- generating embeddings
- storing embeddings in ChromaDB
- embedding the user’s question
- retrieving the most relevant chunks
- building the grounded prompt
- calling the model for answer generation
- returning the answer and sources to the frontend

### ChromaDB responsibilities

ChromaDB is used to store:

- document chunks
- chunk embeddings
- metadata such as source name and chunk id

---

## Why ChromaDB?

ChromaDB was chosen because it is a **local vector database** that is simple and practical for personal projects and prototypes.

### Why it made sense here

- very easy to set up locally
- no external infrastructure required
- good for small to medium-sized document collections
- simple Python integration
- supports persistent local storage
- makes debugging retrieval easier during development

### Important note

ChromaDB **is** a vector database.

So the comparison is not:

- ChromaDB vs vector database

It is really:

- **ChromaDB (local vector database)** vs **managed/hosted vector database**

### Why not use a hosted vector database?

A managed vector database such as Pinecone or other cloud options was unnecessary for this project because:

- this is a local MVP / portfolio project
- the amount of data is small
- local development is cheaper
- it keeps the architecture simpler
- adding cloud infra early would create extra complexity without much gain

---

## Why OpenAI?

OpenAI is used for two key parts of the pipeline:

### 1. Embeddings

The project uses **`text-embedding-3-small`** to convert chunks and user questions into vector representations.

Embeddings are what allow semantic retrieval to happen.

### 2. Answer generation

The backend uses a lightweight OpenAI generation model to answer questions using the retrieved chunks as context.

### Why OpenAI was chosen

- simple API integration
- high-quality embeddings
- reliable generation quality
- easy way to get an MVP working quickly

---

## Why the API Key Must Stay in the Backend

This is very important.

The **OpenAI API key must never be placed in the React frontend**.

### Why?

The frontend runs in the browser. If you put the key there, it can be exposed publicly and anyone could misuse it.

### Correct setup

- frontend talks to backend
- backend talks to OpenAI
- API key stays only in the backend `.env` file

### Wrong setup

- React frontend calls OpenAI directly with your secret key

Do **not** do that.

---

## How the RAG Pipeline Works in This Project

Here is the full flow of what happens when the app is used:

### Step 1: user uploads files or pastes text

The frontend collects:

- uploaded file(s)
- pasted raw text

Then it sends them to the FastAPI backend.

### Step 2: text extraction

The backend checks the file type and extracts readable text:

- PDFs are parsed with `pypdf`
- DOCX files are parsed with `python-docx`
- text/code files are decoded as plain text

### Step 3: chunking

The extracted text is split into smaller chunks using a recursive text splitter.

This is important because large documents are too big to use directly, and retrieval works better on smaller pieces.

### Step 4: embeddings

Each chunk is converted into an embedding using OpenAI.

These embeddings are numerical representations of meaning.

### Step 5: storage in ChromaDB

The chunk text, embedding, and metadata are stored in ChromaDB.

Metadata includes things like:

- source name
- source type
- chunk id

### Step 6: user asks a question

The frontend sends the user’s question to the backend.

### Step 7: retrieve relevant chunks

The backend embeds the question and queries ChromaDB for the most relevant chunks.

### Step 8: build grounded prompt

The backend combines:

- retrieved chunk text
- chunk metadata
- optional conversation history

and builds a prompt for the model.

### Step 9: answer generation

The model generates an answer using only the retrieved context.

### Step 10: answer + sources returned

The backend sends back:

- the answer
- the retrieved sources

The frontend displays both.

---

## Directory Structure

    rag-doc-qa/
    ├── backend/
    │   ├── main.py
    │   ├── rag.py
    │   ├── ingest.py
    │   ├── requirements.txt
    │   ├── .env
    │   └── chroma_db/
    ├── frontend/
    │   ├── src/
    │   │   ├── App.jsx
    │   │   ├── App.css
    │   │   └── main.jsx
    │   ├── package.json
    │   └── vite.config.js
    ├── .gitignore
    └── README.md

### Folder explanation

#### `backend/`

Contains all Python backend logic.

##### `main.py`

FastAPI entry point that defines API routes such as:

- `POST /upload`
- `POST /ask`

##### `ingest.py`

Handles:

- text extraction
- chunking
- embedding generation
- storing chunks in ChromaDB

##### `rag.py`

Handles:

- question embedding
- retrieval
- prompt construction
- answer generation

##### `requirements.txt`

Python dependencies for the backend.

##### `.env`

Stores the user’s own OpenAI API key.

##### `chroma_db/`

Persistent local ChromaDB storage.

#### `frontend/`

Contains the React frontend.

##### `App.jsx`

Main UI logic.

##### `App.css`

Styling.

##### `main.jsx`

React entry point.

---

## Step-by-Step Setup

### 1. Clone the repository

    git clone <your-repo-url>
    cd rag-doc-qa

Replace `<your-repo-url>` with your actual GitHub repository URL.

---

### 2. Set up the backend

Go into the backend folder:

    cd backend

Create a virtual environment:

    python3 -m venv venv

Activate it:

#### macOS / Linux

    source venv/bin/activate

#### Windows

    venv\Scripts\activate

Install backend dependencies:

    python -m pip install -r requirements.txt

---

### 3. Create your own `.env` file

Inside the `backend/` folder, create a file called:

    .env

Put your own OpenAI API key inside it like this:

    OPENAI_API_KEY=your_api_key_here

### Important

You must use **your own API key**.

This repo does **not** contain an API key, and it should never contain one.

### Good practice

- create your own key
- keep it private
- do not commit it
- do not share it
- rotate it if you ever expose it accidentally

### 4. Run the backend

From inside `backend/`:

    uvicorn main:app --reload

If everything is working, the backend should start on:

    http://127.0.0.1:8000

You can also open the automatic API docs at:

    http://127.0.0.1:8000/docs

That page is very useful for testing the backend endpoints directly.

---

### 5. Set up the frontend

Open a second terminal and go into the frontend folder:

    cd frontend

Install frontend dependencies:

    npm install

Run the frontend:

    npm run dev

The frontend should open on something like:

    http://localhost:5173

---

### 6. How to use the app

1. start the backend
2. start the frontend
3. open the React app in the browser
4. upload one or more supported files, or paste text into the text area
5. click **Ingest Content**
6. wait for the document chunks to be stored
7. ask a question about the uploaded content
8. read the answer
9. inspect the retrieved sources shown in the UI

---

## Example Questions to Try

Here are some useful questions to test the app with any uploaded document.

### Factual questions

- What is the main purpose of this document?
- Which topics are mentioned most often?
- What achievements are listed?
- What challenges are described?

### Synthesis questions

- Summarise this document in 5 bullet points
- Compare the two projects mentioned in the document
- What are the strongest themes in the document?
- What are the top areas for improvement?

### Grounding / anti-hallucination questions

- What GRE score is mentioned?
- What scholarship amount is listed?
- What exact tuition fee is stated?

For questions like these, if the information is not actually in the document, the app should say it could not find it in the uploaded content.

That is an important test of whether the RAG system is staying grounded.

---

## What Makes This Better Than a Plain Chatbot?

A normal chatbot may:

- guess
- hallucinate
- answer from general training data
- ignore the actual uploaded content

This project instead:

- reads the uploaded content
- retrieves relevant chunks
- grounds the answer in that content
- shows the sources used

That makes it more useful for:

- document Q&A
- summarisation
- extracting insights from notes
- analysing statements of purpose, reports, or articles
- helping users work with their own files

---

## Why Chunking Is Important

Large documents are not stored as one giant block.

Instead, they are split into smaller pieces called **chunks**.

### Why?

- smaller chunks are easier to retrieve accurately
- long documents would otherwise be too large
- only relevant parts should be passed to the model
- it reduces unnecessary context

This project uses chunking so retrieval is more focused and answers are more grounded.

---

## Why Metadata Is Stored

Each chunk stores metadata such as:

- source name
- source type
- chunk id

This is useful because it allows the app to:

- display where the answer came from
- show retrieved chunks in the UI
- debug retrieval quality
- support better transparency

Without metadata, the app could still answer, but it would be much harder to explain the answer source.

## Security Notes

This project uses an API key, so security matters.

### You should do the following

- keep your key only in `backend/.env`
- make sure `.env` is in `.gitignore`
- never hardcode the key into Python or React code
- never push the key to GitHub
- never expose the key in the frontend

### Example `.gitignore`

    .env
    venv/
    __pycache__/
    backend/venv/
    backend/chroma_db/
    frontend/node_modules/
    frontend/dist/
    .DS_Store

---

## Important Note for Anyone Using This Repo

If you clone this project, **you must create your own `.env` file and add your own OpenAI API key**.

The app will not work without that.

This is expected and intentional.

The project is set up this way so that:

- secrets are not exposed
- each person can use their own key
- the repo stays safe to share publicly

---

## Testing Strategy

The app was tested in stages to reduce API usage and make debugging easier.

### Recommended test order

1. test with small pasted text
2. test with a small text file
3. test one small PDF
4. test simple factual questions
5. test synthesis-style questions
6. test missing-information questions

### Why this approach works

It helps separate the system into parts:

- ingestion
- retrieval
- generation

That way, if something breaks, it is easier to tell whether the issue is:

- file extraction
- chunking
- embeddings
- retrieval
- prompt grounding
- frontend/backend communication

---

## Current Limitations

This is still an MVP, so there are limitations.

### Current limitations

- no OCR support for scanned/image-based PDFs
- no support for legacy `.doc` files
- no authentication
- no user accounts
- no separate collections per user/project
- no cloud deployment yet
- conversation history is lightweight
- retrieval quality depends on chunking and document quality
- large folders / large-scale ingestion are not yet fully optimized

---

## Future Improvements

Planned improvements could include:

- drag-and-drop uploads
- OCR for scanned PDFs
- support for more file types
- better source citations
- retrieval-only debug mode
- multiple collections / projects
- per-document filtering
- user authentication
- deployment to the cloud
- Docker support
- better chunk ranking
- stronger prompt tuning
- support for large folder ingestion
- persistent chat sessions

---

## What I Learned From Building This

This project helped me understand how to build an actual AI application rather than just call an API.

Some of the main things explored through this project were:

- document parsing
- chunking strategies
- semantic retrieval
- embeddings
- vector databases
- prompt grounding
- backend API design
- frontend/backend integration
- how to structure an AI project as a realistic software project

It also showed the difference between:

- a quick prototype
- and a cleaner full-stack implementation

---

## Final Notes

This project is intended as a practical full-stack RAG MVP.

It is not a production-ready system yet, but it demonstrates the core ideas well:

- ingestion
- retrieval
- grounding
- answer generation
- document-based interaction

If you want to use it yourself:

- clone the repo
- add your own API key
- run the backend
- run the frontend
- upload a document
- ask questions

That’s it.

---

## Author

Built by **Schet Varma**.

If you found this project interesting, feel free to explore the code, try it with your own documents, and build on top of it.