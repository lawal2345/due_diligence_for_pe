import os
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

load_dotenv()

# This is the directory where ChromaDB will persist your vectors
CHROMA_DIR = "./chroma_db"

def load_and_chunk_pdfs(file_paths: list[str]) -> list:
    """
    Takes a list of PDF file paths.
    Loads each one, splits into chunks, returns all chunks combined.
    """
    all_chunks = []
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,      # Each chunk is ~1000 characters
        chunk_overlap=200,    # Chunks overlap by 200 chars so context isn't lost at edges
    )
    
    for path in file_paths:
        loader = PyPDFLoader(path)
        pages = loader.load()                        # Returns list of page documents
        chunks = splitter.split_documents(pages)     # Splits pages into smaller chunks
        all_chunks.extend(chunks)
        print(f"Loaded {path}: {len(chunks)} chunks")
    
    return all_chunks


def build_vector_store(chunks: list) -> Chroma:
    """
    Takes chunks, converts them to embeddings, stores in ChromaDB.
    Returns the vector store object so we can query it later.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_DIR
    )
    
    print(f"Vector store built with {len(chunks)} chunks")
    return vector_store


def get_retriever(vector_store: Chroma):
    """
    Returns a retriever — an object that accepts a query string
    and returns the most semantically relevant chunks.
    """
    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 6}   # Return top 6 most relevant chunks per query
    )


def ingest_documents(file_paths: list[str]):
    """
    Master function. Call this with your list of PDFs.
    Returns a retriever ready to answer questions.
    """
    chunks = load_and_chunk_pdfs(file_paths)
    vector_store = build_vector_store(chunks)
    retriever = get_retriever(vector_store)
    return retriever