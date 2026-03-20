import asyncio
import json
import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from database import initialize_buddy_memory, get_all_stored_filenames
from brain import generate_buddy_dashboard

def save_analysis_to_json(analysis, filename, user_id):
    """Logic Unchanged: Saves the audit report to your local laptop folder."""
    output_dir = Path("analysis_results") / str(user_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    if hasattr(analysis, "model_dump"):
        data = analysis.model_dump()
    else:
        data = analysis

    json_path = output_dir / f"{Path(filename).stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"📂 Local Backup saved to: {json_path}")
    return data

def extract_scientific_pdf(file_path: str):
    """Logic Unchanged: Uses Docling for high-fidelity Markdown extraction."""
    converter = DocumentConverter()
    print(f"--- 🧬 Buddy is parsing: {Path(file_path).name} ---")
    result = converter.convert(file_path)
    return result.document.export_to_markdown()

async def main():
    """Local test script: Updated to sync JSON reports to Qdrant Cloud Payloads."""
    test_pdf = "S2059866125000068a.pdf"
    current_user = "123"

    if not Path(test_pdf).exists():
        print(f"Error: {test_pdf} not found.")
        return

    # 1. Check Library Context (Logic Unchanged)
    previous_docs = get_all_stored_filenames(current_user)
    print(f"Checking context: Found {len(previous_docs)} previous documents.")

    # 2. Extract (Logic Unchanged)
    markdown_text = extract_scientific_pdf(test_pdf)

    # 3. Scientific Deep Analysis (MOVED UP)
    # We audit BEFORE storing so the report can be included in the vector metadata
    analysis_json = generate_buddy_dashboard(markdown_text, previous_docs, current_user)
    analysis_data = json.loads(analysis_json)

    # 4. Store and Link (SWITCHED TO CLOUD PAYLOAD)
    # This now pushes Text + Vector + JSON Audit to Qdrant Cloud
    initialize_buddy_memory(markdown_text, test_pdf, current_user, analysis_data)

    # 5. Local Backup (Logic Unchanged)
    save_analysis_to_json(analysis_data, test_pdf, current_user)

    print("\n✅ Cloud Sync Complete. Your research is now permanent in Qdrant.")

if __name__ == "__main__":
    asyncio.run(main())