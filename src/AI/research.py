import asyncio
import json
import os
from pathlib import Path
from docling.document_converter import DocumentConverter
from database import initialize_buddy_memory, get_all_stored_filenames
from brain import generate_buddy_dashboard


def save_analysis_to_json(analysis, filename, user_id):
    """Saves the audit report into a private, user-specific directory."""
    # 1. Create a user-specific results directory
    output_dir = Path("analysis_results") / str(user_id)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Check if analysis is already a dict or a Pydantic model
    if hasattr(analysis, "model_dump"):
        data = analysis.model_dump()
    else:
        data = analysis

        # 3. Save as JSON inside the user's folder
    json_path = output_dir / f"{Path(filename).stem}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"📂 Scientific Data saved to: {json_path}")
    return json_path


def extract_scientific_pdf(file_path: str):
    """Uses Docling to convert PDF into clean Markdown for analysis."""
    converter = DocumentConverter()
    print(f"--- 🧬 Buddy is parsing: {Path(file_path).name} ---")
    result = converter.convert(file_path)
    return result.document.export_to_markdown()


async def main():
    """Local test script to simulate the full segregated pipeline."""
    # Update this with the file you want to analyze
    test_pdf = "S2059866125000068a.pdf"
    current_user = "123"  # Using string ID for consistency with Django

    if not Path(test_pdf).exists():
        print(f"Error: {test_pdf} not found. Please ensure it is in the current folder.")
        return

    # 1. Check Library Context (Filtered by user_id)
    previous_docs = get_all_stored_filenames(current_user)
    print(f"Checking context: Found {len(previous_docs)} previous documents in library.")

    # 2. Extract (Docling)
    markdown_text = extract_scientific_pdf(test_pdf)

    # 3. Store and Link (ChromaDB with user_id metadata)
    initialize_buddy_memory(markdown_text, test_pdf, current_user)

    # 4. Scientific Deep Analysis (Using user-aware brain logic)
    analysis_json = generate_buddy_dashboard(markdown_text, previous_docs, current_user)

    # 5. Save results to user-segregated folder
    analysis_data = json.loads(analysis_json)
    # FIX: Correctly passing current_user to save_analysis_to_json
    save_analysis_to_json(analysis_data, test_pdf, current_user)

    print("\n✅ Audit Complete. Dashboard ready for web integration.")


if __name__ == "__main__":
    # Ensure this runs only locally, not when imported by FastAPI
    asyncio.run(main())