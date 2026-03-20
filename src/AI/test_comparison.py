import os
import json
import asyncio
from llama_index.llms.groq import Groq
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from dotenv import load_dotenv

load_dotenv()

# We only need the LLM for direct comparison, no heavy Embedding model required
llm = Groq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("Crawl_CHAT_AGENT_API_KEY"),
    request_timeout=120.0
)


async def brutal_comparison_pipeline(markdown_text: str, published_url: str, filename: str = "Unknown_File"):
    if not markdown_text:
        return {"error": "No markdown text provided for comparison."}

    try:
        # 1. Scrape Published Paper with Browser Config for low-RAM environments (Render)
        browser_config = BrowserConfig(headless=True, verbose=False)
        run_config = CrawlerRunConfig(cache_mode="BYPASS")

        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=published_url, config=run_config)
            # Take a healthy chunk of the scraped content
            scraped_text = result.markdown[:8000]

            # 2. Direct Comparison (In-Context RAG)
        # Instead of building an index, we place both documents into a structured prompt
        # This is much faster and uses almost 0 extra RAM.
        comparison_prompt = f"""
        SYSTEM ROLE: Tier-1 Scientific Peer Reviewer.

        DOCUMENT 1: USER RESEARCH ({filename})
        ---
        {markdown_text[:8000]}
        ---

        DOCUMENT 2: PUBLISHED REFERENCE (from {published_url})
        ---
        {scraped_text}
        ---

        INSTRUCTION: 
        Compare Document 1 against Document 2. 
        Analyze gaps in statistics, methodology differences, and overall publication readiness.

        Return ONLY a JSON object:
        {{
            "readiness_score": (int 1-100),
            "statistical_gaps": ["list"],
            "methodology_comparison": "string",
            "verdict": "Accept/Reject/Revision",
            "critical_flaws": ["list"]
        }}
        """

        # 3. Direct Async Completion
        response = await llm.acomplete(comparison_prompt)
        raw_text = str(response)

        # 4. Robust JSON Parsing
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