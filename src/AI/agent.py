import os
import chromadb
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.groq import Groq  # <--- Add this import
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter


def get_authentic_buddy_agent(user_id: str):
    load_dotenv()
    chat_key = os.getenv("CHAT_AGENT_API_KEY")
    Settings.llm = Groq(model="llama-3.1-8b-instant", api_key=chat_key)

    db = chromadb.PersistentClient(path="./buddy_storage")
    chroma_collection = db.get_or_create_collection("research_buddy_docs")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

    index = VectorStoreIndex.from_vector_store(vector_store)

    filters = MetadataFilters(filters=[
        ExactMatchFilter(key="user_id", value=str(user_id))
    ])

    memory = ChatMemoryBuffer.from_defaults(token_limit=4000)

    agent = index.as_chat_engine(
        chat_mode="context",
        memory=memory,
        filters=filters,
        system_prompt=(
            f"You are the 'Scientific Research Buddy' for User {user_id}. "
        "You ONLY have authority to answer questions based on the uploaded research papers in the user's library. "
        "\n\nSTRICT RULES:\n"
        "1. If a user asks a general knowledge question, a personal question, or anything NOT "
        "found in their uploaded documents, you must respond EXACTLY with: "
        "If not found you should answer the question. if it is knowledge related"
        )
    )
    return agent