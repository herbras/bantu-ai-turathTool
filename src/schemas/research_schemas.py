from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class IslamicRuling(str, Enum):
    """Islamic legal rulings"""

    HALAL = "halal"
    HARAM = "haram"
    MAKRUH = "makruh"
    MUBAH = "mubah"
    MUSTAHAB = "mustahab"
    WAJIB = "wajib"


class MazhabPerspective(BaseModel):
    """Perspective from Islamic school of thought"""

    mazhab: str = Field(
        ..., description="Name of Islamic mazhab (Hanafi, Shafi'i, Maliki, Hanbali)"
    )
    ruling: Optional[IslamicRuling] = Field(
        None, description="The ruling according to this mazhab"
    )
    evidence: str = Field(..., description="Evidence or reasoning from this mazhab")
    scholars: List[str] = Field(
        default=[], description="Key scholars supporting this view"
    )


class IslamicEvidence(BaseModel):
    """Evidence from Islamic sources"""

    source_type: str = Field(
        ..., description="Type of source: Quran, Hadith, Ijma, Qiyas, etc."
    )
    reference: str = Field(
        ..., description="Specific reference (ayah, hadith number, etc.)"
    )
    text_arabic: Optional[str] = Field(
        None, description="Original Arabic text if available"
    )
    text_translation: str = Field(..., description="Translation or explanation")
    authenticity: Optional[str] = Field(
        None, description="Authenticity grade for hadith"
    )


class TurathQueryResult(BaseModel):
    """Structured result from Turath database query"""

    query: str = Field(..., description="The search query used")
    main_ruling: Optional[IslamicRuling] = Field(
        None, description="Primary Islamic ruling"
    )
    summary: str = Field(..., description="Concise summary of findings")
    detailed_explanation: str = Field(
        ..., description="Detailed explanation of the ruling and reasoning"
    )

    # Evidence and sources
    quran_evidence: List[IslamicEvidence] = Field(
        default=[], description="Evidence from Quran"
    )
    hadith_evidence: List[IslamicEvidence] = Field(
        default=[], description="Evidence from Hadith"
    )
    scholarly_consensus: Optional[str] = Field(
        None, description="Information about ijma (consensus)"
    )

    # Mazhab perspectives
    mazhab_perspectives: List[MazhabPerspective] = Field(
        default=[], description="Views from different mazahib"
    )

    # Contemporary application
    contemporary_ruling: Optional[str] = Field(
        None, description="Contemporary application and considerations"
    )
    practical_guidance: List[str] = Field(
        default=[], description="Practical guidance for Muslims"
    )

    # Metadata
    confidence_level: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Confidence in the ruling (0-1)"
    )
    sources_used: List[str] = Field(
        default=[], description="List of source books/references used"
    )
    related_topics: List[str] = Field(
        default=[], description="Related topics for further study"
    )


class ScholarlyAnalysis(BaseModel):
    """Scholarly analysis and academic perspective"""

    key_points: List[str] = Field(..., description="Key points from scholarly analysis")
    historical_context: Optional[str] = Field(
        None, description="Historical context if relevant"
    )
    methodological_approach: str = Field(
        ..., description="Methodology used in reaching conclusions"
    )
    limitations: List[str] = Field(
        default=[], description="Limitations or areas needing further study"
    )
    recommendations: List[str] = Field(
        default=[], description="Recommendations for practitioners"
    )


class ResearchFindings(BaseModel):
    """Complete research findings for a topic"""

    topic: str = Field(..., description="The research topic")
    research_type: str = Field(
        ..., description="Type of research: comprehensive, quick, academic"
    )

    # Core findings
    turath_results: List[TurathQueryResult] = Field(
        ..., description="Results from Turath database"
    )
    scholarly_analysis: ScholarlyAnalysis = Field(..., description="Academic analysis")

    # Cross-validation
    consensus_level: str = Field(
        ..., description="Level of consensus: strong, moderate, weak, disputed"
    )
    conflicting_views: List[str] = Field(
        default=[], description="Areas of disagreement or debate"
    )

    # Practical application
    final_recommendation: str = Field(..., description="Final practical recommendation")
    implementation_guidelines: List[str] = Field(
        default=[], description="How to implement in daily life"
    )

    # Research metadata
    sources_count: int = Field(..., description="Number of sources consulted")
    research_duration_seconds: float = Field(..., description="Time taken for research")
    quality_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Overall quality score"
    )
