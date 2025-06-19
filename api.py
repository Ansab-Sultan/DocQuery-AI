# api.py
"""
Main FastAPI application entry point.

This script initializes the FastAPI application and includes the necessary
routers from other modules.
"""
from fastapi import FastAPI
from dotenv import load_dotenv

# Import the router from our new module
from rag_router import router as rag_bot_router

# Load environment variables from a .env file
load_dotenv()

app = FastAPI(
    title="DocQuery API",
    description="A professional API for processing documents and answering questions using a RAG pipeline.",
    version="1.1.0",
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

# Include the RAG router. All endpoints defined in rag_router.py will be
# available under the main application.
app.include_router(rag_bot_router)

@app.get("/", tags=["Root"])
def read_root():
    """A simple root endpoint to confirm the API is running."""
    return {"status": "DocQuery API is running and ready."}
