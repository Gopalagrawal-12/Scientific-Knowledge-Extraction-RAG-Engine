import asyncio
import json
import os
from dotenv import load_dotenv

# Import your actual project logic
from database import get_document_text_by_name
from test_comparison import brutal_comparison_pipeline

load_dotenv()


async def run_local_test():
    print("🚀 --- Scientific Research Buddy: Local Comparison Tester ---")

    # 1. --- CONFIGURATION ---
    USER_ID = "2"
    LOCAL_FILENAME = "Pusa-Golden-Cherry-tomato-2-New-promising-yellow-cherry-tomato-for-protected-cultivation.pdf"
    EXTERNAL_URL = "https://en.wikipedia.org/wiki/Digital_learning"

    # 2. --- STEP 1: QDRANT RETRIEVAL ---
    print(f"\n🔍 Searching Qdrant Cloud for: '{LOCAL_FILENAME}' (User: {USER_ID})...")

    try:
        local_text = get_document_text_by_name(USER_ID, LOCAL_FILENAME)

        if not local_text or len(local_text.strip()) == 0:
            print("⚠️ Cloud Retrieval Failed. Using Fallback.")
            local_text = "Sample tomato research content for testing."
        else:
            print(f"✅ Cloud Success: Retrieved {len(local_text)} characters.")

    except Exception as e:
        print(f"❌ Database Error: {e}")
        return

    print(f"\n📡 Scraping & Comparing against: {EXTERNAL_URL}")
    print("⏳ This may take 20-40 seconds (Crawl4AI + LLM Processing)...")

    try:
        # THE FIX: Match the function's (Text, URL) order
        # Arg 1 must be the markdown text, Arg 2 must be the URL
        comparison_result = await brutal_comparison_pipeline(
            markdown_text=local_text,
            published_url=EXTERNAL_URL,
            filename=LOCAL_FILENAME
        )

        print("\n" + "=" * 50)
        print("📊 FINAL COMPARISON REPORT")
        print("=" * 50)
        print(json.dumps(comparison_result, indent=2))
        print("=" * 50)

    except Exception as e:
        print(f"❌ Pipeline Failure: {e}")

if __name__ == "__main__":
    asyncio.run(run_local_test())