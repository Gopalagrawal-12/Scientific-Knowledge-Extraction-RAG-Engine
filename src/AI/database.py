import os
from qdrant_client import QdrantClient, models
from llama_index.core import VectorStoreIndex, StorageContext, Document, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

load_dotenv()

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

def get_qdrant_client():
    """Initializes the secure connection to Qdrant Cloud."""
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    return QdrantClient(url=url, api_key=api_key, prefer_grpc=False, timeout=120)

def initialize_buddy_memory(markdown_text, doc_name, user_id, analysis_result=None):
    """Saves document text AND the LLM Audit Report to Qdrant Cloud."""
    client = get_qdrant_client()
    collection_name = "research_buddy_docs"

    if not client.collection_exists(collection_name):
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
        )

    vector_store = QdrantVectorStore(collection_name=collection_name, client=client)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Creating the Document with Flat Metadata
    doc = Document(
        text=markdown_text,
        metadata={
            "filename": doc_name,
            "user_id": str(user_id),
            "audit_report": analysis_result
        },
        excluded_embed_metadata_keys=["audit_report", "user_id"] # Don't waste vector space on IDs/JSON
    )

    index = VectorStoreIndex.from_documents([doc], storage_context=storage_context)
    return index

def get_all_stored_reports(user_id):
    """Fetches all Audit JSONs for a specific user from Qdrant Payloads."""
    client = get_qdrant_client()
    results, _ = client.scroll(
        collection_name="research_buddy_docs",
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user_id)))]
        ),
        with_payload=True,
        with_vectors=False
    )

    reports = []
    seen_files = set()
    if results:
        for point in results:
            payload = point.payload
            fname = payload.get("filename")
            report = payload.get("audit_report")
            if fname and fname not in seen_files and report:
                reports.append({"filename": fname, "data": report})
                seen_files.add(fname)
    return reports

def get_all_stored_filenames(user_id):
    """Returns a simple list of filenames the user has uploaded."""
    client = get_qdrant_client()
    results, _ = client.scroll(
        collection_name="research_buddy_docs",
        scroll_filter=models.Filter(
            must=[models.FieldCondition(key="user_id", match=models.MatchValue(value=str(user_id)))]
        ),
        with_payload=True
    )
    if results:
        return list(set([p.payload.get("filename") for p in results if "filename" in p.payload]))
    return []


def get_document_text_by_name(user_id: str, filename: str):
    """
    Bulletproof retrieval: Handles flat/nested metadata and
    extracts text from raw keys or LlamaIndex node JSON.
    """
    client = get_qdrant_client()
    col = "research_buddy_docs"

    u_id = str(user_id).strip()
    f_name = str(filename).strip()

    # 1. Try EVERY possible path (Flat and Nested)
    possible_filters = [
        models.Filter(must=[
            models.FieldCondition(key="user_id", match=models.MatchValue(value=u_id)),
            models.FieldCondition(key="filename", match=models.MatchValue(value=f_name))
        ]),
        models.Filter(must=[
            models.FieldCondition(key="metadata.user_id", match=models.MatchValue(value=u_id)),
            models.FieldCondition(key="metadata.filename", match=models.MatchValue(value=f_name))
        ])
    ]

    for f in possible_filters:
        # 'limit=1000' ensures we get all chunks of a large PDF
        results, _ = client.scroll(
            collection_name=col,
            scroll_filter=f,
            with_payload=True,
            limit=1000
        )

        if results:
            full_text = []
            for p in results:
                payload = p.payload
                # Strategy A: Direct 'text' key
                content = payload.get("text")

                # Strategy B: LlamaIndex internal JSON structure
                if not content and "_node_content" in payload:
                    import json
                    try:
                        node_data = json.loads(payload["_node_content"])
                        content = node_data.get("text")
                    except:
                        pass

                if content:
                    full_text.append(content)

            final_string = "\n".join(full_text)
            if final_string.strip():
                return final_string

    print(f"❌ No text could be extracted for {f_name}")
    return None