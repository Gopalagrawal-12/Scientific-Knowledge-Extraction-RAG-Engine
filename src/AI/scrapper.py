import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

async def scrape_published_paper(url: str):
    # Schema to ensure we get the scientific "meat"
    schema = {
        "name": "Research Paper Extractor",
        "baseSelector": "article", # Or the specific journal container
        "fields": [
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "abstract", "selector": ".abstract", "type": "text"},
            {"name": "full_text", "selector": ".content", "type": "text"},
            {"name": "tables", "selector": "table", "type": "html"}
        ]
    }

    async with AsyncWebCrawler(verbose=True) as crawler:
        result = await crawler.arun(
            url=url,
            extraction_strategy=JsonCssExtractionStrategy(schema),
            bypass_cache=True
        )
        return result.extracted_content
from llama_index.core.node_parser import SemanticSplitterNodeParser
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document
# Use the same embedding model as your local DB for consistency
embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
splitter = SemanticSplitterNodeParser(
    buffer_size=1, breakpoint_percentile_threshold=95, embed_model=embed_model
)

def get_chunks_for_graph(text: str):
    doc = Document(text=text)
    nodes = splitter.get_nodes_from_documents([doc])
    return nodes