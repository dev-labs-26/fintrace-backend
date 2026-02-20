"""
Pydantic v2 response schemas for the Financial Forensics Engine.
All field names and types match the Fintrace required JSON output format exactly.
"""

from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field, field_validator


class Transaction(BaseModel):
    """Individual transaction record for timeline visualization."""
    transaction_id: str
    sender_id: str
    receiver_id: str
    amount: float
    timestamp: str


class SuspiciousAccount(BaseModel):
    """One entry in the suspicious_accounts array."""
    account_id: str
    suspicion_score: float = Field(..., ge=0.0, le=100.0)
    detected_patterns: List[str]
    ring_id: str | None = None  # None when account is not in any ring

    @field_validator("suspicion_score", mode="before")
    @classmethod
    def round_score(cls, v: float) -> float:
        return round(float(v), 1)


class FraudRing(BaseModel):
    """One entry in the fraud_rings array."""
    ring_id: str
    member_accounts: List[str]
    pattern_type: str   # "cycle" | "smurfing" | "layered_shell" | "hybrid"
    risk_score: float = Field(..., ge=0.0, le=100.0)
    member_count: int = Field(..., ge=1)

    @field_validator("risk_score", mode="before")
    @classmethod
    def round_risk(cls, v: float) -> float:
        return round(float(v), 1)


class Summary(BaseModel):
    """Top-level summary block."""
    total_accounts_analyzed: int
    suspicious_accounts_flagged: int
    fraud_rings_detected: int
    processing_time_seconds: float

    @field_validator("processing_time_seconds", mode="before")
    @classmethod
    def round_time(cls, v: float) -> float:
        return round(float(v), 3)


class AnalysisResponse(BaseModel):
    """Root response object – strict key compliance with Fintrace format."""
    suspicious_accounts: List[SuspiciousAccount]
    fraud_rings: List[FraudRing]
    summary: Summary
    transactions: List[Transaction] = []  # Optional: for timeline visualization
