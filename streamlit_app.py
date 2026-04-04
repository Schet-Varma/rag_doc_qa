import streamlit as st
from app import answer_question

st.title("RAG Document Q&A")

question = st.text_input("Ask a question about the document:")

if question:
    answer = answer_question(question)
    st.write(answer)