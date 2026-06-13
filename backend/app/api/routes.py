# backend/app/api/routes.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import json
from datetime import datetime

from app.core.database import get_db_connection, init_db, log_audit
from app.models.schemas import (
    CaseUploadRequest, CaseResponse, EvidenceChainResponse,
    DiscretionMatchResponse, SimilarCaseResponse, ProcedureCheckResponse,
    RiskReportResponse, AuditLogEntry, HealthResponse
)
from app.services.case_parser import CaseParser
from app.services.evidence_chain_checker import EvidenceChainChecker
from app.services.discretion_benchmark import DiscretionBenchmark
from app.services.case_similarity_retriever import CaseSimilarityRetriever
from app.services.procedure_legal_checker import ProcedureLegalChecker
from app.services.case_risk_scorer import CaseRiskScorer
from app.services.report_generator import ReportGenerator

router = APIRouter()

# --- 无状态/全局共享服务（无实例间可变状态冲突） ---
discretion_benchmark = DiscretionBenchmark()
similarity_retriever = CaseSimilarityRetriever()
risk_scorer = CaseRiskScorer()
report_generator = ReportGenerator()


def _new_case_parser() -> CaseParser:
    """每次请求创建新实例，避免 self.nodes 跨请求污染。"""
    return CaseParser()


def _new_evidence_checker() -> EvidenceChainChecker:
    """每次请求创建新实例，避免 self.issues / self.chain_elements 跨请求污染。"""
    return EvidenceChainChecker()


def _new_procedure_checker() -> ProcedureLegalChecker:
    """每次请求创建新实例，避免 self.issues / self.timeline 跨请求污染。"""
    return ProcedureLegalChecker()

# 初始化数据库
try:
    init_db()
except Exception as e:
    print(f"Database initialization warning: {e}")

# ================== 案件管理接口 ==================

@router.post("/upload_case")
async def upload_case(request: CaseUploadRequest):
    """上传案卷"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查案件编号是否已存在
        cursor.execute("SELECT id FROM cases WHERE case_number = ?", (request.case_number,))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            raise HTTPException(status_code=400, detail="案件编号已存在")
        
        # 插入新案件
        cursor.execute("""
            INSERT INTO cases (case_number, case_type, content, filing_date, status)
            VALUES (?, ?, ?, ?, 'pending')
        """, (request.case_number, request.case_type, request.content, request.filing_date))
        
        case_id = cursor.lastrowid
        
        # 记录审计日志
        log_audit("upload_case", "cases", case_id, f"上传案件: {request.case_number}")
        
        conn.commit()
        conn.close()
        
        return {"case_id": case_id, "case_number": request.case_number, "status": "上传成功"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze_case")
async def analyze_case(case_id: int):
    """分析案卷合规性"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取案件信息
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        case = cursor.fetchone()
        
        if not case:
            conn.close()
            raise HTTPException(status_code=404, detail="案件不存在")
        
        case_content = case["content"]
        case_number = case["case_number"]
        case_type = case["case_type"]
        filing_date = case["filing_date"]
        
        # 解析案卷结构（每次请求新建实例，避免并发状态污染）
        case_parser = _new_case_parser()
        parsed_nodes = case_parser.parse(case_content, case_type)

        # 检测证据链
        evidence_chain_checker = _new_evidence_checker()
        evidence_result = evidence_chain_checker.check(case_content, parsed_nodes)
        
        # 获取处罚信息
        cursor.execute("SELECT * FROM penalty_records WHERE case_id = ?", (case_id,))
        penalty_record = cursor.fetchone()
        
        penalty_info = {}
        if penalty_record:
            penalty_info = {
                "penalty_type": penalty_record["penalty_type"],
                "amount": penalty_record["amount"],
            }
        
        # 裁量基准匹配
        discretion_result = discretion_benchmark.match(case_content, penalty_info)
        
        # 程序合法性检测
        procedure_checker = _new_procedure_checker()
        procedure_result = procedure_checker.check(case_content, parsed_nodes)
        
        # 同案相似度检测
        similarity_result = {"similar_cases": []}
        similar_cases = similarity_retriever.search(case_content, top_k=5)
        similarity_result["similar_cases"] = similar_cases
        
        # 风险熵评分
        risk_result = risk_scorer.score(
            evidence_result, discretion_result, procedure_result, similarity_result, case_content
        )
        
        # 保存分析结果
        risk_level = risk_result.get("risk_level", "未知")
        risk_score = risk_result.get("total_risk_score", 0)
        
        cursor.execute("""
            INSERT INTO analysis_results (case_id, risk_score, risk_level, details_json)
            VALUES (?, ?, ?, ?)
        """, (case_id, risk_score, risk_level, json.dumps(risk_result, ensure_ascii=False)))
        
        # 更新案件状态
        cursor.execute("UPDATE cases SET status = 'analyzed' WHERE id = ?", (case_id,))
        
        # 记录审计日志
        log_audit("analyze_case", "cases", case_id, f"分析案件: {case_number}, 风险等级: {risk_level}")
        
        conn.commit()
        conn.close()
        
        return {
            "case_id": case_id,
            "case_number": case_number,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "radar_data": risk_result.get("radar_data", {}),
            "parsed_nodes": parsed_nodes,
            "evidence_result": evidence_result,
            "discretion_result": discretion_result,
            "procedure_result": procedure_result,
            "similarity_result": similarity_result,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check_evidence_chain")
async def check_evidence_chain(case_id: int):
    """检测证据链完整性"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        case = cursor.fetchone()
        
        if not case:
            conn.close()
            raise HTTPException(status_code=404, detail="案件不存在")
        
        case_parser = _new_case_parser()
        parsed_nodes = case_parser.parse(case["content"], case["case_type"])
        evidence_chain_checker = _new_evidence_checker()
        result = evidence_chain_checker.check(case["content"], parsed_nodes)

        conn.close()

        return {
            "case_id": case_id,
            "is_complete": result["is_complete"],
            "score": result["score"],
            "chain_completeness": result["chain_completeness"],
            "evidence_sufficiency": result["evidence_sufficiency"],
            "issues": result["issues"],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/match_discretion")
async def match_discretion(case_id: int):
    """匹配裁量基准"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        case = cursor.fetchone()
        
        if not case:
            conn.close()
            raise HTTPException(status_code=404, detail="案件不存在")
        
        cursor.execute("SELECT * FROM penalty_records WHERE case_id = ?", (case_id,))
        penalty_record = cursor.fetchone()
        
        penalty_info = {}
        if penalty_record:
            penalty_info = {
                "penalty_type": penalty_record["penalty_type"],
                "amount": penalty_record["amount"],
            }
        
        result = discretion_benchmark.match(case["content"], penalty_info)
        
        conn.close()
        
        return {
            "case_id": case_id,
            "penalty_type": result["penalty_type"],
            "amount": result["amount"],
            "benchmark_min": result["benchmark_min"],
            "benchmark_max": result["benchmark_max"],
            "deviation": result["deviation"],
            "is_abnormal": result["is_abnormal"],
            "match_level": result["match_level"],
            "issues": result["issues"],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search_similar_cases")
async def search_similar_cases(case_id: int, top_k: int = 5):
    """检索相似案例"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        case = cursor.fetchone()
        
        if not case:
            conn.close()
            raise HTTPException(status_code=404, detail="案件不存在")
        
        similar_cases = similarity_retriever.search(case["content"], top_k)
        
        conn.close()
        
        return {
            "case_id": case_id,
            "similar_cases": similar_cases,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/check_procedure")
async def check_procedure(case_id: int):
    """校验程序合法性"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        case = cursor.fetchone()
        
        if not case:
            conn.close()
            raise HTTPException(status_code=404, detail="案件不存在")
        
        case_parser = _new_case_parser()
        parsed_nodes = case_parser.parse(case["content"], case["case_type"])
        procedure_checker = _new_procedure_checker()
        result = procedure_checker.check(case["content"], parsed_nodes)

        conn.close()

        return {
            "case_id": case_id,
            "is_legal": result["is_legal"],
            "score": result["score"],
            "issues": result["issues"],
            "timeline": result["timeline"],
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_risk_report/{case_id}")
async def get_risk_report(case_id: int):
    """获取风险报告"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        case = cursor.fetchone()
        
        if not case:
            conn.close()
            raise HTTPException(status_code=404, detail="案件不存在")
        
        cursor.execute("SELECT * FROM analysis_results WHERE case_id = ? ORDER BY created_at DESC LIMIT 1", (case_id,))
        analysis = cursor.fetchone()
        
        if not analysis:
            conn.close()
            raise HTTPException(status_code=404, detail="请先分析案件")
        
        case_info = {
            "case_number": case["case_number"],
            "case_type": case["case_type"],
            "filing_date": case["filing_date"],
            "status": case["status"],
        }
        
        risk_result = json.loads(analysis["details_json"])
        
        # 生成完整报告
        report = report_generator.generate(
            case_info=case_info,
            analysis_result=risk_result,
            evidence_result={},
            discretion_result={},
            procedure_result={},
            similarity_result={},
            risk_result=risk_result,
        )
        
        conn.close()
        
        return report
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_case/{case_id}")
async def get_case(case_id: int):
    """获取案卷信息"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        case = cursor.fetchone()
        
        if not case:
            conn.close()
            raise HTTPException(status_code=404, detail="案件不存在")
        
        # 解析案卷结构
        case_parser = _new_case_parser()
        parsed_nodes = case_parser.parse(case["content"], case["case_type"])

        conn.close()

        return {
            "id": case["id"],
            "case_number": case["case_number"],
            "case_type": case["case_type"],
            "content": case["content"],
            "filing_date": case["filing_date"],
            "status": case["status"],
            "created_at": case["created_at"],
            "parsed_nodes": parsed_nodes,
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit_logs")
async def get_audit_logs(limit: int = 100):
    """获取审计日志"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT ?", (limit,))
        logs = cursor.fetchall()
        
        conn.close()
        
        return {
            "logs": [
                {
                    "id": log["id"],
                    "action": log["action"],
                    "target_type": log["target_type"],
                    "target_id": log["target_id"],
                    "details": log["details"],
                    "created_at": log["created_at"],
                }
                for log in logs
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "version": "1.0.0"
    }
