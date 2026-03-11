import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Document, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter

# Scientific-grade embedding model
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


def initialize_buddy_memory(markdown_text, doc_name, user_id):
    """Saves document linked to a specific user_id."""
    db = chromadb.PersistentClient(path="./buddy_storage")
    chroma_collection = db.get_or_create_collection("research_buddy_docs")

    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Every "Node" of text created from this doc will carry the user_id
    doc = Document(
        text=markdown_text,
        metadata={
            "filename": doc_name,
            "user_id": str(user_id)
        }
    )

    index = VectorStoreIndex.from_documents(
        [doc],
        storage_context=storage_context,
        show_progress=True
    )
    return index


def get_all_stored_filenames(user_id):
    """Returns only the document names belonging to the logged-in user."""
    db = chromadb.PersistentClient(path="./buddy_storage")
    collection = db.get_or_create_collection("research_buddy_docs")

    # Filter the results so User A doesn't see User B's filenames
    results = collection.get(
        where={"user_id": str(user_id)},
        include=['metadatas']
    )

    if results['metadatas']:
        return list(set([m['filename'] for m in results['metadatas']]))
    return []


def get_user_query_engine(user_id):
    """Creates a chat engine that is strictly filtered to one user's data."""
    db = chromadb.PersistentClient(path="./buddy_storage")
    chroma_collection = db.get_or_create_collection("research_buddy_docs")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    # This is the "Security Guard" for your Chatbot
    filters = MetadataFilters(filters=[
        ExactMatchFilter(key="user_id", value=str(user_id))
    ])

    index = VectorStoreIndex.from_vector_store(vector_store)

    # Returns an engine that only 'knows' this user's research
    return index.as_query_engine(filters=filters)


def get_document_text_by_name(user_id: str, filename: str):
    db = chromadb.PersistentClient(path="./buddy_storage")
    collection = db.get_collection("research_buddy_docs")

    # Filter by user and filename
    results = collection.get(
        where={
            "$and": [
                {"user_id": user_id},
                {"filename": filename}
            ]
        },
        include=["documents"]
    )

    # Join all chunks back into one string
    if results["documents"]:
        return "\n".join(results["documents"])
    return None