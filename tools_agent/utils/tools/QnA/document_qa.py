# # tools_agent/utils/tools/QnA/document_qa.py

# import os
# import json
# import asyncio
# from typing import List, Dict, Annotated
# from pathlib import Path

# #import PyPDF2
# #import docx

# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.vectorstores import Chroma
# from langchain.embeddings.openai import OpenAIEmbeddings
# # from langchain_core.tools import tool   # <— uncomment to enable
# from langchain.chains import RetrievalQA
# from langchain.chat_models import init_chat_model

# # ──────────────────────────────────────────────────────────────────────────────
# # Global variables for the vector store and metadata
# # ──────────────────────────────────────────────────────────────────────────────
# document_store: Chroma = None
# document_metadata: Dict = {}

# # Paths for static and uploaded documents, and where to save the FAISS index
# STATIC_DOCS_PATH = Path("backend/static/documents")
# UPLOADS_DOCS_PATH = Path("backend/uploads")
# VECTOR_STORE_PATH = Path("backend/vector_store")

# # Ensure these directories exist on startup
# STATIC_DOCS_PATH.mkdir(parents=True, exist_ok=True)
# UPLOADS_DOCS_PATH.mkdir(parents=True, exist_ok=True)
# VECTOR_STORE_PATH.mkdir(parents=True, exist_ok=True)


# # ──────────────────────────────────────────────────────────────────────────────
# # Helper: extract text from file
# # ──────────────────────────────────────────────────────────────────────────────
# def extract_text_from_file(file_path: Path) -> str:
#     """Extract raw text from PDF, DOCX, or TXT. Returns error string if something fails."""
#     ext = file_path.suffix.lower()

#     try:
#         if ext == ".pdf":
#             text_chunks = []
#             with open(file_path, "rb") as f:
#                 reader = PyPDF2.PdfReader(f)
#                 for page in reader.pages:
#                     page_text = page.extract_text() or ""
#                     text_chunks.append(page_text)
#             return "\n".join(text_chunks)

#         elif ext == ".docx":
#             doc = docx.Document(file_path)
#             return "\n".join(p.text for p in doc.paragraphs)

#         elif ext == ".txt":
#             return file_path.read_text(encoding="utf-8")

#         else:
#             return f"Unsupported file format: {ext}"

#     except Exception as e:
#         return f"Error reading file {file_path.name}: {str(e)}"


# # ──────────────────────────────────────────────────────────────────────────────
# # Helper: walk a directory, load all supported docs into a list of dicts
# # ──────────────────────────────────────────────────────────────────────────────
# def load_documents_from_directory(directory: Path, source_type: str) -> List[Dict]:
#     """
#     Load every .pdf, .docx, or .txt from `directory`.
#     Returns a list of dicts: { 'content': <str>, 'metadata': {…} }.
#     """
#     docs: List[Dict] = []
#     if not directory.exists():
#         return docs

#     for file_path in directory.iterdir():
#         if (
#             file_path.is_file()
#             and file_path.suffix.lower() in [".pdf", ".docx", ".txt"]
#         ):
#             raw = extract_text_from_file(file_path)
#             if raw.startswith("Error") or raw.startswith("Unsupported"):
#                 continue

#             docs.append({
#                 "content": raw,
#                 "metadata": {
#                     "source": str(file_path),
#                     "filename": file_path.name,
#                     "source_type": source_type,
#                     "file_size": file_path.stat().st_size,
#                 }
#             })

#     return docs


# # ──────────────────────────────────────────────────────────────────────────────
# # Initialize (or rebuild) the FAISS-based document store
# # ──────────────────────────────────────────────────────────────────────────────
# async def initialize_document_store() -> bool:
#     """
#     Read all static & uploaded docs, chunk them, embed them, and write to disk.
#     Returns True on success, False on error.
#     """
#     global document_store, document_metadata

#     try:
#         # 1) load raw docs
#         static_docs = load_documents_from_directory(STATIC_DOCS_PATH, "static")
#         uploaded_docs = load_documents_from_directory(UPLOADS_DOCS_PATH, "uploaded")
#         all_docs = static_docs + uploaded_docs

#         if not all_docs:
#             print("No documents found to index.")
#             return False

#         # 2) chunk each document’s content
#         splitter = RecursiveCharacterTextSplitter(
#             chunk_size=1000,
#             chunk_overlap=200,
#             length_function=len,
#         )

#         texts: List[str] = []
#         metadatas: List[Dict] = []

#         for doc in all_docs:
#             chunks = splitter.split_text(doc["content"])
#             for idx, txt_chunk in enumerate(chunks):
#                 texts.append(txt_chunk)
#                 md = doc["metadata"].copy()
#                 md["chunk_id"] = idx
#                 metadatas.append(md)

#         # 3) create embeddings + FAISS store
#         embeddings = OpenAIEmbeddings()
#         document_store = FAISS.from_texts(texts, embeddings, metadatas=metadatas)

#         # 4) collect & save metadata
#         document_metadata = {
#             "total_documents": len(all_docs),
#             "static_documents": len(static_docs),
#             "uploaded_documents": len(uploaded_docs),
#             "total_chunks": len(texts),
#             "files": [doc["metadata"]["filename"] for doc in all_docs],
#         }

#         document_store.save_local(str(VECTOR_STORE_PATH))
#         (VECTOR_STORE_PATH / "metadata.json").write_text(
#             json.dumps(document_metadata, indent=2), encoding="utf-8"
#         )

#         print(f"Document store initialized: {len(all_docs)} files, {len(texts)} chunks.")
#         return True

#     except Exception as e:
#         print(f"Error initializing document store: {str(e)}")
#         return False


# # ──────────────────────────────────────────────────────────────────────────────
# # Helper: try reloading an existing FAISS index from disk
# # ──────────────────────────────────────────────────────────────────────────────
# def load_existing_document_store() -> bool:
#     """If a FAISS index already exists on disk, load it into memory."""
#     global document_store, document_metadata

#     try:
#         # Check for index presence (FAISS by default writes "index.faiss" under the folder)
#         index_file = VECTOR_STORE_PATH / "index.faiss"
#         if index_file.exists():
#             embeddings = OpenAIEmbeddings()
#             document_store = FAISS.load_local(
#                 str(VECTOR_STORE_PATH),
#                 embeddings,
#                 allow_dangerous_deserialization=True,
#             )

#             metadata_file = VECTOR_STORE_PATH / "metadata.json"
#             if metadata_file.exists():
#                 document_metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

#             return True

#     except Exception as e:
#         print(f"Error loading existing document store: {str(e)}")

#     return False


# # ──────────────────────────────────────────────────────────────────────────────
# # Tool: query_documents
# # ──────────────────────────────────────────────────────────────────────────────
# # @tool(
# #     name="query_documents",
# #     description="Query and ask questions about uploaded and static documents in the knowledge base."
# # )
# async def query_documents(
#     question: Annotated[str, "The question to ask about the documents"],
#     document_type: Annotated[str, "Type of documents to search: 'all', 'static', or 'uploaded'"] = "all",
#     max_results: Annotated[int, "Maximum number of relevant document chunks to return"] = 5
# ) -> str:
#     """
#     1) Ensure the FAISS store is loaded (or build it if missing).
#     2) Run a similarity search for `question`.
#     3) Return the LLM’s answer + a list of source filenames.
#     """
#     global document_store, document_metadata

#     try:
#         # 1) Make sure we have an in-memory store
#         if document_store is None:
#             if not load_existing_document_store():
#                 await initialize_document_store()

#         if document_store is None:
#             return "❌ No documents are currently available. Upload files and try again."

#         # 2) Build a retriever, with an optional filter on source_type
#         filter_kwargs = None
#         if document_type in ("static", "uploaded"):
#             filter_kwargs = {"source_type": document_type}

#         retriever = document_store.as_retriever(
#             search_kwargs={"k": max_results, "filter": filter_kwargs}
#         )

#         # 3) Initialize the chat model and RetrievalQA chain
#         model = init_chat_model("openai:gpt-4o-mini", temperature=0.3)
#         qa_chain = RetrievalQA.from_chain_type(
#             llm=model,
#             chain_type="stuff",
#             retriever=retriever,
#             return_source_documents=True
#         )

#         # 4) Run the chain
#         result = qa_chain({"query": question})
#         answer = result["result"]
#         sources = result["source_documents"]

#         # 5) Format the response
#         response = f"📄 **Answer based on your documents:**\n\n{answer}\n\n"
#         if sources:
#             response += "**📚 Sources:**\n"
#             seen = set()
#             for doc_chunk in sources:
#                 fname = doc_chunk.metadata.get("filename", "Unknown")
#                 stype = doc_chunk.metadata.get("source_type", "unknown")
#                 if fname not in seen:
#                     response += f"• {fname} ({stype})\n"
#                     seen.add(fname)

#         # 6) Append high-level metadata if available
#         if document_metadata:
#             response += "\n**📊 Knowledge Base Info:**\n"
#             response += f"• Total documents: {document_metadata.get('total_documents', 0)}\n"
#             response += f"• Static documents: {document_metadata.get('static_documents', 0)}\n"
#             response += f"• Uploaded documents: {document_metadata.get('uploaded_documents', 0)}\n"

#         return response

#     except Exception as e:
#         return f"❌ Error querying documents: {str(e)}"


# # ──────────────────────────────────────────────────────────────────────────────
# # Tool: list_available_documents
# # ──────────────────────────────────────────────────────────────────────────────
# # @tool(
# #     name="list_available_documents",
# #     description="List all documents currently available in the knowledge base."
# # )
# async def list_available_documents() -> str:
#     """
#     Returns a formatted string listing every PDF, DOCX, and TXT in both
#     the `static` and `uploads` folders, plus a summary.
#     """
#     global document_metadata

#     try:
#         # Ensure the store is at least "known" (so document_metadata is populated)
#         if document_store is None:
#             if not load_existing_document_store():
#                 await initialize_document_store()

#         # Gather file lists
#         static_files = []
#         uploaded_files = []
#         if STATIC_DOCS_PATH.exists():
#             static_files = [
#                 f.name
#                 for f in STATIC_DOCS_PATH.iterdir()
#                 if f.is_file() and f.suffix.lower() in [".pdf", ".docx", ".txt"]
#             ]
#         if UPLOADS_DOCS_PATH.exists():
#             uploaded_files = [
#                 f.name
#                 for f in UPLOADS_DOCS_PATH.iterdir()
#                 if f.is_file() and f.suffix.lower() in [".pdf", ".docx", ".txt"]
#             ]

#         # Build the response
#         if not (static_files or uploaded_files):
#             return "📄 No documents are currently available in the knowledge base."

#         response = "📚 **Available Documents in Knowledge Base:**\n\n"

#         if static_files:
#             response += "**📁 Static Documents (Pre-loaded):**\n"
#             for fn in static_files:
#                 response += f"• {fn}\n"
#             response += "\n"

#         if uploaded_files:
#             response += "**📤 Uploaded Documents:**\n"
#             for fn in uploaded_files:
#                 response += f"• {fn}\n"
#             response += "\n"

#         # Summary
#         total = len(static_files) + len(uploaded_files)
#         response += "**📊 Summary:**\n"
#         response += f"• Total documents: {total}\n"
#         response += f"• Static documents: {len(static_files)}\n"
#         response += f"• Uploaded documents: {len(uploaded_files)}\n"

#         return response

#     except Exception as e:
#         return f"❌ Error listing documents: {str(e)}"


# # ──────────────────────────────────────────────────────────────────────────────
# # Tool: refresh_document_index
# # ──────────────────────────────────────────────────────────────────────────────
# # @tool(
# #     name="refresh_document_index",
# #     description="Refresh the document index to include newly uploaded files."
# # )
# async def refresh_document_index() -> str:
#     """
#     Rebuilds the FAISS index from scratch, so any newly uploaded docs
#     become searchable immediately.
#     """
#     try:
#         success = await initialize_document_store()
#         if success:
#             return "✅ Document index refreshed successfully! All uploaded documents are now searchable."
#         else:
#             return "❌ Failed to refresh document index. Please verify that documents exist."
#     except Exception as e:
#         return f"❌ Error refreshing document index: {str(e)}"


# # ──────────────────────────────────────────────────────────────────────────────
# # On module import: asynchronously build or load the store
# # ──────────────────────────────────────────────────────────────────────────────
# async def __init_document_store_on_import():
#     # If no existing FAISS index, build now in the background
#     if not load_existing_document_store():
#         await initialize_document_store()


# # If the event loop is running, schedule the init; otherwise run it directly
# try:
#     loop = asyncio.get_event_loop()
#     if loop.is_running():
#         asyncio.create_task(__init_document_store_on_import())
#     else:
#         asyncio.run(__init_document_store_on_import())
# except Exception as e:
#     print(f"Note: Document Q&A will initialize on first use. {str(e)}")
