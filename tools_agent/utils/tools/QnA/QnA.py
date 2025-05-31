# tools_agent/utils/tools/QnA/QnA.py - Fixed version without auth requirement

import httpx
import asyncio
from typing import List, Dict, Any, Optional, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from langchain_core.runnables import RunnableConfig

# Your backend URL
BACKEND_URL = "https://vesty-app-fastapi.onrender.com"  # Update this to your actual backend URL

class DocumentQueryInput(BaseModel):
    query: str = Field(description="The question to ask about the documents")

class ListDocumentsInput(BaseModel):
    """Input for listing documents - no parameters needed"""
    pass

class RefreshIndexInput(BaseModel):
    """Input for refreshing document index - no parameters needed"""
    pass

class SimpleDocumentQATool(BaseTool):
    name: str = "query_documents"
    description: str = """Ask questions about documents in the static document library.
    This tool can help answer questions about contracts, inspection reports, 
    property documents, and other real estate related files.
    
    Examples:
    - "What documents are available?"
    - "What are the key terms in the purchase agreement?"
    - "What is mentioned about the inspection?"
    - "Summarize the main points of the contract"
    """
    args_schema: Type[BaseModel] = DocumentQueryInput

    async def _arun(self, query: str, **kwargs) -> str:
        """Query documents asynchronously"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # No authentication needed for static documents
                response = await client.get(f"{BACKEND_URL}/api/documents/static")
                
                if response.status_code == 200:
                    data = response.json()
                    documents = data.get("documents", [])
                    
                    if not documents:
                        return "📄 **No documents found in the library.**\n\nTo get started:\n1. Add PDF, DOCX, or TXT files to your `backend/static/documents` folder\n2. Restart your backend server\n3. Use the Documents sidebar to browse available files"
                    
                    # Generate a response based on the query and available documents
                    if "available" in query.lower() or "list" in query.lower():
                        result = f"📄 **Available Documents ({len(documents)}):**\n\n"
                        for doc in documents:
                            file_size = doc.get('file_size', 0)
                            size_str = f"{file_size // 1024}KB" if file_size > 0 else "Unknown size"
                            result += f"• **{doc['filename']}** ({size_str})\n"
                        
                        result += f"\n💡 **Next steps:** Use the Documents sidebar to select a specific document, then ask me questions about its content!"
                        return result
                    
                    else:
                        # For specific questions, provide guidance for now
                        result = f"📄 I found {len(documents)} documents in your library:\n\n"
                        for doc in documents[:5]:  # Show first 5
                            result += f"• {doc['filename']}\n"
                        
                        result += f"\n🤖 **To answer your question: \"{query}\"**\n"
                        result += "I'll need to implement document content analysis. For now:\n\n"
                        result += "1. Use the Documents sidebar to select a specific document\n"
                        result += "2. I can help you understand what documents are available\n"
                        result += "3. Full document Q&A coming in the next update!\n\n"
                        result += "💡 Which specific document would you like to focus on?"
                        
                        return result
                
                elif response.status_code == 404:
                    return "❌ **Document endpoint not found.** The `/api/documents/static` endpoint needs to be added to the backend server."
                else:
                    return f"❌ Error accessing document library: HTTP {response.status_code}"
                
        except httpx.TimeoutException:
            return "⏱️ Request timed out while accessing documents. Please try again."
        except httpx.ConnectError:
            return "🔌 Cannot connect to the document server. Please check if the backend is running."
        except Exception as e:
            return f"❌ Error accessing documents: {str(e)}"
    
    def _run(self, query: str, **kwargs) -> str:
        """Synchronous wrapper"""
        return asyncio.run(self._arun(query, **kwargs))

class ListDocumentsTool(BaseTool):
    name: str = "list_available_documents"
    description: str = """List all documents available in the static document library.
    Shows what documents are ready for Q&A and analysis.
    """
    args_schema: Type[BaseModel] = ListDocumentsInput

    async def _arun(self, **kwargs) -> str:
        """List documents asynchronously"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # No authentication needed for static documents
                response = await client.get(f"{BACKEND_URL}/api/documents/static")
                
                if response.status_code == 200:
                    data = response.json()
                    documents = data.get("documents", [])
                    
                    if not documents:
                        return "📄 **No documents found in the static library.**\n\n" + \
                               "To add documents:\n" + \
                               "1. Place PDF, DOCX, or TXT files in `backend/static/documents/`\n" + \
                               "2. Restart your backend server\n" + \
                               "3. Use the Documents sidebar to browse files"
                    
                    result = f"📄 **Document Library ({len(documents)} files):**\n\n"
                    
                    total_size = 0
                    for doc in documents:
                        file_size = doc.get('file_size', 0)
                        total_size += file_size
                        size_str = f"{file_size // 1024}KB" if file_size > 0 else "Unknown"
                        file_type = doc.get('file_type', '').upper().replace('.', '')
                        
                        result += f"• **{doc['filename']}**\n"
                        result += f"  └ {size_str} • {file_type} document\n\n"
                    
                    result += f"📊 **Total:** {len(documents)} documents, {total_size // 1024}KB\n\n"
                    result += "💡 **Usage:** Select a document from the sidebar to ask specific questions about its content!"
                    
                    return result
                
                elif response.status_code == 404:
                    return "❌ **Document endpoint not found.** Please add the `/api/documents/static` endpoint to your backend server."
                else:
                    return f"❌ Error loading document library: HTTP {response.status_code}"
                
        except httpx.TimeoutException:
            return "⏱️ Request timed out while loading documents. Please try again."
        except httpx.ConnectError:
            return "🔌 Cannot connect to the document server. Please check if the backend is running."
        except Exception as e:
            return f"❌ Error listing documents: {str(e)}"
    
    def _run(self, **kwargs) -> str:
        """Synchronous wrapper"""
        return asyncio.run(self._arun(**kwargs))

class RefreshIndexTool(BaseTool):
    name: str = "refresh_document_index"
    description: str = """Refresh the document search index. This is a placeholder for now.
    Will be implemented in the next update to enable full document search capabilities.
    """
    args_schema: Type[BaseModel] = RefreshIndexInput

    async def _arun(self, **kwargs) -> str:
        """Refresh index asynchronously"""
        return "🔄 **Document indexing feature coming soon!**\n\nThis will enable:\n• Full text search through documents\n• Advanced Q&A capabilities\n• Document content analysis\n\nFor now, you can browse and select documents from the sidebar."
    
    def _run(self, **kwargs) -> str:
        """Synchronous wrapper"""
        return asyncio.run(self._arun(**kwargs))

# Create tool instances
query_documents = SimpleDocumentQATool()
list_available_documents = ListDocumentsTool()
refresh_document_index = RefreshIndexTool()

# Export tools for use in agent
__all__ = [
    "query_documents",
    "list_available_documents", 
    "refresh_document_index"
]