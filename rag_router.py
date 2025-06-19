# rag_router.py
"""
FastAPI router for the RAG system.

This module uses the latest LangChain patterns for conversational RAG,
including a history-aware retriever to improve follow-up questions.
Now supports processing multiple PDFs into a single conversational context.
"""
import os
import tempfile
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel, Field

# --- Core LangChain and AI Model Imports ---
# New imports for the advanced conversational chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Standard imports
from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# --- Pydantic Models for API Data Validation ---
class ChatMessage(BaseModel):
    role: str
    content: str

class QuestionRequest(BaseModel):
    question: str
    chat_history: List[ChatMessage] = Field(default_factory=list)

class AnswerResponse(BaseModel):
    # The chain will now return more than just the answer, but we'll extract it.
    answer: str

class ProcessResponse(BaseModel):
    message: str
    filenames: List[str]

# --- Core RAG Logic Class ---
class RAGSystem:
    """Encapsulates the RAG models and chain creation logic."""
    def __init__(self, google_api_key: str):
        if not google_api_key:
            raise ValueError("Google API Key is required for RAGSystem.")
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=google_api_key, temperature=0.5)
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=google_api_key)

    def create_rag_chain(self, pdf_bytes_list: List[bytes]) -> Runnable:
        """Creates a conversational RAG chain from a list of PDF byte streams."""
        all_documents = []
        for pdf_bytes in pdf_bytes_list:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(pdf_bytes)
                temp_file_path = temp_file.name
            
            try:
                loader = PyPDFLoader(file_path=temp_file_path)
                documents = loader.load()
                all_documents.extend(documents)
            finally:
                os.unlink(temp_file_path)

        if not all_documents:
            raise ValueError("Failed to load any documents from the provided PDFs.")
        
        docs = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=150).split_documents(all_documents)
        vector_store = FAISS.from_documents(docs, self.embeddings)
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})

        # --- LATEST LANGCHAIN PATTERN ---

        # 1. Prompt to rephrase the user's question into a standalone search query
        rephrase_question_prompt = ChatPromptTemplate.from_messages([
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            ("user", "Given the above conversation, generate a search query to look up in order to get information relevant to the conversation")
        ])
        
        # 2. Create a history-aware retriever chain
        history_aware_retriever = create_history_aware_retriever(
            self.llm, retriever, rephrase_question_prompt
        )

        # 3. Prompt to answer the question using the retrieved context
        answer_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are 'DocQuery AI', a professional AI assistant. Answer the user's questions based on the provided document context. If the context doesn't contain the answer, say so. Be concise and polite.\n\nContext:\n{context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
        ])
        
        # 4. Create a chain to "stuff" the retrieved documents into the final prompt
        document_chain = create_stuff_documents_chain(self.llm, answer_prompt)

        # 5. Combine the chains into a final retrieval chain
        conversational_retrieval_chain = create_retrieval_chain(
            history_aware_retriever, document_chain
        )
        
        return conversational_retrieval_chain

# --- State Management (remains the same) ---
class RAGState:
    def __init__(self, rag_system_instance: RAGSystem):
        self.rag_system = rag_system_instance
        self.rag_chain: Runnable | None = None

try:
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    rag_system_instance = RAGSystem(google_api_key=GOOGLE_API_KEY)
    rag_state = RAGState(rag_system_instance=rag_system_instance)
except (ValueError, TypeError) as e:
    raise RuntimeError(f"Failed to initialize RAG system. Is GOOGLE_API_KEY set? Error: {e}")

def get_rag_state():
    return rag_state

# --- API Router Definition ---
router = APIRouter(prefix="/rag-bot", tags=["RAG Q&A"])

@router.post("/process-pdf/", response_model=ProcessResponse)
async def process_pdf_endpoint(files: List[UploadFile] = File(...), state: RAGState = Depends(get_rag_state)):
    pdf_bytes_list = []
    filenames = []
    for file in files:
        if file.content_type != 'application/pdf':
            # Skip non-PDF files or raise an error. Here, we raise an error.
            raise HTTPException(status_code=400, detail=f"Invalid file type: {file.filename}. Please upload only PDF files.")
        
        pdf_bytes_list.append(await file.read())
        filenames.append(file.filename)

    if not pdf_bytes_list:
        raise HTTPException(status_code=400, detail="No PDF files were provided.")

    try:
        # Create a single RAG chain from all provided documents
        state.rag_chain = state.rag_system.create_rag_chain(pdf_bytes_list)
        return {"message": "PDFs processed successfully.", "filenames": filenames}
    except Exception as e:
        print(f"Error processing PDFs: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process PDFs: {str(e)}")

@router.post("/ask/", response_model=AnswerResponse)
async def ask_question_endpoint(request: QuestionRequest, state: RAGState = Depends(get_rag_state)):
    if state.rag_chain is None:
        raise HTTPException(status_code=400, detail="No documents have been processed. Please upload one or more PDFs first.")
    
    # Convert chat history from Pydantic models to LangChain message objects
    chat_history_messages: List[BaseMessage] = []
    for msg in request.chat_history:
        if msg.role == "user":
            chat_history_messages.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            chat_history_messages.append(AIMessage(content=msg.content))

    try:
        input_data = {"input": request.question, "chat_history": chat_history_messages}
        response = state.rag_chain.invoke(input_data)
        
        return {"answer": response.get("answer", "No answer could be generated.")}
    except Exception as e:
        print(f"Error invoking RAG chain: {e}")
        raise HTTPException(status_code=500, detail=f"An error occurred while generating the answer: {str(e)}")