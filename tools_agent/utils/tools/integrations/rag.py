# tools_agent/utils/tools/integrations/rag.py

import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Annotated
from langchain_core.tools import tool

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

class FSBORAG:
    def __init__(self):
        self.documents = {}
        self._load_pdf_documents()
    
    def _extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract text content from PDF file."""
        if not PDF_AVAILABLE:
            return "PyPDF2 not installed. Install with: pip install PyPDF2"
        
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            return f"Error reading PDF: {str(e)}"
    
    def _chunk_text(self, text: str, chunk_size: int = 600) -> List[str]:
        """Split text into searchable chunks."""
        # Clean up text
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r'\s+', ' ', text)
        
        # Split by sections first (look for common section markers)
        sections = re.split(r'(?:Phase \d+:|## |Step \d+:|Section \d+:)', text)
        
        chunks = []
        for section in sections:
            section = section.strip()
            if len(section) < 50:  # Skip very short sections
                continue
                
            # If section is small enough, keep as one chunk
            if len(section) <= chunk_size:
                chunks.append(section)
            else:
                # Split large sections by sentences
                sentences = re.split(r'[.!?]+', section)
                current_chunk = ""
                
                for sentence in sentences:
                    sentence = sentence.strip()
                    if not sentence:
                        continue
                        
                    if len(current_chunk + sentence) < chunk_size:
                        current_chunk += sentence + ". "
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = sentence + ". "
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
        
        return [chunk for chunk in chunks if len(chunk.strip()) > 30]
    
    def _load_pdf_documents(self):
        """Load PDF documents from static folder."""
        static_dir = Path(__file__).parent.parent.parent.parent.parent / "static"
        
        pdf_files = {
            "Kentucky FSBO Guide": "Kentucky_FSBO_Guide.pdf",
            "FSBO FAQ": "FSBO_Seller_FAQ.pdf"
        }
        
        for doc_name, filename in pdf_files.items():
            pdf_path = static_dir / filename
            
            if pdf_path.exists():
                print(f"Loading {doc_name}...")
                text_content = self._extract_text_from_pdf(pdf_path)
                
                if not text_content.startswith("Error") and not text_content.startswith("PyPDF2"):
                    chunks = self._chunk_text(text_content)
                    self.documents[doc_name] = {
                        'chunks': chunks,
                        'source_file': str(pdf_path),
                        'total_chunks': len(chunks)
                    }
                    print(f"  Loaded {len(chunks)} chunks from {filename}")
                else:
                    print(f"  Error loading {filename}: {text_content}")
            else:
                print(f"  File not found: {pdf_path}")
    
    def search(self, query: str, max_results: int = 2) -> List[Dict]:
        """Search through documents using keyword matching."""
        if not self.documents:
            return []
        
        query_words = query.lower().split()
        results = []
        
        for doc_name, doc_info in self.documents.items():
            chunks = doc_info.get('chunks', [])
            
            for i, chunk in enumerate(chunks):
                chunk_lower = chunk.lower()
                
                # Count exact word matches (higher score)
                exact_matches = sum(1 for word in query_words if word in chunk_lower)
                
                # Count partial matches (lower score)
                partial_matches = sum(0.5 for word in query_words 
                                    if any(word in chunk_word for chunk_word in chunk_lower.split()))
                
                score = exact_matches + partial_matches
                
                if score > 0:
                    results.append({
                        'document': doc_name,
                        'chunk_index': i,
                        'chunk_text': chunk,
                        'score': score,
                        'source_file': doc_info.get('source_file', 'unknown')
                    })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:max_results]

# Initialize the RAG system (loads PDFs automatically)
_fsbo_rag = FSBORAG()

@tool
async def search_fsbo_knowledge(
    query: Annotated[str, "Search query for FSBO information, legal requirements, pricing, marketing, etc."]
) -> str:
    """
    Search the FSBO knowledge base for information about selling homes without an agent.
    Covers legal requirements, pricing strategies, marketing tips, and closing processes.
    """
    try:
        results = _fsbo_rag.search(query, max_results=2)
        
        if not results:
            return f"No FSBO information found for: {query}\n\nTry asking about: pricing, legal requirements, marketing, closing process, or Kentucky FSBO steps."
        
        response = f"FSBO Knowledge Search Results for: {query}\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"**Result {i}** (from {result['document']}):\n\n"
            
            # Truncate very long chunks for readability
            chunk_text = result['chunk_text']
            if len(chunk_text) > 500:
                chunk_text = chunk_text[:500] + "..."
            
            response += f"{chunk_text}\n\n"
            response += f"_Source: {Path(result['source_file']).name}_\n\n"
        
        return response.strip()
        
    except Exception as e:
        return f"Error searching FSBO knowledge: {str(e)}"

@tool
async def list_fsbo_documents() -> str:
    """List all FSBO documents currently loaded in the knowledge base."""
    try:
        if not _fsbo_rag.documents:
            return "No FSBO documents loaded. Check that PDF files are in the static/ folder."
        
        response = "Loaded FSBO Documents:\n\n"
        
        for doc_name, info in _fsbo_rag.documents.items():
            response += f"**{doc_name}**\n"
            response += f"  - Chunks: {info['total_chunks']}\n"
            response += f"  - Source: {Path(info['source_file']).name}\n\n"
        
        return response.strip()
        
    except Exception as e:
        return f"Error listing documents: {str(e)}"