# -*- coding: utf-8 -*-
"""
Edge Case Tests
===============
Tests for boundary conditions, error handling, and edge cases.
"""
import pytest
from app.services.case_parser import CaseParser
from app.services.evidence_chain_checker import EvidenceChainChecker
from app.services.discretion_benchmark import DiscretionBenchmark
from app.services.case_similarity_retriever import CaseSimilarityRetriever
from app.services.procedure_legal_checker import ProcedureLegalChecker
from app.services.case_risk_scorer import CaseRiskScorer
from app.services.report_generator import ReportGenerator


# ── CaseParser Edge Cases ──────────────────────────────────────

class TestCaseParserEdgeCases:
    """Edge cases for CaseParser."""

    def setup_method(self):
        self.parser = CaseParser()

    def test_empty_string(self):
        result = self.parser.parse("")
        assert isinstance(result, dict)
        assert result["node_count"] >= 0

    def test_very_long_content(self):
        long_content = "违法事实：测试内容。" * 10000
        result = self.parser.parse(long_content)
        assert isinstance(result, dict)

    def test_special_characters(self):
        content = "案件编号: @#$%^&*\n违法事实：特殊字符测试！@#"
        result = self.parser.parse(content)
        assert isinstance(result, dict)

    def test_unicode_content(self):
        content = "案件编号: UNICODE-001\n违法事实：包含emoji测试"
        result = self.parser.parse(content)
        assert isinstance(result, dict)

    def test_only_whitespace(self):
        result = self.parser.parse("   \n\t\n   ")
        assert isinstance(result, dict)

    def test_single_line(self):
        result = self.parser.parse("违法事实：单行测试内容")
        assert isinstance(result, dict)

    def test_multiple_filing_dates(self):
        content = "立案日期: 2024-01-15\n立案日期: 2024-02-20"
        result = self.parser.parse(content)
        assert isinstance(result, dict)

    def test_no_chinese_content(self):
        content = "Case number: 001\nViolation: test"
        result = self.parser.parse(content)
        assert isinstance(result, dict)


# ── EvidenceChainChecker Edge Cases ────────────────────────────

class TestEvidenceChainCheckerEdgeCases:
    """Edge cases for EvidenceChainChecker."""

    def setup_method(self):
        self.checker = EvidenceChainChecker()
        self.parser = CaseParser()

    def test_empty_content(self):
        parsed = self.parser.parse("")
        result = self.checker.check("", parsed)
        assert result["score"] < 100

    def test_content_with_no_evidence(self):
        content = "案件编号: 001\n违法事实：测试\n处罚决定：罚款"
        parsed = self.parser.parse(content)
        result = self.checker.check(content, parsed)
        assert len(result["issues"]) > 0

    def test_content_with_only_facts(self):
        content = "违法事实：当事人实施了违法行为"
        parsed = self.parser.parse(content)
        result = self.checker.check(content, parsed)
        assert isinstance(result, dict)

    def test_content_with_all_elements(self):
        content = """
        违法事实：当事人实施违法行为
        物证：现场照片
        书证：营业执照
        依据《环境保护法》第六十三条
        罚款人民币50000元
        """
        parsed = self.parser.parse(content)
        result = self.checker.check(content, parsed)
        assert result["score"] > 0

    def test_extract_facts_no_match(self):
        facts = self.checker._extract_facts("没有违法事实的内容")
        assert isinstance(facts, list)

    def test_extract_evidence_no_match(self):
        evidence = self.checker._extract_evidence("没有证据的内容")
        assert isinstance(evidence, list)

    def test_extract_legal_basis_no_match(self):
        legal = self.checker._extract_legal_basis("没有法律依据的内容")
        assert isinstance(legal, list)

    def test_extract_penalty_no_match(self):
        penalty = self.checker._extract_penalty("没有处罚的内容")
        assert isinstance(penalty, dict)


# ── DiscretionBenchmark Edge Cases ─────────────────────────────

class TestDiscretionBenchmarkEdgeCases:
    """Edge cases for DiscretionBenchmark."""

    def setup_method(self):
        self.benchmark = DiscretionBenchmark()

    def test_empty_content(self):
        result = self.benchmark.match("", {})
        assert isinstance(result, dict)

    def test_zero_penalty(self):
        result = self.benchmark.match("罚款人民币0元", {"amount": 0})
        assert isinstance(result, dict)

    def test_very_large_penalty(self):
        result = self.benchmark.match("罚款人民币999999999元", {"amount": 999999999})
        assert isinstance(result, dict)

    def test_negative_amount(self):
        result = self.benchmark.match("罚款人民币-100元", {"amount": -100})
        assert isinstance(result, dict)

    def test_no_penalty_info(self):
        result = self.benchmark.match("简单案件内容", {})
        assert isinstance(result, dict)

    def test_mismatched_penalty_type(self):
        result = self.benchmark.match("罚款", {"penalty_type": "行政拘留", "amount": 5000})
        assert isinstance(result, dict)

    def test_calculate_deviation_zero_baseline(self):
        legal = {"fixed_amount": 0}
        actual = {"amount": 100}
        deviation = self.benchmark._calculate_deviation(legal, actual, {})
        # When baseline is 0, the code may return None or 0
        assert deviation is None or isinstance(deviation, (int, float))


# ── CaseSimilarityRetriever Edge Cases ─────────────────────────

class TestCaseSimilarityRetrieverEdgeCases:
    """Edge cases for CaseSimilarityRetriever."""

    def setup_method(self):
        self.retriever = CaseSimilarityRetriever()

    def test_search_empty_corpus(self):
        results = self.retriever.search("test query")
        assert results == []

    def test_add_empty_content(self):
        self.retriever.add_case_to_corpus(1, "", "行政处罚")
        assert len(self.retriever.corpus) == 1

    def test_add_very_long_content(self):
        long_content = "测试内容 " * 10000
        self.retriever.add_case_to_corpus(1, long_content, "行政处罚")
        assert len(self.retriever.corpus) == 1

    def test_cosine_similarity_zero_vectors(self):
        vec1 = {"a": 0.0}
        vec2 = {"a": 0.0}
        result = self.retriever._cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_cosine_similarity_no_common_words(self):
        vec1 = {"a": 1.0, "b": 2.0}
        vec2 = {"c": 1.0, "d": 2.0}
        result = self.retriever._cosine_similarity(vec1, vec2)
        assert result == 0.0

    def test_extract_keywords_only_stop_words(self):
        keywords = self.retriever._extract_keywords("的 了 在 是 我")
        assert isinstance(keywords, list)

    def test_extract_keywords_mixed_language(self):
        keywords = self.retriever._extract_keywords("Hello 世界 World 测试")
        assert isinstance(keywords, list)

    def test_build_index_single_document(self):
        self.retriever.add_case_to_corpus(1, "单文档测试", "行政处罚")
        self.retriever.build_index()
        assert len(self.retriever.corpus_vectors) == 1

    def test_check_penalty_deviation_no_amount(self):
        self.retriever.add_case_to_corpus(1, "罚款人民币50000元", "行政处罚")
        result = self.retriever.check_penalty_deviation({}, [{"case_id": 1, "similarity_score": 0.8}])
        assert result["has_deviation"] is False

    def test_search_top_k_larger_than_corpus(self):
        self.retriever.add_case_to_corpus(1, "测试内容", "行政处罚")
        self.retriever.build_index()
        results = self.retriever.search("测试", top_k=100)
        assert len(results) <= 1


# ── ProcedureLegalChecker Edge Cases ──────────────────────────

class TestProcedureLegalCheckerEdgeCases:
    """Edge cases for ProcedureLegalChecker."""

    def setup_method(self):
        self.checker = ProcedureLegalChecker()
        self.parser = CaseParser()

    def test_empty_content(self):
        parsed = self.parser.parse("")
        result = self.checker.check("", parsed)
        assert isinstance(result, dict)

    def test_content_with_all_dates(self):
        content = """
        立案日期: 2024-01-01
        调查日期：2024-01-05
        告知日期：2024-01-10
        决定日期：2024-01-12
        送达日期：2024-01-15
        """
        parsed = self.parser.parse(content)
        result = self.checker.check(content, parsed)
        assert isinstance(result, dict)

    def test_parse_date_edge_formats(self):
        assert self.checker._parse_date("2024年12月31日") is not None
        assert self.checker._parse_date("2024-1-1") is not None
        assert self.checker._parse_date("2024/1/1") is not None

    def test_check_deadlines_insufficient_timeline(self):
        self.checker.timeline = []
        issues = self.checker._check_deadlines()
        assert len(issues) > 0

    def test_check_notice_with_all_elements(self):
        content = "告知书 当事人 违法事实 处罚依据 处罚内容 陈述申辩"
        issues = self.checker._check_notice_procedure(content)
        assert isinstance(issues, list)

    def test_check_signature_with_all_elements(self):
        content = "当事人 执法人员 负责人 行政机关"
        issues = self.checker._check_signature_procedure(content)
        assert isinstance(issues, list)

    def test_check_delivery_with_all_elements(self):
        content = "送达 签收"
        issues = self.checker._check_delivery_procedure(content)
        assert isinstance(issues, list)


# ── CaseRiskScorer Edge Cases ─────────────────────────────────

class TestCaseRiskScorerEdgeCases:
    """Edge cases for CaseRiskScorer."""

    def setup_method(self):
        self.scorer = CaseRiskScorer()

    def test_score_with_all_empty_results(self):
        result = self.scorer.score(
            evidence_result={},
            discretion_result={},
            procedure_result={},
            similarity_result={},
            case_content=""
        )
        assert isinstance(result, dict)

    def test_score_with_high_risk_indicators(self):
        result = self.scorer.score(
            evidence_result={
                "is_complete": False,
                "chain_completeness": {"is_complete": False, "missing_elements": ["事实", "证据"]},
                "evidence_sufficiency": {"is_sufficient": False, "evidence_count": 0, "high_priority_ratio": 0, "type_diversity": 0}
            },
            discretion_result={"deviation": 1.0, "is_abnormal": True, "match_level": "abnormal"},
            procedure_result={"score": 0, "issues": [{"type": "test", "severity": "high", "message": "test"}]},
            similarity_result={"similar_cases": []},
            case_content="短"
        )
        assert result["total_risk_score"] > 0

    def test_determine_risk_level_boundary(self):
        assert self.scorer._determine_risk_level(0) == "基本合规"
        assert self.scorer._determine_risk_level(20) == "格式问题"
        assert self.scorer._determine_risk_level(50) == "一般瑕疵"
        assert self.scorer._determine_risk_level(80) == "重大瑕疵"

    def test_calculate_format_risk_complete_content(self):
        content = "案件编号: 001\n当事人：张三\n日期：2024-01-01\n" + "内容" * 100
        result = self.scorer._calculate_format_risk(content)
        assert result["score"] >= 0

    def test_risk_summary_with_no_details(self):
        self.scorer.risk_details = {}
        summary = self.scorer._generate_risk_summary()
        assert summary["total_issues"] == 0


# ── ReportGenerator Edge Cases ────────────────────────────────

class TestReportGeneratorEdgeCases:
    """Edge cases for ReportGenerator."""

    def setup_method(self):
        self.generator = ReportGenerator()

    def test_generate_with_all_empty_inputs(self):
        report = self.generator.generate(
            case_info={}, analysis_result={}, evidence_result={},
            discretion_result={}, procedure_result={},
            similarity_result={}, risk_result={"risk_level": "未知"}
        )
        assert isinstance(report, dict)

    def test_generate_case_info_defaults(self):
        info = self.generator._generate_case_info({})
        assert info["case_number"] == "未知"
        assert info["case_type"] == "行政处罚"

    def test_generate_executive_summary_unknown_level(self):
        summary = self.generator._generate_executive_summary({"risk_level": "未知", "total_risk_score": 0})
        assert "summary" in summary

    def test_generate_conclusion_unknown_level(self):
        conclusion = self.generator._generate_conclusion({"risk_level": "未知"})
        assert conclusion["verdict"] == "待评定"

    def test_generate_issues_list_with_mixed_issues(self):
        evidence_result = {"issues": [{"type": "test", "severity": "high", "message": "test"}]}
        discretion_result = {"issues": [{"type": "test", "severity": "medium", "message": "test"}]}
        procedure_result = {"issues": [{"type": "test", "severity": "low", "message": "test"}]}
        risk_result = {"risk_summary": {"major_issues": []}}
        issues = self.generator._generate_issues_list(evidence_result, discretion_result, procedure_result, risk_result)
        assert len(issues) >= 3

    def test_generate_responsibility_nodes(self):
        evidence_result = {"issues": [{"type": "evidence_missing", "severity": "high"}]}
        discretion_result = {"issues": []}
        procedure_result = {"issues": []}
        nodes = self.generator._generate_responsibility_nodes(evidence_result, discretion_result, procedure_result)
        assert isinstance(nodes, list)

    def test_generate_rectification_suggestions_format_issue(self):
        suggestions = self.generator._generate_rectification_suggestions(
            {"issues": []}, {"is_abnormal": False}, {"is_legal": True},
            {"risk_level": "格式问题"}
        )
        assert len(suggestions) > 0

    def test_report_id_uniqueness(self):
        import time
        report1 = self.generator.generate(
            case_info={}, analysis_result={}, evidence_result={},
            discretion_result={}, procedure_result={},
            similarity_result={}, risk_result={"risk_level": "基本合规"}
        )
        time.sleep(1)
        report2 = self.generator.generate(
            case_info={}, analysis_result={}, evidence_result={},
            discretion_result={}, procedure_result={},
            similarity_result={}, risk_result={"risk_level": "基本合规"}
        )
        assert report1["report_id"] != report2["report_id"]


# ── Database Edge Cases ───────────────────────────────────────

class TestDatabaseEdgeCases:
    """Edge cases for database operations."""

    def test_init_db_twice(self, tmp_path):
        """Should handle double initialization."""
        from app.core import database
        original_path = database.DATABASE_PATH
        try:
            db_path = tmp_path / "test.db"
            database.DATABASE_PATH = db_path
            database.init_db()
            database.init_db()  # Second init should not fail
            assert db_path.exists()
        finally:
            database.DATABASE_PATH = original_path

    def test_log_audit(self, tmp_path):
        """Should log audit entries."""
        from app.core import database
        original_path = database.DATABASE_PATH
        try:
            db_path = tmp_path / "test.db"
            database.DATABASE_PATH = db_path
            database.init_db()
            database.log_audit("test_action", "test_type", 1, "test details")
            conn = database.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM audit_logs WHERE action = ?", ("test_action",))
            log = cursor.fetchone()
            conn.close()
            assert log is not None
        finally:
            database.DATABASE_PATH = original_path


# ── Schema Validation Edge Cases ──────────────────────────────

class TestSchemaEdgeCases:
    """Edge cases for Pydantic schemas."""

    def test_case_upload_request(self):
        from app.models.schemas import CaseUploadRequest
        req = CaseUploadRequest(case_number="001", case_type="行政处罚", content="test")
        assert req.case_number == "001"

    def test_case_upload_request_with_optional(self):
        from app.models.schemas import CaseUploadRequest
        req = CaseUploadRequest(case_number="001", case_type="行政处罚", content="test", filing_date="2024-01-01")
        assert req.filing_date == "2024-01-01"

    def test_health_response(self):
        from app.models.schemas import HealthResponse
        resp = HealthResponse(status="ok", timestamp="2024-01-01")
        assert resp.status == "ok"
        assert resp.version == "1.0.0"

    def test_evidence_record_request(self):
        from app.models.schemas import EvidenceRecordRequest
        req = EvidenceRecordRequest(case_id=1, evidence_type="物证", content="test")
        assert req.case_id == 1

    def test_penalty_record_request(self):
        from app.models.schemas import PenaltyRecordRequest
        req = PenaltyRecordRequest(case_id=1, penalty_type="罚款", amount=50000)
        assert req.amount == 50000
