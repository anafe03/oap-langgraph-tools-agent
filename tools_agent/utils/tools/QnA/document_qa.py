# tools_agent/utils/tools/QnA/document_qa.py

import os
import json
import asyncio
from typing import List, Dict, Optional, Annotated
from pathlib import Path
import PyPDF2
import docx
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain_core.tools import tool
from langchain.chains import RetrievalQA
from langchain.chat_models import init_chat_model

# Global variables for document store
document_store = None
document_metadata = {}

# Initialize paths
STATIC_DOCS_PATH = Path("backend/static/documents")
UPLOADS_DOCS_PATH = Path("backend/uploads")
VECTOR_STORE_PATH = Path("backend/vector_store")

# Ensure directories exist
STATIC_DOCS_PATH.mkdir(parents=True, exist_ok=True)
UPLOADS_DOCS_PATH.mkdir(parents=True, exist_ok=True)
VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)


def extract_text_from_file(file_path: Path) -> str:
    """Extract text from various file formats."""
    file_extension = file_path.suffix.lower()
    
    try:
        if file_extension == '.pdf':
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
                
        elif file_extension == '.docx':
            doc = docx.Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
            
        elif file_extension == '.txt':
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
                
        else:
            return f"Unsupported file format: {file_extension}"
            
    except Exception as e:
        return f"Error reading file {file_path.name}: {str(e)}"


def load_documents_from_directory(directory: Path, source_type: str) -> List[Dict]:
    """Load all documents from a directory."""
    documents = []
    
    if not directory.exists():
        return documents
    
    for file_path in directory.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in ['.pdf', '.docx', '.txt']:
            text = extract_text_from_file(file_path)
            if text and not text.startswith("Error") and not text.startswith("Unsupported"):
                documents.append({
                    'content': text,
                    'metadata': {
                        'source': str(file_path),
                        'filename': file_path.name,
                        'source_type': source_type,
                        'file_size': file_path.stat().st_size
                    }
                })
    
    return documents


async def initialize_document_store():
    """Initialize or refresh the document vector store."""
    global document_store, document_metadata
    
    try:
        # Load documents from both directories
        static_docs = load_documents_from_directory(STATIC_DOCS_PATH, "static")
        uploaded_docs = load_documents_from_directory(UPLOADS_DOCS_PATH, "uploaded")
        
        all_documents = static_docs + uploaded_docs
        
        if not all_documents:
            print("No documents found to index")
            return False
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )
        
        texts = []
        metadatas = []
        
        for doc in all_documents:
            chunks = text_splitter.split_text(doc['content'])
            for i, chunk in enumerate(chunks):
                texts.append(chunk)
                chunk_metadata = doc['metadata'].copy()
                chunk_metadata['chunk_id'] = i
                metadatas.append(chunk_metadata)
        
        # Create embeddings and vector store
        embeddings = OpenAIEmbeddings()
        document_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)
        
        # Save metadata
        document_metadata = {
            'total_documents': len(all_documents),
            'static_documents': len(static_docs),
            'uploaded_documents': len(uploaded_docs),
            'total_chunks': len(texts),
            'files': [doc['metadata']['filename'] for doc in all_documents]
        }
        
        # Save vector store
        document_store.save_local(str(VECTOR_STORE_PATH))
        
        with open(VECTOR_STORE_PATH / "metadata.json", 'w') as f:
            json.dump(document_metadata, f, indent=2)
        
        print(f"Document store initialized with {len(all_documents)} documents")
        return True
        
    except Exception as e:
        print(f"Error initializing document store: {str(e)}")
        return False


def load_existing_document_store():
    """Load existing vector store if available."""
    global document_store, document_metadata
    
    try:
        if (VECTOR_STORE_PATH / "index.faiss").exists():
            embeddings = OpenAIEmbeddings()
            document_store = FAISS.load_local(str(VECTOR_STORE_PATH), embeddings, allow_dangerous_deserialization=True)
            
            if (VECTOR_STORE_PATH / "metadata.json").exists():
                with open(VECTOR_STORE_PATH / "metadata.json", 'r') as f:
                    document_metadata = json.load(f)
            
            return True
    except Exception as e:
        print(f"Error loading existing document store: {str(e)}")
    
    return False


@tool(name="query_documents", description="Query and ask questions about uploaded documents and static documents in the knowledge base")
async def query_documents(
    question: Annotated[str, "The question to ask about the documents"],
    document_type: Annotated[str, "Type of documents to search: 'all', 'static', or 'uploaded'"] = "all",
    max_results: Annotated[int, "Maximum number of relevant document chunks to consider"] = 5
) -> str:
    """
    Query documents in the knowledge base to answer questions.
    
    This tool searches through both static documents (pre-loaded) and user-uploaded documents
    to find relevant information and answer questions.
    """
    global document_store, document_metadata
    
    try:
        # Load document store if not already loaded
        if document_store is None:
            if not load_existing_document_store():
                await initialize_document_store()
        
        if document_store is None:
            return "❌ No documents are currently available in the knowledge base. Please upload some documents first."
        
        # Create retrieval chain
        model = init_chat_model("openai:gpt-4o-mini", temperature=0.3)
        
        # Filter by document type if specified
        filter_dict = None
        if document_type != "all":
            filter_dict = {"source_type": document_type}
        
        # Perform similarity search
        retriever = document_store.as_retriever(
            search_kwargs={
                "k": max_results,
                "filter": filter_dict
            }
        )
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=model,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # Get answer
        result = qa_chain({"query": question})
        
        # Format response with sources
        answer = result['result']
        sources = result['source_documents']
        
        response = f"📄 **Answer based on your documents:**\n\n{answer}\n\n"
        
        if sources:
            response += "**📚 Sources:**\n"
            seen_files = set()
            for doc in sources:
                filename = doc.metadata.get('filename', 'Unknown file')
                source_type = doc.metadata.get('source_type', 'unknown')
                if filename not in seen_files:
                    response += f"• {filename} ({source_type})\n"
                    seen_files.add(filename)
        
        # Add document store info
        if document_metadata:
            response += f"\n**📊 Knowledge Base Info:**\n"
            response += f"• Total documents: {document_metadata.get('total_documents', 0)}\n"
            response += f"• Static documents: {document_metadata.get('static_documents', 0)}\n"
            response += f"• Uploaded documents: {document_metadata.get('uploaded_documents', 0)}\n"
        
        return response
        
    except Exception as e:
        return f"❌ Error querying documents: {str(e)}"


@tool(name="list_available_documents", description="List all documents currently available in the knowledge base")
async def list_available_documents() -> str:
    """
    List all documents currently available in the knowledge base.
    Shows both static documents and user-uploaded documents.
    """
    global document_metadata
    
    try:
        # Load document store if not already loaded
        if document_store is None:
            if not load_existing_document_store():
                await initialize_document_store()
        
        if not document_metadata:
            return "📄 No documents are currently available in the knowledge base."
        
        response = "📚 **Available Documents in Knowledge Base:**\n\n"
        
        # Get file info from directories
        static_files = []
        uploaded_files = []
        
        if STATIC_DOCS_PATH.exists():
            static_files = [f.name for f in STATIC_DOCS_PATH.iterdir() 
                          if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.txt']]
        
        if UPLOADS_DOCS_PATH.exists():
            uploaded_files = [f.name for f in UPLOADS_DOCS_PATH.iterdir() 
                            if f.is_file() and f.suffix.lower() in ['.pdf', '.docx', '.txt']]
        
        # Static documents
        if static_files:
            response += "**📁 Static Documents (Pre-loaded):**\n"
            for filename in static_files:
                response += f"• {filename}\n"
            response += "\n"
        
        # Uploaded documents
        if uploaded_files:
            response += "**📤 Uploaded Documents:**\n"
            for filename in uploaded_files:
                response += f"• {filename}\n"
            response += "\n"
        
        # Summary
        response += f"**📊 Summary:**\n"
        response += f"• Total documents: {len(static_files) + len(uploaded_files)}\n"
        response += f"• Static documents: {len(static_files)}\n"
        response += f"• Uploaded documents: {len(uploaded_files)}\n"
        
        if not static_files and not uploaded_files:
            response += "\n💡 To get started, upload some documents using the file upload feature."
        
        return response
        
    except Exception as e:
        return f"❌ Error listing documents: {str(e)}"


@tool(name="refresh_document_index", description="Refresh the document index to include newly uploaded files")
async def refresh_document_index() -> str:
    """
    Refresh the document index to include any newly uploaded files.
    Use this after uploading new documents to make them searchable.
    """
    try:
        success = await initialize_document_store()
        
        if success:
            return "✅ Document index refreshed successfully! All uploaded documents are now searchable."
        else:
            return "❌ Failed to refresh document index. Please check if documents are properly uploaded."
            
    except Exception as e:
        return f"❌ Error refreshing document index: {str(e)}"


# Initialize document store on module load
async def init_document_qa():
    """Initialize the document Q&A system."""
    if not load_existing_document_store():
        await initialize_document_store()

# Run initialization when module is imported
try:
    import asyncio
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If event loop is already running, schedule the initialization
        asyncio.create_task(init_document_qa())
    else:
        # If no event loop is running, run the initialization
        asyncio.run(init_document_qa())
except Exception as e:
    print(f"Note: Document Q&A will initialize on first use. {str(e)}")