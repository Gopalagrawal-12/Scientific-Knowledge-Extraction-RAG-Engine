# Scientific Knowledge Extraction & RAG Engine

## Overview
The **Scientific Knowledge Extraction & RAG Engine** is an advanced retrieval-augmented generation (RAG) system engineered to automate the ingestion, processing, and querying of dense academic literature and scientific dossiers. It leverages a dual-layered, hybrid retrieval strategy that combines vector-based semantic search with Knowledge Graph traversal, enabling the resolution of complex, multi-hop queries with absolute, source-grounded accuracy.

## Key Features
*   **Hierarchical Document Parsing:** Utilizes `Docling` to automate the ingestion and structural chunking of complex PDFs and academic papers, preserving context and structural integrity.
*   **Hybrid Retrieval Pipeline:** Integrates vector-based similarity search via `ChromaDB` with `Knowledge Graph` structures to capture both semantic meaning and relational facts.
*   **Multi-hop Query Resolution:** Designed to answer highly complex questions that require synthesizing information from multiple, distinct nodes within a document corpus.
*   **Academic-Grade Citation:** Integrates `Zorito` to ensure 100% source-grounded outputs, providing verifiable academic citations for all generated responses.
*   **Modular API Architecture:** Built on `Django` to provide a robust API for document upload, graph ingestion, and query processing.

## Technologies Used
*   **Core Backend:** Python, Django
*   **Vector Database:** ChromaDB
*   **Knowledge Representation:** Knowledge Graphs
*   **Document Processing:** Docling
*   **AI & Orchestration:** LLM Orchestration frameworks (LangChain)
*   **Citation & Grounding:** Zorito

## System Architecture

1.  **Ingestion & Parsing:** Unstructured academic documents are ingested via the Django API. `Docling` parses the documents, extracting text while maintaining structural hierarchy (headers, paragraphs, figures).
2.  **Chunking & Embedding:** The parsed text is intelligently chunked. Vector embeddings are generated for semantic context, while structured data is extracted to build relationships.
3.  **Storage:** 
    *   Semantic embeddings are stored in `ChromaDB`.
    *   Relational entities are stored in a `Knowledge Graph`.
4.  **Retrieval (Hybrid Strategy):** When a user submits a query, the system simultaneously queries both ChromaDB (for semantic similarity) and the Knowledge Graph (for factual relationships).
5.  **Generation & Grounding:** An orchestrating LLM synthesizes the retrieved contexts, while `Zorito` ensures the final response is strictly grounded in the source material and properly cited.

## Setup & Installation

### Prerequisites
*   Python 3.10+
*   Virtual Environment (recommended)

### Installation Steps

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Gopalagrawal-12/scientific-rag-engine.git
    cd scientific-rag-engine
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    *(Assuming a `requirements.txt` is present)*
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the root directory and configure necessary API keys (e.g., LLM provider keys, database credentials).

5.  **Run Database Migrations (Django):**
    ```bash
    python manage.py migrate
    ```

6.  **Start the Development Server:**
    ```bash
    python manage.py runserver
    ```

## Usage

*   **API Endpoints:** Detailed documentation for the API endpoints (e.g., `/api/upload`, `/api/query`) can be found in the API documentation (Swagger/Redoc if implemented, or code comments).
*   **Local Testing:** Ensure your local instances of any required vector databases or graph databases are running before executing queries.

## Future Enhancements
*   Integration with open-source, local AI models (e.g., via Ollama) for completely offline execution.
*   Expansion of parsing capabilities for broader scientific formats (e.g., LaTeX source, specialized datasets).

## Contact
*   **Developer:** Gopal Agrawal
*   **GitHub:** [Gopalagrawal-12](https://github.com/Gopalagrawal-12)
*   **LinkedIn:** [gopal-agrawal-41b868312](https://www.linkedin.com/in/gopal-agrawal-41b868312)
*   **Email:** 4347gopalgoyal@gmail.com
