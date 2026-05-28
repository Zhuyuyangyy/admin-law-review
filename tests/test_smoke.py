# -*- coding: utf-8 -*-
"""
admin-law-review Smoke Tests
=============================
Verifies all core service modules load and process sample data correctly.
"""
import sys
from pathlib import Path

import pytest


# ── Module Import Tests ─────────────────────────────────────────

class TestModuleImports:
    """Verify all core service modules can be imported."""

    def test_import_case_parser(self):
        from app.services.case_parser import CaseParser
        assert CaseParser is not None

    def test_import_evidence_chain_checker(self):
        from app.services.evidence_chain_checker import EvidenceChainChecker
        assert EvidenceChainChecker is not None

    def test_import_discretion_benchmark(self):
        from app.services.discretion_benchmark import DiscretionBenchmark
        assert DiscretionBenchmark is not None

    def test_import_case_similarity_retriever(self):
        from app.services.case_similarity_retriever import CaseSimilarityRetriever
        assert CaseSimilarityRetriever is not None

    def test_import_procedure_legal_checker(self):
        from app.services.procedure_legal_checker import ProcedureLegalChecker
        assert ProcedureLegalChecker is not None

    def test_import_case_risk_scorer(self):
        from app.services.case_risk_scorer import CaseRiskScorer
        assert CaseRiskScorer is not None

    def test_import_report_generator(self):
        from app.services.report_generator import ReportGenerator
        assert ReportGenerator is not None

    def test_import_schemas(self):
        from app.models.schemas import (
            CaseUploadRequest, HealthResponse, RiskReportResponse,
        )
        assert CaseUploadRequest is not None
        assert HealthResponse is not None

    def test_import_database(self):
        from app.core.database import init_db, get_db_connection
        assert init_db is not None
        assert get_db_connection is not None


# ── Sample Case Content ─────────────────────────────────────────

SAMPLE_CASE = """
案件编号: (X)罚字[2024]001号
立案日期: 2024-01-15
案件类型: 行政处罚

【调查笔录】
调查人员：张三、李四
调查日期：2024-01-16
当事人：王五
违法事实：当事人于2024年1月10日在某地实施非法倾倒废物行为

【证据材料】
物证：现场照片5张、倾倒车辆照片
书证：营业执照副本、环境影响评价文件
证人证言：目击者陈述

【违法事实】
当事人非法倾倒废物共计10吨，严重污染环境

【行政处罚告知书】
告知日期：2024-01-20
依据《环境保护法》第六十三条

【处罚决定】
罚款人民币50000元
决定日期：2024-01-25

【送达凭证】
送达日期：2024-01-26
当事人签字确认
"""


# ── CaseParser Smoke Tests ──────────────────────────────────────

class TestCaseParserSmoke:
    """Basic CaseParser functionality checks."""

    def test_parser_instantiates(self):
        from app.services.case_parser import CaseParser
        parser = CaseParser()
        assert parser is not None

    def test_parse_returns_dict(self):
        from app.services.case_parser import CaseParser
        parser = CaseParser()
        result = parser.parse(SAMPLE_CASE)
        assert isinstance(result, dict)

    def test_parse_finds_nodes(self):
        from app.services.case_parser import CaseParser
        parser = CaseParser()
        result = parser.parse(SAMPLE_CASE)
        nodes = result.get("nodes", result.get("process_nodes", []))
        assert len(nodes) > 0, "Parser should find process nodes in sample case"

    def test_parse_has_coord_map(self):
        from app.services.case_parser import CaseParser
        parser = CaseParser()
        result = parser.parse(SAMPLE_CASE)
        # Should contain coordinate mapping or process flow info
        assert "coord_map" in result or "process_nodes" in result or "nodes" in result

    def test_parse_finds_filing(self):
        from app.services.case_parser import CaseParser
        parser = CaseParser()
        result = parser.parse(SAMPLE_CASE)
        # Should detect the filing node (立案)
        content_str = str(result)
        assert "立案" in content_str or "filing" in content_str


# ── EvidenceChainChecker Smoke Tests ────────────────────────────

class TestEvidenceChainCheckerSmoke:
    """Basic evidence chain checking."""

    def test_checker_instantiates(self):
        from app.services.evidence_chain_checker import EvidenceChainChecker
        checker = EvidenceChainChecker()
        assert checker is not None

    def test_check_returns_dict(self):
        from app.services.case_parser import CaseParser
        from app.services.evidence_chain_checker import EvidenceChainChecker

        parser = CaseParser()
        parsed = parser.parse(SAMPLE_CASE)
        checker = EvidenceChainChecker()
        result = checker.check(SAMPLE_CASE, parsed)
        assert isinstance(result, dict)

    def test_check_has_score(self):
        from app.services.case_parser import CaseParser
        from app.services.evidence_chain_checker import EvidenceChainChecker

        parser = CaseParser()
        parsed = parser.parse(SAMPLE_CASE)
        checker = EvidenceChainChecker()
        result = checker.check(SAMPLE_CASE, parsed)
        assert "score" in result or "chain_score" in result or "completeness" in result

    def test_check_detects_evidence(self):
        from app.services.case_parser import CaseParser
        from app.services.evidence_chain_checker import EvidenceChainChecker

        parser = CaseParser()
        parsed = parser.parse(SAMPLE_CASE)
        checker = EvidenceChainChecker()
        result = checker.check(SAMPLE_CASE, parsed)
        # Should find evidence items in the sample case
        assert "evidence" in str(result).lower() or "issues" in result


# ── DiscretionBenchmark Smoke Tests ─────────────────────────────

class TestDiscretionBenchmarkSmoke:
    """Basic discretion benchmark matching."""

    def test_benchmark_instantiates(self):
        from app.services.discretion_benchmark import DiscretionBenchmark
        bench = DiscretionBenchmark()
        assert bench is not None

    def test_match_returns_dict(self):
        from app.services.discretion_benchmark import DiscretionBenchmark
        bench = DiscretionBenchmark()
        result = bench.match(SAMPLE_CASE, {"penalty_type": "fine", "amount": 50000})
        assert isinstance(result, dict)

    def test_match_has_issues_or_deviation(self):
        from app.services.discretion_benchmark import DiscretionBenchmark
        bench = DiscretionBenchmark()
        result = bench.match(SAMPLE_CASE, {"penalty_type": "fine", "amount": 50000})
        # Should return some analysis
        assert len(result) > 0

    def test_default_benchmarks_loaded(self):
        from app.services.discretion_benchmark import DiscretionBenchmark
        bench = DiscretionBenchmark()
        assert "罚款" in bench.benchmarks


# ── ProcedureLegalChecker Smoke Tests ───────────────────────────

class TestProcedureLegalCheckerSmoke:
    """Basic procedure legality checking."""

    def test_checker_instantiates(self):
        from app.services.procedure_legal_checker import ProcedureLegalChecker
        checker = ProcedureLegalChecker()
        assert checker is not None

    def test_check_returns_dict(self):
        from app.services.case_parser import CaseParser
        from app.services.procedure_legal_checker import ProcedureLegalChecker

        parser = CaseParser()
        parsed = parser.parse(SAMPLE_CASE)
        checker = ProcedureLegalChecker()
        result = checker.check(SAMPLE_CASE, parsed)
        assert isinstance(result, dict)

    def test_check_has_issues_list(self):
        from app.services.case_parser import CaseParser
        from app.services.procedure_legal_checker import ProcedureLegalChecker

        parser = CaseParser()
        parsed = parser.parse(SAMPLE_CASE)
        checker = ProcedureLegalChecker()
        result = checker.check(SAMPLE_CASE, parsed)
        assert "issues" in result or "score" in result or "deadline_issues" in result


# ── CaseRiskScorer Smoke Tests ──────────────────────────────────

class TestCaseRiskScorerSmoke:
    """Basic risk scoring."""

    def test_scorer_instantiates(self):
        from app.services.case_risk_scorer import CaseRiskScorer
        scorer = CaseRiskScorer()
        assert scorer is not None

    def test_risk_levels_defined(self):
        from app.services.case_risk_scorer import CaseRiskScorer
        scorer = CaseRiskScorer()
        assert len(scorer.RISK_LEVELS) == 4
        assert "重大瑕疵" in scorer.RISK_LEVELS

    def test_risk_dimensions_defined(self):
        from app.services.case_risk_scorer import CaseRiskScorer
        scorer = CaseRiskScorer()
        assert len(scorer.RISK_DIMENSIONS) == 5
        total_weight = sum(scorer.RISK_DIMENSIONS.values())
        assert abs(total_weight - 1.0) < 0.01, f"Risk weights should sum to 1.0, got {total_weight}"


# ── ReportGenerator Smoke Tests ─────────────────────────────────

class TestReportGeneratorSmoke:
    """Basic report generation."""

    def test_generator_instantiates(self):
        from app.services.report_generator import ReportGenerator
        gen = ReportGenerator()
        assert gen is not None

    def test_generate_returns_dict(self):
        from app.services.report_generator import ReportGenerator
        gen = ReportGenerator()
        report = gen.generate(
            case_info={"case_number": "TEST-001", "case_type": "行政处罚"},
            analysis_result={},
            evidence_result={"score": 0.8, "issues": []},
            discretion_result={"deviation": 0, "is_abnormal": False},
            procedure_result={"score": 0.9, "issues": []},
            similarity_result={"similar_cases": []},
            risk_result={"total_score": 15, "risk_level": "基本合规", "risk_scores": {}},
        )
        assert isinstance(report, dict)
        assert "report_title" in report
        assert "conclusion" in report


# ── CaseSimilarityRetriever Smoke Tests ─────────────────────────

class TestCaseSimilarityRetrieverSmoke:
    """Basic similarity retrieval."""

    def test_retriever_instantiates(self):
        from app.services.case_similarity_retriever import CaseSimilarityRetriever
        retriever = CaseSimilarityRetriever()
        assert retriever is not None

    def test_add_case_to_corpus(self):
        from app.services.case_similarity_retriever import CaseSimilarityRetriever
        retriever = CaseSimilarityRetriever()
        retriever.add_case_to_corpus(1, "非法倾倒废物 环境污染 罚款", "行政处罚")
        assert len(retriever.corpus) == 1

    def test_build_index(self):
        from app.services.case_similarity_retriever import CaseSimilarityRetriever
        retriever = CaseSimilarityRetriever()
        retriever.add_case_to_corpus(1, "非法倾倒废物 环境污染", "行政处罚")
        retriever.add_case_to_corpus(2, "违法建设 未经审批", "行政处罚")
        retriever.build_index()
        assert len(retriever.corpus_vectors) == 2


# ── Rules Data File ─────────────────────────────────────────────

class TestRulesData:
    """Verify the rules JSON file loads correctly."""

    def test_rules_file_exists(self):
        rules_path = Path(__file__).resolve().parent.parent / "backend" / "app" / "rules" / "admin_law_rules.json"
        assert rules_path.exists(), "admin_law_rules.json missing"

    def test_rules_file_is_valid_json(self):
        import json
        rules_path = Path(__file__).resolve().parent.parent / "backend" / "app" / "rules" / "admin_law_rules.json"
        with open(rules_path, encoding="utf-8") as f:
            data = json.load(f)
        assert "rules" in data
        assert len(data["rules"]) >= 7

    def test_rules_have_required_fields(self):
        import json
        rules_path = Path(__file__).resolve().parent.parent / "backend" / "app" / "rules" / "admin_law_rules.json"
        with open(rules_path, encoding="utf-8") as f:
            data = json.load(f)
        for rule in data["rules"]:
            assert "rule_id" in rule
            assert "rule_type" in rule
            assert "severity" in rule


# ── Database Smoke Test ─────────────────────────────────────────

class TestDatabaseSmoke:
    """Verify database can initialize."""

    def test_init_db_creates_tables(self, tmp_path):
        """Database should initialize without errors using a temp path."""
        from app.core import database
        original_path = database.DATABASE_PATH
        try:
            database.DATABASE_PATH = tmp_path / "test.db"
            database.init_db()
            assert (tmp_path / "test.db").exists()
        finally:
            database.DATABASE_PATH = original_path


# ── Root FastAPI App ────────────────────────────────────────────

class TestRootApp:
    """Verify the root FastAPI application."""

    def test_root_app_importable(self):
        import importlib
        # The root main.py defines `app`
        spec = importlib.util.spec_from_file_location("main", str(Path(__file__).resolve().parent.parent / "main.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert hasattr(mod, "app")

    def test_health_endpoint(self):
        from fastapi.testclient import TestClient
        import importlib.util
        spec = importlib.util.spec_from_file_location("main", str(Path(__file__).resolve().parent.parent / "main.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        client = TestClient(mod.app)
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
