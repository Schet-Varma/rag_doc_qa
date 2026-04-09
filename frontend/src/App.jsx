import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

const API_BASE_URL = "http://127.0.0.1:8000";

function App() {
  const [files, setFiles] = useState([]);
  const [pastedText, setPastedText] = useState("");
  const [savedDraftName, setSavedDraftName] = useState("My Notes");
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [sources, setSources] = useState([]);
  const [chatHistory, setChatHistory] = useState([]);
  const [uploadMessage, setUploadMessage] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [isAsking, setIsAsking] = useState(false);

  useEffect(() => {
    const savedText = localStorage.getItem("rag_pasted_text");
    const savedDraft = localStorage.getItem("rag_draft_name");

    if (savedText) {
      setPastedText(savedText);
    }

    if (savedDraft) {
      setSavedDraftName(savedDraft);
    }
  }, []);

  useEffect(() => {
    localStorage.setItem("rag_pasted_text", pastedText);
  }, [pastedText]);

  useEffect(() => {
    localStorage.setItem("rag_draft_name", savedDraftName);
  }, [savedDraftName]);

  function handleFileChange(event) {
    setFiles(Array.from(event.target.files));
  }

  async function handleUpload() {
    if (files.length === 0 && pastedText.trim() === "") {
      setUploadMessage("Please upload files or paste some text first.");
      return;
    }

    const formData = new FormData();

    files.forEach((file) => {
      formData.append("files", file);
    });

    formData.append("pasted_text", pastedText);
    formData.append("reset_db", "true");

    try {
      setIsUploading(true);
      setUploadMessage("");

      const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });

      setUploadMessage(`Ingestion complete. Stored ${response.data.total_chunks} chunks.`);
    } catch (error) {
      setUploadMessage("Upload failed. Check backend/server.");
    } finally {
      setIsUploading(false);
    }
  }

  async function handleAsk() {
    if (question.trim() === "") {
      return;
    }

    const formData = new FormData();
    formData.append("question", question);
    formData.append("history", JSON.stringify(chatHistory));

    try {
      setIsAsking(true);

      const response = await axios.post(`${API_BASE_URL}/ask`, formData);

      const newAnswer = response.data.answer;
      const newSources = response.data.sources || [];

      setAnswer(newAnswer);
      setSources(newSources);

      setChatHistory((prev) => [
        ...prev,
        { question: question, answer: newAnswer },
      ]);
    } catch (error) {
      setAnswer("Something went wrong while getting the answer.");
      setSources([]);
    } finally {
      setIsAsking(false);
    }
  }
  
  function clearDraft() {
    setPastedText("");
    setSavedDraftName("My Notes");
    localStorage.removeItem("rag_pasted_text");
    localStorage.removeItem("rag_draft_name");
  }

  function clearChat() {
    setChatHistory([]);
    setAnswer("");
    setSources([]);
  }

  return (
    <div className="app-container">
      <h1>RAG Document Q&A</h1>
      <p className="subtitle">
        Upload multiple files, paste notes, and ask grounded questions about your content.
      </p>

      <div className="card">
        <h2>Upload Content</h2>

        <input type="file" multiple onChange={handleFileChange} />

        <p className="small-label">Saved text draft name</p>
        <input
          type="text"
          value={savedDraftName}
          onChange={(event) => setSavedDraftName(event.target.value)}
          placeholder="Name your pasted notes"
        />

        <textarea
          rows="10"
          placeholder="Or paste text here..."
          value={pastedText}
          onChange={(event) => setPastedText(event.target.value)}
        />

        <div className="button-row">
          <button onClick={handleUpload} disabled={isUploading}>
            {isUploading ? "Uploading..." : "Ingest Content"}
          </button>

          <button className="secondary-button" onClick={clearDraft}>
            Clear Saved Text
          </button>
        </div>

        {uploadMessage && <p className="status-message">{uploadMessage}</p>}
      </div>

      <div className="card">
        <h2>Ask a Question</h2>

        <input
          type="text"
          placeholder="Ask something about your uploaded content..."
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
        />

        <div className="button-row">
          <button onClick={handleAsk} disabled={isAsking}>
            {isAsking ? "Thinking..." : "Get Answer"}
          </button>

          <button className="secondary-button" onClick={clearChat}>
            Clear Chat
          </button>
        </div>

        {answer && (
          <div className="answer-box">
            <h3>Answer</h3>
            <p>{answer}</p>
          </div>
        )}

        {sources.length > 0 && (
          <div className="sources-box">
            <h3>Retrieved Sources</h3>
            {sources.map((source, index) => (
              <details key={index} className="source-item">
                <summary>
                  {source.source_label || source.metadata?.source_name || "Unknown source"}
                </summary>
                <p>{source.text}</p>
              </details>
            ))}
          </div>
        )}
      </div>

      {chatHistory.length > 0 && (
        <div className="card">
          <h2>Conversation History</h2>
          {chatHistory
            .slice()
            .reverse()
            .map((item, index) => (
              <details key={index} className="history-item">
                <summary>{item.question}</summary>
                <p>{item.answer}</p>
              </details>
            ))}
        </div>
      )}
    </div>
  );
}

export default App;