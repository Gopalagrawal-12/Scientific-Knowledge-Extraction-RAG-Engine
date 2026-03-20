import os
import json
import asyncio
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path
from dotenv import load_dotenv
from contextlib import asynccontextmanager

# --- Logical Imports ---
from research import extract_scientific_pdf, save_analysis_to_json
from database import (
    initialize_buddy_memory,
    get_all_stored_filenames,
    get_qdrant_client,
    get_all_stored_reports,
    get_document_text_by_name
)
from brain import generate_buddy_dashboard
from agent import get_authentic_buddy_agent
from test_comparison import brutal_comparison_pipeline
from zotero_connector import ZoteroSideSector

load_dotenv()


# --- 0. Setup & Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Pre-configures Qdrant Cloud indexes for high-speed multi-tenancy."""
    try:
        client = get_qdrant_client()
        col = "research_buddy_docs"
        if not client.collection_exists(col):
            from qdrant_client.http import models
            client.create_collection(
                col,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )

        # KEY FIX: Indexing root-level and nested keys to prevent 400 Bad Request errors
        from qdrant_client.http import models
        client.create_payload_index(col, "filename", "keyword")
        client.create_payload_index(col, "user_id", "keyword")
        client.create_payload_index(col, "metadata.filename", "keyword")
        client.create_payload_index(col, "metadata.user_id", "keyword")

        print("✅ Qdrant Cloud: Verified user_id and filename indexes.")
    except Exception as e:
        print(f"⚠️ Startup Warning: {e}")
    yield


app = FastAPI(title="Scientific Research Buddy API", lifespan=lifespan)


class ChatRequest(BaseModel):
    user_id: str
    message: str


class CompareRequest(BaseModel):
    user_id: str
    paper_url: str
    local_filename: str


# --- 1. API: Process Research (Upload & Audit) ---
@app.post("/process-research")
async def process_research(user_id: str = Form(...), file: UploadFile = File(...)):
    temp_path = Path(f"temp_{user_id}_{file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Extract PDF
        markdown_text = await asyncio.to_thread(extract_scientific_pdf, str(temp_path))

        # Generate Scientific Audit
        previous_docs = await asyncio.to_thread(get_all_stored_filenames, user_id)
        analysis_raw = await asyncio.to_thread(generate_buddy_dashboard, markdown_text, previous_docs, user_id)
        analysis_data = json.loads(analysis_raw)

        # Save to Cloud
        await asyncio.to_thread(initialize_buddy_memory, markdown_text, file.filename, user_id, analysis_data)

        return {"status": "success", "analysis": analysis_data}
    except Exception as e:
        print(f"❌ Processing Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if temp_path.exists():
            os.remove(temp_path)


# --- 2. API: Library Dashboard ---
@app.get("/get-all/{user_id}")
async def get_all(user_id: str):
    reports = await asyncio.to_thread(get_all_stored_reports, user_id)
    return {"user_id": user_id, "reports": reports}


# --- 3. API: RAG Chat Agent ---
@app.post("/chat")
async def chat(request: ChatRequest):
    try:
        buddy = get_authentic_buddy_agent(request.user_id)
        # Using to_thread because llama-index's .chat is often synchronous
        response = await asyncio.to_thread(buddy.chat, request.message)
        return {"response": str(response)}
    except Exception as e:
        print(f"❌ Chat Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- 4. API: Brutal Comparison (The fix for the Coroutine Error) ---
@app.post("/compare")
async def compare_research(request: CompareRequest):
    print(f"DEBUG: Comparing for User [{request.user_id}] File [{request.local_filename}]")
    try:
        # 1. Fetch text from Cloud (Running in thread to keep API responsive)
        local_text = await asyncio.to_thread(
            get_document_text_by_name,
            request.user_id,
            request.local_filename
        )

        if not local_text:
            raise HTTPException(status_code=404, detail="Document not found in cloud.")

        # 2. Run Comparison
        # Since brutal_comparison_pipeline is an 'async def', we AWAIT it directly.
        # This prevents the "coroutine object is not iterable" error.
        comparison_result = await brutal_comparison_pipeline(
            markdown_text=local_text,
            published_url=request.paper_url,
            filename=request.local_filename
        )

        # 3. Return as a standard dictionary
        return {"status": "success", "comparison": comparison_result}

    except Exception as e:
        print(f"❌ Comparison Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# --- 5. API: Zotero Sidebar Sync ---
@app.get("/zotero/sidebar/{user_id}")
async def zotero_sidebar(user_id: str, lib_id: str, api_key: str):
    connector = ZoteroSideSector(lib_id, api_key)
    data = await asyncio.to_thread(connector.get_organized_library)
    return {"user_id": user_id, "sidebar_data": data}


if __name__ == "__main__":
    import uvicorn

    # Use environment PORT for Render/Production
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)