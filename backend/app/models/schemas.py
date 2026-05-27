# backend/app/models/schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime

class CaseUploadRequest(BaseModel):
    case_number: str
    case_type: str
    content: str
    filing_date: Optional[str] = None

class EvidenceRecordRequest(BaseModel):
    case_id: int
    evidence_type: str
    content: str
    submitted_date: Optional[str] = None

class PenaltyRecordRequest(BaseModel):
    case_id: int
    penalty_type: str
    amount: Optional[float] = None
    basis_article: Optional[str] = None
    discretion_basis: Optional[str] = None

class CaseAnalysisRequest(BaseModel):
    case_id: int

class EvidenceChainCheckRequest(BaseModel):
    case_id: int

class DiscretionMatchRequest(BaseModel):
    case_id: int

class SimilarCaseSearchRequest(BaseModel):
    case_id: int
    top_k: int = 5

class ProcedureCheckRequest(BaseModel):
    case_id: int

class CaseResponse(BaseModel):
    id: int
    case_number: str
    case_type: str
    content: str
    filing_date: Optional[str]
    status: str
    created_at: str

class EvidenceChainResponse(BaseModel):
    case_id: int
    is_complete: bool
    score: float
    issues: List[Dict[str, Any]]

class DiscretionMatchResponse(BaseModel):
    case_id: int
    penalty_type: str
    amount: Optional[float]
    benchmark_min: Optional[float]
    benchmark_max: Optional[float]
    deviation: Optional[float]
    is_abnormal: bool
    match_level: str

class SimilarCaseResponse(BaseModel):
    case_id: int
    similar_cases: List[Dict[str, Any]]

class ProcedureCheckResponse(BaseModel):
    case_id: int
    is_legal: bool
    score: float
    issues: List[Dict[str, Any]]

class RiskReportResponse(BaseModel):
    case_id: int
    risk_score: float
    risk_level: str
    details: Dict[str, Any]
    created_at: str

class RuleInfo(BaseModel):
    rule_id: str
    rule_type: str
    description: str
    severity: str
    penalty: str
    enabled: bool

class AuditLogEntry(BaseModel):
    id: int
    action: str
    target_type: Optional[str]
    target_id: Optional[int]
    details: Optional[str]
    created_at: str

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str = "1.0.0"
