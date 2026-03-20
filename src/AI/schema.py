from pydantic import BaseModel, Field
from typing import List, Dict, Any

class AuditVerdict(BaseModel):
    rigor_score: int
    publication_readiness: str
    critical_flaw: str

class PlagiarismReport(BaseModel):
    status: str
    similarity: float
    source: str
    rehabilitation_fix: str

class MarketRelevance(BaseModel):
    score: float
    status: str
    gap_analysis: str

class SuggestedPaper(BaseModel):
    title: str
    reason: str
    utility: str

class GlossaryItem(BaseModel):
    term: str
    definition: str

class ResearchAudit(BaseModel):
    summary: List[str]
    hypothesis: str
    methodology: List[str]
    quantitative_findings: List[str]
    unique_scientific_insights: List[str]
    audit_verdict: AuditVerdict
    plagiarism_report: PlagiarismReport
    market_relevance: MarketRelevance
    suggested_papers: List[SuggestedPaper]
    glossary: List[GlossaryItem]
    library_link: str
    citations: List[str]