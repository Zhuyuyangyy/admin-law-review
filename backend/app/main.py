from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime
import random

router = APIRouter(prefix="/api/v1", tags=["admin-law-review"])

class ReviewCaseRequest(BaseModel):
    case_id: str
    facts: List[str]
    evidence: List[Dict]  # [{"evidence_id": str, "description": str, "type": str, "weight": float}]
    procedure_steps: List[Dict]  # [{"step": str, "completed": bool, "timestamp": str}]

class ConsistencyRequest(BaseModel):
    case_id: str
    facts: List[str]
    evidence_map: Dict[str, str]  # evidence_id -> supported_fact

class ProcedureRequest(BaseModel):
    case_id: str
    procedure_steps: List[Dict]
    required_procedures: List[str]

@router.post("/review_case")
async def review_case(req: ReviewCaseRequest):
    """Comprehensive admin case review: facts, evidence, procedure"""
    evidence_weights = {e["evidence_id"]: e.get("weight", 0.5) for e in req.evidence}
    evidence_types = {e["evidence_id"]: e.get("type", "unknown") for e in req.evidence}
    fact_coverage = {}
    for fact in req.facts:
        supporting = [e["evidence_id"] for e in req.evidence if e.get("description", "") and any(word in fact for word in e.get("description", "").split()[:3]))]
        fact_coverage[fact] = {"supporting_evidence": supporting, "coverage_score": round(sum(evidence_weights.get(eid, 0) for eid in supporting) / max(len(supporting), 1), 3)}
    evidence_assessment = []
    for e in req.evidence:
        quality_score = e.get("weight", 0.5) * (0.9 if e.get("type") in ["物证", "书证", "鉴定意见"] else 0.6 if e.get("type") in ["证人证言", "当事人陈述"] else 0.4)
        evidence_assessment.append({"evidence_id": e["evidence_id"], "quality_score": round(quality_score, 3), "assessment": "强" if quality_score > 0.7 else "中" if quality_score > 0.4 else "弱", "type": e.get("type", "unknown")})
    procedure_compliance = []
    for step in req.procedure_steps:
        compliance_rate = 100 if step.get("completed") else 0
        procedure_compliance.append({"step": step.get("step", ""), "completed": step.get("completed", False), "compliance_rate": compliance_rate, "timestamp": step.get("timestamp", "")})
    overall_score = round(sum(e["quality_score"] * evidence_weights.get(e["evidence_id"], 0.5) for e in evidence_assessment) / max(len(evidence_assessment), 1), 3)
    return {"case_id": req.case_id, "fact_count": len(req.facts), "evidence_count": len(req.evidence), "fact_coverage": fact_coverage, "evidence_assessment": evidence_assessment, "procedure_compliance": procedure_compliance, "overall_quality_score": overall_score, "review_timestamp": datetime.now().isoformat()}

@router.post("/check_facts_evidence_consistency")
async def check_facts_evidence_consistency(req: ConsistencyRequest):
    """Check consistency between facts and evidence"""
    inconsistencies = []
    for fact in req.facts:
        relevant_evidence = [eid for eid, fid in req.evidence_map.items() if fid == fact]
        if not relevant_evidence:
            inconsistencies.append({"fact": fact, "issue": "无相关证据支持", "severity": "high"})
        else:
            conflicting = [eid for eid in relevant_evidence if any(c in fact for c in ["矛盾", "冲突", "不一致"])]
            if conflicting:
                inconsistencies.append({"fact": fact, "issue": f"证据{conflicting}可能矛盾", "severity": "medium"})
    contradiction_score = round(len(inconsistencies) / max(len(req.facts), 1), 3)
    return {"case_id": req.case_id, "total_facts": len(req.facts), "inconsistencies_found": len(inconsistencies), "contradiction_score": contradiction_score, "inconsistencies": inconsistencies, "consistency_verdict": "证据充分" if contradiction_score < 0.2 else "存疑需补充" if contradiction_score < 0.5 else "事实认定存疑"}

@router.post("/assess_procedure_compliance")
async def assess_procedure_compliance(req: ProcedureRequest):
    """Assess whether procedure steps comply with legal requirements"""
    required = set(req.required_procedures)
    completed = set(step["step"] for step in req.procedure_steps if step.get("completed"))
    missing = required - completed
    extra_steps = [step for step in req.procedure_steps if step.get("completed") and step["step"] not in required]
    compliance_rate = round(len(completed & required) / max(len(required), 1) * 100, 1)
    violations = []
    if missing:
        violations.append({"type": "missing_required_step", "steps": list(missing), "severity": "critical"})
    for step in req.procedure_steps:
        if not step.get("completed") and step["step"] in required:
            violations.append({"type": "incomplete_step", "step": step["step"], "severity": "high"})
    return {"case_id": req.case_id, "compliance_rate": compliance_rate, "required_steps": list(required), "completed_steps": list(completed & required), "missing_steps": list(missing), "extra_steps": [s["step"] for s in extra_steps], "violations": violations, "verdict": "程序合法" if compliance_rate == 100 and not violations else "程序违法" if compliance_rate < 70 else "程序瑕疵"}

@router.get("/get_case_summary")
async def get_case_summary(case_id: str):
    """Get case summary for a given case ID"""
    return {"case_id": case_id, "case_type": random.choice(["行政处罚", "行政许可", "行政强制", "行政复议"]), "case_status": random.choice(["已立案", "调查中", "审理中", "已结案"]), "summary": f"案件编号{case_id}，涉及{random.choice(['行政处罚', '土地纠纷', '环保查处', '工商登记'])}事项，已完成事实认定和证据审核，程序合规性良好。", "key_findings": ["事实认定清楚", "证据链完整", "法律适用正确"], "decision": "维持原决定" if random.random() > 0.3 else "发回重审", "confidence": round(random.uniform(0.75, 0.95), 2)}