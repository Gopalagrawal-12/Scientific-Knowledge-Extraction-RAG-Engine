import os
import json
import asyncio
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pydantic import BaseModel
from pathlib import Path

# --- Logical Imports from your project files ---
from research import extract_scientific_pdf, save_analysis_to_json
from database import initialize_buddy_memory, get_all_stored_filenames
from brain import generate_buddy_dashboard
from agent import get_authentic_buddy_agent
from test_comparison import brutal_comparison_pipeline

app = FastAPI(title="Scientific Research Buddy API")
RESULTS_DIR = Path("analysis_results")


# Request Model for Chat
class ChatRequest(BaseModel):
    user_id: str
    message: str


# --- 1. API: Process Research ---
@app.post("/process-research")
async def process_research(user_id: str = Form(...), file: UploadFile = File(...)):
    """
    Parses PDF, saves to ChromaDB, and generates the initial Audit Dashboard.
    """
    temp_path = Path(f"temp_{file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())

        # 1. Extraction
        markdown_text = extract_scientific_pdf(str(temp_path))
        # 2. Database Sync
        initialize_buddy_memory(markdown_text, file.filename, user_id)
        # 3. Scientific Audit
        previous_docs = get_all_stored_filenames(user_id)
        analysis_json = generate_buddy_dashboard(markdown_text, previous_docs, user_id)
        analysis_data = json.loads(analysis_json)

        save_analysis_to_json(analysis_data, file.filename,user_id)  #
        return {"status": "success", "analysis": analysis_data}
    finally:
        if temp_path.exists(): os.remove(temp_path)


# --- 2. API: Compare ---
@app.post("/compare")
async def compare(
        user_id: str = Form(...),
        benchmark_url: str = Form(...),
        file: UploadFile = File(...)
):
    """
    Takes ID, PDF, and Link. Returns the Brutal Comparison JSON.
    """
    temp_path = Path(f"compare_temp_{file.filename}")
    try:
        with open(temp_path, "wb") as buffer:
            buffer.write(await file.read())

        # Parse and pass text directly to comparison pipeline
        markdown_text = extract_scientific_pdf(str(temp_path))
        comparison_report = await brutal_comparison_pipeline(
            markdown_text=markdown_text,
            published_url=benchmark_url,
            filename=file.filename
        )
        return {"status": "success", "comparison_data": comparison_report}
    finally:
        if temp_path.exists(): os.remove(temp_path)


# main.py updates

@app.get("/get-all/{user_id}")
async def get_all(user_id: str):
    """Retrieves saved JSON results ONLY from the user's private folder."""
    # Segregate physical files on disk
    user_dir = RESULTS_DIR / str(user_id)

    if not user_dir.exists():
        return {"user_id": user_id, "reports": []}

    reports = []
    for json_file in user_dir.glob("*.json"):
        with open(json_file, "r", encoding="utf-8") as f:
            reports.append({
                "filename": json_file.name,
                "data": json.load(f)
            })
    return {"user_id": user_id, "reports": reports}


@app.post("/chat")
async def chat(request: ChatRequest):
    """Uses the filtered agent to ensure zero data leakage."""
    try:
        # This agent already has MetadataFilters applied in agent.py
        buddy = get_authentic_buddy_agent(request.user_id)
        response = buddy.chat(request.message)
        return {"response": str(response)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# main.py update
from zotero_connector import ZoteroSideSector


@app.get("/zotero/sidebar/{user_id}")
async def get_zotero_sidebar(user_id: str, lib_id: str, api_key: str):
    """
    Returns organized Zotero data for the frontend Side Sector.
    """
    # This remains separate from the RAG logic to avoid data clustering
    connector = ZoteroSideSector(lib_id, api_key)
    data = connector.get_organized_library()

    if "error" in data:
        raise HTTPException(status_code=400, detail=data["error"])

    return {
        "user_id": user_id,
        "sidebar_data": data
    }

# --- STABLE STARTUP ---
if __name__ == "__main__":
    import uvicorn

    config = uvicorn.Config(app, host="0.0.0.0", port=8000, loop="asyncio")
    server = uvicorn.Server(config)
    asyncio.run(server.serve())