import os
import json
import asyncio
from llama_index.core import Document, VectorStoreIndex, Settings
from llama_index.llms.groq import Groq
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from crawl4ai import AsyncWebCrawler
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Global Settings
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
Settings.llm = Groq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("Crawl_CHAT_AGENT_API_KEY"),
    request_timeout=120.0
)


async def brutal_comparison_pipeline(markdown_text: str, published_url: str, filename: str = "Unknown_File"):
    """
    Executes a stable Semantic Comparison between provided text and a live URL.
    Returns a structured JSON object.
    """
    if not markdown_text:
        return {"error": "No markdown text provided for comparison."}

    try:
        # 1. Scrape Published Paper
        async with AsyncWebCrawler() as crawler:
            result = await crawler.arun(url=published_url)
            scraped_text = result.markdown[:6000]  # Increased limit for better context

        # 2. Build a standard Vector Index (Much more stable than Graph)
        docs = [
            Document(text=markdown_text, metadata={"source": "YOUR_RESEARCH", "filename": filename}),
            Document(text=scraped_text, metadata={"source": "PUBLISHED_PAPER", "url": published_url})
        ]

        # In-memory index creation
        index = VectorStoreIndex.from_documents(docs)
        query_engine = index.as_query_engine(similarity_top_k=5)

        # 3. Request Structured JSON
        brutal_query = f"""
        Compare the provided research ({filename}) against the 'PUBLISHED_PAPER'.
        Analyze strictly. Return ONLY a JSON object:
        {{
            "readiness_score": (int 1-100),
            "statistical_gaps": ["gap1", "gap2"],
            "methodology_comparison": "detailed string",
            "verdict": "Accept/Reject/Revision",
            "critical_flaws": ["flaw1", "flaw2"]
        }}
        """

        # Using aquery for async compatibility
        response = await query_engine.aquery(brutal_query)

        raw_text = str(response)

        # Clean JSON markdown if necessary
        if "```json" in raw_text:
            raw_text = raw_text.split("```json")[1].split("```")[0].strip()
        elif "```" in raw_text:
            raw_text = raw_text.split("```")[1].split("```")[0].strip()

        return json.loads(raw_text)

    except Exception as e:
        return {
            "error": "Comparison Failed",
            "details": str(e)
        }