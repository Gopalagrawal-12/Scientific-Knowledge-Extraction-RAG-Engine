import os
import json
import numpy as np
from qdrant_client import QdrantClient, models
from groq import Groq
from serpapi import GoogleSearch
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Internal Project Imports
from llama_index.core import Settings
# Note: ResearchAudit from schema is kept for documentation/validation if needed,
# but we use standard string-based JSON prompting for Groq SDK compatibility.
from schema import ResearchAudit

load_dotenv()

# Qdrant Configuration
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")


def get_qdrant_client():
    """Returns a secure Qdrant Cloud client."""
    return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)


def check_plagiarism_simple(text_segment):
    """Grounded search to find real-world matches via SerpApi."""
    api_key = os.getenv("SERP_API_KEY")
    if not api_key:
        return {"similarity_score": 0, "source": "N/A", "snippets": []}

    search_query = f'"{text_segment[:120].strip()}"'
    params = {"q": search_query, "api_key": api_key, "num": 3}

    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if "organic_results" in results and len(results["organic_results"]) > 0:
            top_match = results["organic_results"][0]
            snippets = [r.get("snippet", "") for r in results["organic_results"]]
            match_text = top_match.get("snippet", "")
            similarity = SequenceMatcher(None, text_segment, match_text).ratio() * 100
            return {
                "similarity_score": round(similarity, 2),
                "source": top_match.get("link"),
                "snippets": snippets
            }
    except Exception as e:
        print(f"❌ SerpApi Error: {e}")
    return {"similarity_score": 0, "source": "N/A", "snippets": []}


def get_related_context(markdown_text, current_user):
    """Internal library similarity search using modern Qdrant query_points."""
    try:
        client = get_qdrant_client()
        query_vector = Settings.embed_model.get_query_embedding(markdown_text[:2000])

        response = client.query_points(
            collection_name="research_buddy_docs",
            query=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.user_id",
                        match=models.MatchValue(value=str(current_user))
                    )
                ]
            ),
            limit=1
        )

        if response.points:
            return response.points[0].payload["metadata"]["filename"]
    except Exception as e:
        print(f"Context retrieval error: {e}")
    return "None"


def calculate_market_relevance(current_text, market_snippets):
    """Calculates Cosine Similarity between user text and web benchmarks."""
    if not market_snippets:
        return 0
    try:
        vectorizer = TfidfVectorizer(stop_words='english')
        all_texts = [current_text[:5000]] + market_snippets
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        current_vec = tfidf_matrix[0:1]
        market_vecs = tfidf_matrix[1:]
        similarities = cosine_similarity(current_vec, market_vecs)
        return round(np.mean(similarities) * 100, 2)
    except Exception as e:
        print(f"⚠️ Market Relevance Error: {e}")
        return 0


def generate_buddy_dashboard(markdown_text, previous_docs, current_user):
    """Standard Version: No .beta, no .parse. Guaranteed to run on your environment."""
    # Use the Researcher specific API Key
    client = Groq(api_key=os.getenv("RESEARCHER_API_KEY"))

    # 1. Gather Contextual Data
    test_segment = markdown_text[1000:1300]
    market_data = check_plagiarism_simple(test_segment)
    market_score = calculate_market_relevance(markdown_text, market_data["snippets"])
    most_related = get_related_context(markdown_text, current_user)

    # 2. Strict Prompt Construction
    prompt = (
        "SYSTEM ROLE: Lead Editor at a Tier-1 Scientific Journal.\n"
        "TASK: Perform a 'Brutal Scientific Audit'. Return ONLY a JSON object.\n\n"
        "REQUIRED JSON STRUCTURE:\n"
        "{\n"
        "  'summary': ['5 dense paragraphs'],\n"
        "  'hypothesis': 'string',\n"
        "  'methodology': ['list'],\n"
        "  'quantitative_findings': ['list of stats'],\n"
        "  'unique_scientific_insights': ['list'],\n"
        "  'audit_verdict': { 'rigor_score': 0-100, 'publication_readiness': 'High/Med/Low', 'critical_flaw': 'str' },\n"
        f"  'plagiarism_report': {{ 'status': 'Flagged/Clear', 'similarity': {market_data['similarity_score']}, 'source': '{market_data.get('source', 'N/A')}', 'rehabilitation_fix': 'str' }},\n"
        f"  'market_relevance': {{ 'score': {market_score}, 'status': 'High/Med/Low', 'gap_analysis': 'str' }},\n"
        "  'suggested_papers': [{ 'title': 'str', 'reason': 'str', 'utility': 'str' }],\n"
        "  'glossary': [{ 'term': 'str', 'definition': 'str' }],\n"
        f"  'library_link': '{most_related}',\n"
        "  'citations': ['list']\n"
        "}\n\n"
        f"TEXT TO AUDIT:\n{markdown_text[:12000]}"
    )

    # 3. STANDARD CREATE CALL - No '.beta' attribute exists in this line
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.1
    )

    return response.choices[0].message.content