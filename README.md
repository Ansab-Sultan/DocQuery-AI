# DocQuery AI: Intelligent Multi-Document Assistant

DocQuery AI is a sophisticated, conversational AI application designed to answer questions about your documents. It leverages a powerful Retrieval-Augmented Generation (RAG) pipeline, allowing you to have interactive, context-aware conversations based on the content of **one or more uploaded PDF files simultaneously**.

This system is built with a modern tech stack, featuring a FastAPI backend for robust API services and a Streamlit frontend for a user-friendly, interactive experience.

## ✨ Features

  - **Intuitive Multi-PDF Upload**: Easily upload a batch of PDF documents through a clean and simple web interface.
  - **Unified Conversational Context**: The contents of all uploaded documents are merged into a single knowledge base, allowing you to ask questions that draw information from across the entire set.
  - **Conversational Q\&A**: Ask follow-up questions.The AI remembers the previous turns of the conversation to provide contextually relevant answers.
  - **State-of-the-Art AI**: Powered by Google's Gemini 2.5 Flash model for fast and accurate language understanding and generation.
  - **Secure & Private**: Your documents are processed in memory for the duration of the session and are not stored permanently on the server.
  - **Developer-Friendly**: The project is modular, with a clear separation between the frontend (`main.py`), backend (`api.py`), and the core AI logic (`rag_router.py`), making it easy to extend and customize.

## 🚀 How It Works

The application employs an advanced conversational RAG pipeline built with LangChain. This approach ensures that the AI can handle follow-up questions effectively across a combined set of documents.

1.  **Multi-PDF Processing**: When one or more PDFs are uploaded, the application reads the content from each file.
2.  **Document Aggregation**: The text and metadata from all uploaded PDFs are loaded and collected into a single, unified list of documents.
3.  **Embedding & Indexing**: This combined collection of text is broken down into smaller chunks. These chunks are then converted into numerical representations (embeddings) using Google's embedding model and stored in a single, searchable FAISS vector store.
4.  **History-Aware Retriever**: When you ask a question, the system first considers the chat history to rephrase your question into a standalone query. This ensures that follow-up questions like "Can you compare the findings in both reports?" are understood in context.
5.  **Unified Document Retrieval**: The rephrased query is used to find the most relevant text chunks from the indexed collection of all uploaded PDFs.
6.  **Answer Generation**: The retrieved text chunks, along with the original question and chat history, are passed to the Gemini language model. The model, acting as 'DocQuery AI', synthesizes this information to generate a concise and accurate answer.

## 🛠️ Tech Stack

  - **Backend**: FastAPI, Uvicorn
  - **Frontend**: Streamlit
  - **AI/ML**: LangChain, Google Gemini 2.5 Flash, FAISS (for vector storage)
  - **Core Libraries**: Pydantic, Requests, python-dotenv 

## ⚙️ Getting Started

Follow these instructions to set up and run the DocQuery AI application on your local machine.

### Prerequisites

  - Python 3.8 or newer
  - A Google API Key with the "Generative Language API" enabled. You can obtain one from the [Google AI Studio](https://aistudio.google.com/app/apikey).

### 1\. Clone the Repository

```bash
git clone <repository-url>
cd <repository-directory>
```

### 2\. Set Up a Virtual Environment

It's highly recommended to use a virtual environment to manage project dependencies.

```bash
# For Unix/macOS
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
.\venv\Scripts\activate
```

### 3\. Install Dependencies

Install all the required Python packages using the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4\. Configure Environment Variables

Create a file named `.env` in the root directory of the project and add your Google API key:

```.env
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
```

The application uses `python-dotenv` to load this key automatically.

### 5\. Run the Backend Server

Start the FastAPI backend server using Uvicorn. The server will handle PDF processing and question-answering.

```bash
uvicorn api:app --reload
```

The API will be accessible at `http://127.0.0.1:8000`. You can see the auto-generated API documentation at `http://127.0.0.1:8000/docs`.

### 6\. Run the Frontend Application

In a **new terminal window**, navigate to the project directory and run the Streamlit application.

```bash
streamlit run main.py
```

The web application will open in your browser, and you can start uploading documents and asking questions.

## Usage

1.  **Upload Documents**: Open the web app, and you'll see the "Upload Your Documents" section. Click the uploader to select one or more PDF files from your computer.
2.  **Process Documents**: After selecting your files, click the "Process Documents" button. A spinner will indicate that the backend is analyzing and indexing the content from all provided documents.
3.  **Ask Questions**: Once processing is successful, the chat interface will become active, confirming which files have been processed. Type your questions about the documents' combined content into the chat input box and press Enter.
4.  **Converse**: The AI's response will appear. You can ask follow-up questions that refer to information across any of the uploaded documents, as the AI uses the entire conversation history to understand the context. A new document upload will reset the chat history and the knowledge base.