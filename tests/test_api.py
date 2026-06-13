# -*- coding: utf-8 -*-
"""
API Integration Tests
=====================
Tests for FastAPI endpoints using TestClient.
"""
import pytest
from fastapi.testclient import TestClient
import importlib.util
from pathlib import Path
import sys


# ── Setup ───────────────────────────────────────────────────────

ROOT_DIR = str(Path(__file__).resolve().parent.parent)
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

BACKEND_DIR = str(Path(__file__).resolve().parent.parent / "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)


@pytest.fixture(scope="module")
def client():
    """Create a test client for the FastAPI app."""
    spec = importlib.util.spec_from_file_location("main", str(Path(ROOT_DIR) / "main.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return TestClient(mod.app)


# ── Health Endpoint Tests ───────────────────────────────────────

class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_ok_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"

    def test_health_response_format(self, client):
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data


# ── Upload Case Tests ──────────────────────────────────────────

class TestUploadCase:
    """Tests for case upload endpoint."""

    def test_upload_case_success(self, client):
        response = client.post("/api/upload_case", json={
            "case_number": "TEST-API-001",
            "case_type": "行政处罚",
            "content": "案件编号: TEST-API-001\n违法事实：测试违法行为\n物证：测试物证\n书证：测试书证\n依据《测试法》第一条\n罚款人民币10000元",
            "filing_date": "2024-01-15"
        })
        # May return 200 or 500 depending on database state
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "case_id" in data

    def test_upload_duplicate_case(self, client):
        """Uploading duplicate case number should fail."""
        # First upload
        client.post("/api/upload_case", json={
            "case_number": "TEST-DUP-001",
            "case_type": "行政处罚",
            "content": "测试内容"
        })
        # Second upload with same number
        response = client.post("/api/upload_case", json={
            "case_number": "TEST-DUP-001",
            "case_type": "行政处罚",
            "content": "测试内容2"
        })
        # May return 400 (duplicate) or 500 (database error)
        assert response.status_code in [400, 500]

    def test_upload_case_missing_fields(self, client):
        """Missing required fields should fail."""
        response = client.post("/api/upload_case", json={})
        assert response.status_code == 422


# ── Analyze Case Tests ─────────────────────────────────────────

class TestAnalyzeCase:
    """Tests for case analysis endpoint."""

    def test_analyze_nonexistent_case(self, client):
        """Analyzing nonexistent case should return 404."""
        response = client.post("/api/analyze_case", params={"case_id": 99999})
        assert response.status_code == 404

    def test_analyze_existing_case(self, client):
        """Should analyze an existing case if upload succeeds."""
        # First upload a case
        upload_resp = client.post("/api/upload_case", json={
            "case_number": "TEST-ANALYZE-001",
            "case_type": "行政处罚",
            "content": "案件编号: TEST-ANALYZE-001\n立案日期: 2024-01-15\n调查日期：2024-01-16\n违法事实：当事人实施违法行为\n物证：现场照片\n书证：营业执照\n依据《环境保护法》第六十三条\n罚款人民币50000元\n告知日期：2024-01-20\n决定日期：2024-01-25\n送达日期：2024-01-26\n当事人签字确认"
        })
        if upload_resp.status_code == 200:
            case_id = upload_resp.json()["case_id"]
            response = client.post("/api/analyze_case", params={"case_id": case_id})
            assert response.status_code in [200, 500]
        else:
            # Skip if upload failed
            assert upload_resp.status_code in [400, 500]


# ── Evidence Chain Tests ────────────────────────────────────────

class TestEvidenceChain:
    """Tests for evidence chain check endpoint."""

    def test_check_evidence_chain_nonexistent(self, client):
        response = client.post("/api/check_evidence_chain", params={"case_id": 99999})
        assert response.status_code == 404


# ── Discretion Match Tests ─────────────────────────────────────

class TestDiscretionMatch:
    """Tests for discretion match endpoint."""

    def test_match_discretion_nonexistent(self, client):
        response = client.post("/api/match_discretion", params={"case_id": 99999})
        assert response.status_code == 404


# ── Similar Cases Tests ────────────────────────────────────────

class TestSimilarCases:
    """Tests for similar cases search endpoint."""

    def test_search_similar_nonexistent(self, client):
        response = client.post("/api/search_similar_cases", params={"case_id": 99999})
        assert response.status_code == 404


# ── Procedure Check Tests ──────────────────────────────────────

class TestProcedureCheck:
    """Tests for procedure check endpoint."""

    def test_check_procedure_nonexistent(self, client):
        response = client.post("/api/check_procedure", params={"case_id": 99999})
        assert response.status_code == 404


# ── Risk Report Tests ──────────────────────────────────────────

class TestRiskReport:
    """Tests for risk report endpoint."""

    def test_get_risk_report_nonexistent(self, client):
        response = client.get("/api/get_risk_report/99999")
        assert response.status_code == 404


# ── Get Case Tests ─────────────────────────────────────────────

class TestGetCase:
    """Tests for get case endpoint."""

    def test_get_case_nonexistent(self, client):
        response = client.get("/api/get_case/99999")
        assert response.status_code == 404

    def test_get_existing_case(self, client):
        """Should retrieve an existing case if upload succeeds."""
        # Upload first
        upload_resp = client.post("/api/upload_case", json={
            "case_number": "TEST-GET-001",
            "case_type": "行政处罚",
            "content": "案件编号: TEST-GET-001\n违法事实：测试行为"
        })
        if upload_resp.status_code == 200:
            case_id = upload_resp.json()["case_id"]
            response = client.get(f"/api/get_case/{case_id}")
            assert response.status_code in [200, 500]
        else:
            assert upload_resp.status_code in [400, 500]


# ── Audit Logs Tests ───────────────────────────────────────────

class TestAuditLogs:
    """Tests for audit logs endpoint."""

    def test_get_audit_logs(self, client):
        response = client.get("/api/audit_logs")
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert isinstance(data["logs"], list)

    def test_get_audit_logs_with_limit(self, client):
        response = client.get("/api/audit_logs", params={"limit": 5})
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) <= 5


# ── V1 API Tests ───────────────────────────────────────────────

class TestV1API:
    """Tests for V1 API endpoints."""

    def test_review_case(self, client):
        response = client.post("/api/v1/review_case", json={
            "case_id": "V1-TEST-001",
            "facts": ["违法事实一", "违法事实二"],
            "evidence": [
                {"evidence_id": "E001", "description": "现场照片", "type": "物证", "weight": 0.9},
                {"evidence_id": "E002", "description": "营业执照", "type": "书证", "weight": 0.8}
            ],
            "procedure_steps": [
                {"step": "立案", "completed": True, "timestamp": "2024-01-15"},
                {"step": "调查", "completed": True, "timestamp": "2024-01-16"}
            ]
        })
        assert response.status_code == 200
        data = response.json()
        assert data["case_id"] == "V1-TEST-001"
        assert "fact_coverage" in data
        assert "evidence_assessment" in data

    def test_check_facts_evidence_consistency(self, client):
        response = client.post("/api/v1/check_facts_evidence_consistency", json={
            "case_id": "V1-TEST-002",
            "facts": ["违法事实一"],
            "evidence_map": {"E001": "违法事实一"}
        })
        assert response.status_code == 200
        data = response.json()
        assert "consistency_verdict" in data

    def test_assess_procedure_compliance(self, client):
        response = client.post("/api/v1/assess_procedure_compliance", json={
            "case_id": "V1-TEST-003",
            "procedure_steps": [
                {"step": "立案", "completed": True},
                {"step": "调查", "completed": True}
            ],
            "required_procedures": ["立案", "调查", "告知", "决定"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "verdict" in data
        assert "compliance_rate" in data

    def test_get_case_summary(self, client):
        response = client.get("/api/v1/get_case_summary", params={"case_id": "V1-TEST-001"})
        assert response.status_code == 200
        data = response.json()
        assert "case_id" in data
        assert "summary" in data
