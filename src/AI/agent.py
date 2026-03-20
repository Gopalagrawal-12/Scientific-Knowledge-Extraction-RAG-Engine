import os
from llama_index.llms.groq import Groq
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
from database import get_qdrant_client  # Imports your Cloud Connection logic
from dotenv import load_dotenv

load_dotenv()

# --- Global Settings ---
# Re-using the same embedding model as database.py for consistency
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


def get_authentic_buddy_agent(user_id: str):
    """
    Creates a Cloud-Synced Chat Agent isolated by user_id.
    Connects to Qdrant Cloud (NOT local Chroma).
    """

    # 1. Setup LLM (Groq Llama 3.1)
    chat_key = os.getenv("CHAT_AGENT_API_KEY")
    if not chat_key:
        raise ValueError("CHAT_AGENT_API_KEY not found in environment variables.")

    Settings.llm = Groq(
        model="llama-3.1-8b-instant",
        api_key=chat_key,
        request_timeout=60.0
    )

    # 2. Connect to Qdrant Cloud
    client = get_qdrant_client()
    collection_name = "research_buddy_docs"

    # 3. Initialize the Vector Store from the Cloud Collection
    vector_store = QdrantVectorStore(
        collection_name=collection_name,
        client=client
    )

    # 4. Create Index View
    # Note: from_vector_store is efficient; it doesn't re-download the data.
    index = VectorStoreIndex.from_vector_store(vector_store)

    # 5. Multi-tenant Isolation (CRITICAL)
    # We use the root 'user_id' key because LlamaIndex hoisted it during indexing.
    filters = MetadataFilters(filters=[
        ExactMatchFilter(key="user_id", value=str(user_id))
    ])

    # 6. Session Memory
    # This keeps the last ~4000 tokens of the current conversation in context.
    memory = ChatMemoryBuffer.from_defaults(token_limit=4000)

    # 7. Build the Chat Engine
    agent = index.as_chat_engine(
        chat_mode="context",
        memory=memory,
        filters=filters,
        system_prompt=(
            f"You are the 'Scientific Research Buddy' for User {user_id}. "
            "You are a Tier-1 Research Assistant. Your knowledge is strictly grounded "
            "in the documents found in the user's Qdrant Cloud library. "
            "\n\nSTRICT RULES:\n"
            "1. Answer based ONLY on the provided context from the research papers.\n"
            "2. If the answer is not in the library, clearly state that the information "
            "is not available in their current research collection.\n"
            "3. Be precise, academic, and professional in your tone."
        )
    )

    return agent