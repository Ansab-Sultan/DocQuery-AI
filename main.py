# main.py (Streamlit App)
"""
A Streamlit web application for interacting with a RAG (Retrieval-Augmented Generation) system.

This UI allows users to:
- Upload one or more PDF documents.
- Ask questions based on the combined content of the uploaded documents.
- View the AI-generated answers in a conversational format.
"""

import streamlit as st
import requests
from dotenv import load_dotenv
import os

# --- Page Configuration ---
st.set_page_config(
    page_title="DocQuery AI",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Environment Variables & API Configuration ---
load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
PROCESS_PDF_URL = f"{API_URL}/rag-bot/process-pdf/"
ASK_QUESTION_URL = f"{API_URL}/rag-bot/ask/"

# --- Session State Initialization ---
if 'pdf_processed' not in st.session_state:
    st.session_state.pdf_processed = False
if 'pdf_filenames' not in st.session_state:
    st.session_state.pdf_filenames = []
if 'error_message' not in st.session_state:
    st.session_state.error_message = ""
if 'messages' not in st.session_state:
    st.session_state.messages = []

# --- UI Layout ---
st.title("📄 DocQuery AI")
st.subheader("Your intelligent document assistant.")

# --- Step 1: Document Upload ---
st.header("1. Upload Your Documents")
uploaded_files = st.file_uploader(
    "Choose one or more PDF files to analyze. Your documents are processed securely.",
    type="pdf",
    key="pdf_uploader",
    accept_multiple_files=True
)

if uploaded_files:
    if st.button("Process Documents", use_container_width=True):
        with st.spinner("Analyzing your documents... This may take a moment."):
            # Prepare files for multipart upload
            files_to_upload = [('files', (file.name, file.getvalue(), 'application/pdf')) for file in uploaded_files]
            
            try:
                # Increased timeout for potentially large documents
                response = requests.post(PROCESS_PDF_URL, files=files_to_upload, timeout=300)
                response.raise_for_status() 
                
                result = response.json()
                st.session_state.pdf_processed = True
                st.session_state.pdf_filenames = result.get("filenames", [])
                st.session_state.error_message = ""
                # Reset the chat history when new documents are processed
                st.session_state.messages = []
                
                processed_files_str = ", ".join([f"**{name}**" for name in st.session_state.pdf_filenames])
                st.success(f"Successfully processed: {processed_files_str}!")

            except requests.exceptions.RequestException as e:
                st.session_state.pdf_processed = False
                st.session_state.error_message = f"Failed to connect to the backend API. Please ensure it is running. Error: {e}"
            except Exception as e:
                st.session_state.pdf_processed = False
                st.session_state.error_message = f"An error occurred during processing: {e}"

# Display any errors that occurred during processing
if st.session_state.error_message:
    st.error(st.session_state.error_message, icon="🚨")

# --- Step 2: Chat Interface ---
st.header("2. Ask Questions")

if st.session_state.pdf_processed:
    processed_files_str = ", ".join([f"**{name}**" for name in st.session_state.pdf_filenames])
    st.info(f"Ready to answer questions about {processed_files_str}.", icon="✅")

    # Display chat history from session state
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # User chat input
    if prompt := st.chat_input("e.g., What is the main topic of these documents?"):
        # Add user's message to chat history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    payload = {
                        "question": prompt,
                        "chat_history": st.session_state.messages[:-1] 
                    }
                    response = requests.post(ASK_QUESTION_URL, json=payload, timeout=120)
                    response.raise_for_status()

                    answer = response.json().get("answer", "I couldn't find an answer in the documents.")
                    st.write(answer)
                    # Add assistant's response to chat history
                    st.session_state.messages.append({"role": "assistant", "content": answer})

                except requests.exceptions.RequestException:
                    st.error("Failed to get an answer from the backend. Please check the API connection.", icon="🚨")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}", icon="🚨")
else:
    st.warning("Please upload and process one or more PDF documents to begin asking questions.", icon="⬆️")