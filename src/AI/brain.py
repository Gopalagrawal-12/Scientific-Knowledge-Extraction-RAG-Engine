import os
import json
import numpy as np
import chromadb
from groq import Groq
from serpapi import GoogleSearch
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

load_dotenv()


def calculate_market_relevance(current_text, market_snippets):
    """Calculates Cosine Similarity between user text and web benchmarks."""
    if not market_snippets:
        return 0

    # Vectorize current text against market snippets
    vectorizer = TfidfVectorizer()
    # Compare first 5000 chars of research to snippets found on Google
    all_texts = [current_text[:5000]] + market_snippets
    tfidf_matrix = vectorizer.fit_transform(all_texts)

    # Compare current text (index 0) to the average of the market results
    current_vec = tfidf_matrix[0:1]
    market_vecs = tfidf_matrix[1:]
    similarities = cosine_similarity(current_vec, market_vecs)

    return round(np.mean(similarities) * 100, 2)


def check_plagiarism_simple(text_segment):
    """Grounded search to find real-world matches via SerpApi."""
    if not os.getenv("SERP_API_KEY"):
        return {"similarity_score": 0, "source": None, "snippets": []}

    params = {
        "q": f'"{text_segment[:120]}"',
        "api_key": os.getenv("SERP_API_KEY")
    }
    try:
        search = GoogleSearch(params)
        results = search.get_dict()
        if "organic_results" in results:
            top = results["organic_results"][0]
            # Capture top 5 snippets for the relevance calculation
            snippets = [r.get("snippet", "") for r in results["organic_results"][:5]]
            similarity = SequenceMatcher(None, text_segment, top.get("snippet", "")).ratio() * 100
            return {
                "similarity_score": round(similarity, 2),
                "source": top.get("link"),
                "snippets": snippets
            }
    except Exception:
        pass
    return {"similarity_score": 0, "source": None, "snippets": []}


def get_related_context(markdown_text, current_user):
    """Internal library similarity search strictly segregated by user_id."""
    try:
        db = chromadb.PersistentClient(path="./buddy_storage")
        collection = db.get_collection("research_buddy_docs")

        # STRENGTHENED: Filter query results by the specific user_id string
        results = collection.query(
            query_texts=[markdown_text[:2000]],
            n_results=2,
            where={"user_id": str(current_user)}  # <--- Ensures User A never sees User B's files
        )

        # Return filename from the user's specific metadata if found
        if results['metadatas'] and len(results['metadatas'][0]) > 0:
            return results['metadatas'][0][0]['filename']
    except Exception as e:
        print(f"Context retrieval error: {e}")

    return "No prior relevant documents found."


def generate_buddy_dashboard(markdown_text, previous_docs, current_user):
    """Generates the main audit JSON using LLM processing."""
    client = Groq(api_key=os.getenv("RESEARCHER_API_KEY"))

    # 1. PRE-AUDIT: Check a high-risk segment for plagiarism
    test_segment = markdown_text[1000:1300]
    market_data = check_plagiarism_simple(test_segment)

    # 2. CALCULATE MARKET RELEVANCE
    market_score = calculate_market_relevance(markdown_text, market_data["snippets"])

    # 3. DYNAMIC SCALING FOR OUTPUT LIMITS
    word_count = len(markdown_text.split())
    glossary_limit = max(8, min(120, word_count // 40))

    # Ensure most_related only pulls files for this specific user
    most_related = get_related_context(markdown_text, current_user)

    # 4. THE AUTHORITATIVE PROMPT
    # model swapped to llama-3.1-8b-instant to avoid TPD rate limits
    prompt = (
            "SYSTEM ROLE: Lead Editor at a Tier-1 Scientific Journal.\n"
            f"TARGET USER SILO: {current_user}\n"
            "OUTPUT FORMAT: Strict JSON.\n\n"
            f"LIBRARY CONTEXT (Current User Only): {previous_docs}\n"
            f"INTERNAL CROSS-REFERENCE: {most_related}\n"
            f"EXTERNAL PLAGIARISM EVIDENCE: {json.dumps(market_data)}\n\n"
            f"TEXT TO AUDIT ({word_count} words):\n{markdown_text[:12000]}\n\n"  # Reduced token length to prevent limit errors
            "INSTRUCTIONS:\n"
            "Perform a 'Brutal Scientific Audit'. Tone: Cold, Clinical, Authoritative.\n\n"
            "REQUIRED JSON STRUCTURE:\n"
            "- 'summary': 5 dense paragraphs.\n"
            "- 'hypothesis': The precise intended goal.\n"
            "- 'methodology': A LIST of technical steps.\n"
            "- 'quantitative_findings': A LIST of metrics/stats.\n"
            "- 'unique_scientific_insights': A LIST of logical takeaways.\n"
            "- 'audit_verdict': { 'rigor_score': 0-100, 'publication_readiness': 'High/Med/Low', 'critical_flaw': 'str' }\n"
            "- 'plagiarism_report': { 'status': 'Flagged/Clear', 'similarity': " + str(
        market_data['similarity_score']) + ", 'source': '" + str(
        market_data['source']) + "', 'rehabilitation_fix': 'str' },\n"
                                 "- 'market_relevance': { 'score': " + str(
        market_score) + ", 'status': 'High/Med/Low', 'gap_analysis': 'str' },\n"
                        "- 'suggested_papers': [ { 'title': 'Exact Title', 'reason': 'Why it fills a gap', 'utility': 'str' } ],\n"
                        f"- 'glossary': A LIST of {glossary_limit} technical terms (term and definition),\n"
                        "- 'library_link': Technical connection to " + most_related + ",\n"
                                                                                      "- 'citations': LIST of all referenced works."
    )

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Swapped from 70b to avoid RateLimitError 429
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.3
    )

    return response.choices[0].message.content