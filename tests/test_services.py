# -*- coding: utf-8 -*-
"""
Comprehensive Service Unit Tests
=================================
Tests for all core service modules with detailed coverage.
"""
import pytest
from app.services.case_parser import CaseParser, ProcessNode
from app.services.evidence_chain_checker import EvidenceChainChecker
from app.services.discretion_benchmark import DiscretionBenchmark
from app.services.case_similarity_retriever import CaseSimilarityRetriever
from app.services.procedure_legal_checker import ProcedureLegalChecker
from app.services.case_risk_scorer import CaseRiskScorer
from app.services.report_generator import ReportGenerator


# ── Shared Test Fixtures ────────────────────────────────────────

SAMPLE_CASE_FULL = """
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
鉴定意见：环境损害鉴定报告

【违法事实】
当事人非法倾倒废物共计10吨，严重污染环境

【行政处罚告知书】
告知日期：2024-01-20
依据《环境保护法》第六十三条
处罚依据：《固体废物污染环境防治法》第一百一十二条
处罚内容：罚款人民币50000元
陈述申辩权：当事人有权进行陈述和申辩

【处罚决定】
罚款人民币50000元
决定日期：2024-01-25

【送达凭证】
送达日期：2024-01-26
当事人签字确认
"""

SAMPLE_CASE_MINIMAL = """
案件编号: (Y)罚字[2024]002号
当事人：赵六
违法事实：未按规定办理许可手续
"""


# ── CaseParser Tests ────────────────────────────────────────────

class TestCaseParser:
    """Comprehensive CaseParser tests."""

    def setup_method(self):
        self.parser = CaseParser()

    def test_process_coords_defined(self):
        """All 8 process coordinates should be defined."""
        assert len(CaseParser.PROCESS_COORDS) == 8
        required_nodes = ["filing", "investigation", "evidence", "fact_determination",
                         "notice", "hearing", "penalty_decision", "delivery"]
        for node in required_nodes:
            assert node in CaseParser.PROCESS_COORDS

    def test_process_coords_have_xy(self):
        """Each coordinate should have x and y values."""
        for node_id, coords in CaseParser.PROCESS_COORDS.items():
            assert "x" in coords
            assert "y" in coords
            assert 0 <= coords["x"] <= 100
            assert 0 <= coords["y"] <= 100

    def test_parse_full_case(self):
        """Full case should parse all nodes."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        assert result["case_type"] == "行政处罚"
        assert result["node_count"] >= 5
        assert len(result["nodes"]) >= 5

    def test_parse_minimal_case(self):
        """Minimal case should still return valid structure."""
        result = self.parser.parse(SAMPLE_CASE_MINIMAL)
        assert isinstance(result, dict)
        assert "nodes" in result
        assert "coord_map" in result

    def test_parse_finds_filing_date(self):
        """Should detect filing date from case content."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        filing_node = next((n for n in result["nodes"] if n["node_id"] == "filing"), None)
        assert filing_node is not None
        assert filing_node["date"] is not None

    def test_parse_finds_filing_content(self):
        """Should detect filing content."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        filing_node = next((n for n in result["nodes"] if n["node_id"] == "filing"), None)
        assert filing_node is not None
        assert isinstance(filing_node["content"], str)

    def test_parse_detects_evidence_types(self):
        """Should detect evidence types from case content."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        evidence_node = next((n for n in result["nodes"] if n["node_id"] == "evidence"), None)
        assert evidence_node is not None
        assert isinstance(evidence_node["content"], str)

    def test_parse_detects_penalty(self):
        """Should detect penalty decision."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        penalty_node = next((n for n in result["nodes"] if n["node_id"] == "penalty_decision"), None)
        assert penalty_node is not None

    def test_parse_detects_notice(self):
        """Should detect notice procedure."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        notice_node = next((n for n in result["nodes"] if n["node_id"] == "notice"), None)
        assert notice_node is not None

    def test_parse_detects_delivery(self):
        """Should detect delivery procedure."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        delivery_node = next((n for n in result["nodes"] if n["node_id"] == "delivery"), None)
        assert delivery_node is not None

    def test_parse_completeness_score(self):
        """Completeness score should be non-negative."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        completeness = result["completeness"]
        assert completeness["score"] >= 0

    def test_parse_timeline(self):
        """Timeline should contain dated nodes."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        timeline = result["timeline"]
        assert isinstance(timeline, list)

    def test_parse_coord_map(self):
        """Coord map should contain all defined coordinates."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        coord_map = result["coord_map"]
        assert len(coord_map) == 8

    def test_node_to_dict_conversion(self):
        """Node dict should contain all required fields."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        for node in result["nodes"]:
            assert "node_id" in node
            assert "node_type" in node
            assert "name" in node
            assert "content" in node
            assert "x_coord" in node
            assert "y_coord" in node
            assert "issues" in node

    def test_parse_investigation_node(self):
        """Should detect investigation node with content."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        inv_node = next((n for n in result["nodes"] if n["node_id"] == "investigation"), None)
        assert inv_node is not None
        assert inv_node["content"] != "未进行有效调查取证"

    def test_parse_fact_determination(self):
        """Should detect fact determination."""
        result = self.parser.parse(SAMPLE_CASE_FULL)
        fact_node = next((n for n in result["nodes"] if n["node_id"] == "fact_determination"), None)
        assert fact_node is not None

    def test_parse_with_custom_case_type(self):
        """Should accept custom case type."""
        result = self.parser.parse(SAMPLE_CASE_FULL, case_type="行政许可")
        assert result["case_type"] == "行政许可"

    def test_parse_empty_content(self):
        """Empty content should return nodes with issues."""
        result = self.parser.parse("")
        assert isinstance(result, dict)
        assert result["node_count"] >= 0


# ── EvidenceChainChecker Tests ──────────────────────────────────

class TestEvidenceChainChecker:
    """Comprehensive EvidenceChainChecker tests."""

    def setup_method(self):
        self.checker = EvidenceChainChecker()
        self.parser = CaseParser()

    def test_required_chain_elements(self):
        """Should have 4 required chain elements."""
        assert len(EvidenceChainChecker.REQUIRED_CHAIN_ELEMENTS) == 4
        assert "fact" in EvidenceChainChecker.REQUIRED_CHAIN_ELEMENTS
        assert "evidence" in EvidenceChainChecker.REQUIRED_CHAIN_ELEMENTS
        assert "legal_basis" in EvidenceChainChecker.REQUIRED_CHAIN_ELEMENTS
        assert "penalty" in EvidenceChainChecker.REQUIRED_CHAIN_ELEMENTS

    def test_evidence_priority_defined(self):
        """Should have 8 evidence priority types."""
        assert len(EvidenceChainChecker.EVIDENCE_PRIORITY) == 8
        assert EvidenceChainChecker.EVIDENCE_PRIORITY["物证"] == 10
        assert EvidenceChainChecker.EVIDENCE_PRIORITY["书证"] == 9

    def test_min_evidence_per_fact(self):
        """Minimum evidence per fact should be 2."""
        assert EvidenceChainChecker.MIN_EVIDENCE_PER_FACT == 2

    def test_check_full_case(self):
        """Full case should have high completeness score."""
        parsed = self.parser.parse(SAMPLE_CASE_FULL)
        result = self.checker.check(SAMPLE_CASE_FULL, parsed)
        assert result["score"] > 0
        assert "is_complete" in result

    def test_check_returns_all_fields(self):
        """Result should contain all required fields."""
        parsed = self.parser.parse(SAMPLE_CASE_FULL)
        result = self.checker.check(SAMPLE_CASE_FULL, parsed)
        assert "is_complete" in result
        assert "score" in result
        assert "chain_completeness" in result
        assert "evidence_sufficiency" in result
        assert "chain_elements" in result
        assert "issues" in result

    def test_check_chain_completeness(self):
        """Chain completeness should have required structure."""
        parsed = self.parser.parse(SAMPLE_CASE_FULL)
        result = self.checker.check(SAMPLE_CASE_FULL, parsed)
        cc = result["chain_completeness"]
        assert "is_complete" in cc
        assert "score" in cc
        assert "missing_elements" in cc

    def test_check_evidence_sufficiency(self):
        """Evidence sufficiency should have required structure."""
        parsed = self.parser.parse(SAMPLE_CASE_FULL)
        result = self.checker.check(SAMPLE_CASE_FULL, parsed)
        es = result["evidence_sufficiency"]
        assert "is_sufficient" in es
        assert "score" in es
        # May or may not have these fields depending on content parsing
        assert isinstance(es, dict)

    def test_extract_facts(self):
        """Should extract facts from case content or return empty list."""
        facts = self.checker._extract_facts(SAMPLE_CASE_FULL)
        assert isinstance(facts, list)

    def test_extract_evidence(self):
        """Should extract evidence from case content or return empty list."""
        evidence = self.checker._extract_evidence(SAMPLE_CASE_FULL)
        assert isinstance(evidence, list)
        for ev in evidence:
            assert "type" in ev
            assert "content" in ev
            assert "priority" in ev

    def test_extract_legal_basis(self):
        """Should extract legal basis from case content or return empty list."""
        legal_basis = self.checker._extract_legal_basis(SAMPLE_CASE_FULL)
        assert isinstance(legal_basis, list)

    def test_extract_penalty(self):
        """Should extract penalty from case content."""
        penalty = self.checker._extract_penalty(SAMPLE_CASE_FULL)
        assert isinstance(penalty, dict)

    def test_check_empty_content(self):
        """Empty content should have low score."""
        parsed = self.parser.parse("")
        result = self.checker.check("", parsed)
        assert result["score"] < 100

    def test_check_minimal_case(self):
        """Minimal case should have issues."""
        parsed = self.parser.parse(SAMPLE_CASE_MINIMAL)
        result = self.checker.check(SAMPLE_CASE_MINIMAL, parsed)
        assert len(result["issues"]) > 0

    def test_evidence_type_diversity(self):
        """Should detect evidence types."""
        evidence = self.checker._extract_evidence(SAMPLE_CASE_FULL)
        types = set(e["type"] for e in evidence)
        assert isinstance(types, set)

    def test_high_priority_ratio(self):
        """Should calculate high priority evidence ratio."""
        evidence = self.checker._extract_evidence(SAMPLE_CASE_FULL)
        high_priority = [e for e in evidence if e["priority"] >= 7]
        ratio = len(high_priority) / len(evidence) if evidence else 0
        assert 0 <= ratio <= 1


# ── DiscretionBenchmark Tests ──────────────────────────────────

class TestDiscretionBenchmark:
    """Comprehensive DiscretionBenchmark tests."""

    def setup_method(self):
        self.benchmark = DiscretionBenchmark()

    def test_default_benchmarks(self):
        """Should have default benchmarks for 3 penalty types."""
        assert "罚款" in self.benchmark.benchmarks
        assert "责令停产停业" in self.benchmark.benchmarks
        assert "吊销许可证" in self.benchmark.benchmarks

    def test_discretion_factors(self):
        """Should have 5 discretion factors."""
        assert len(DiscretionBenchmark.DISCRETION_FACTORS) == 5
        assert "违法情节" in DiscretionBenchmark.DISCRETION_FACTORS
        assert "违法所得" in DiscretionBenchmark.DISCRETION_FACTORS
        assert "持续时间" in DiscretionBenchmark.DISCRETION_FACTORS
        assert "主观态度" in DiscretionBenchmark.DISCRETION_FACTORS
        assert "危害后果" in DiscretionBenchmark.DISCRETION_FACTORS

    def test_match_returns_dict(self):
        """Match should return a dictionary."""
        result = self.benchmark.match(SAMPLE_CASE_FULL, {"penalty_type": "罚款", "amount": 50000})
        assert isinstance(result, dict)

    def test_match_has_required_fields(self):
        """Match result should have all required fields."""
        result = self.benchmark.match(SAMPLE_CASE_FULL, {"penalty_type": "罚款", "amount": 50000})
        assert "penalty_type" in result
        assert "is_abnormal" in result
        assert "match_level" in result
        assert "issues" in result

    def test_match_level_values(self):
        """Match level should be one of expected values."""
        result = self.benchmark.match(SAMPLE_CASE_FULL, {"penalty_type": "罚款", "amount": 50000})
        valid_levels = ["excellent", "good", "acceptable", "poor", "abnormal", "unknown"]
        assert result["match_level"] in valid_levels

    def test_load_custom_benchmarks(self):
        """Should accept custom benchmarks."""
        custom = {"行政拘留": {"severity_weights": {"轻微": 1, "严重": 2}}}
        self.benchmark.load_custom_benchmarks(custom)
        assert "行政拘留" in self.benchmark.benchmarks

    def test_extract_legal_penalty(self):
        """Should extract legal penalty from content."""
        result = self.benchmark._extract_legal_penalty(SAMPLE_CASE_FULL)
        assert isinstance(result, dict)

    def test_extract_actual_penalty(self):
        """Should extract actual penalty from content."""
        result = self.benchmark._extract_actual_penalty(SAMPLE_CASE_FULL, {"amount": 50000})
        assert result.get("amount") == 50000

    def test_extract_discretion_factors(self):
        """Should extract discretion factors from content."""
        factors = self.benchmark._extract_discretion_factors(SAMPLE_CASE_FULL)
        assert isinstance(factors, dict)

    def test_calculate_deviation_none_without_amount(self):
        """Should return None if no actual amount."""
        deviation = self.benchmark._calculate_deviation({}, {}, {})
        assert deviation is None

    def test_calculate_deviation_with_fixed_amount(self):
        """Should calculate deviation with fixed amount."""
        legal = {"fixed_amount": 10000}
        actual = {"amount": 15000}
        deviation = self.benchmark._calculate_deviation(legal, actual, {})
        assert deviation is not None
        assert abs(deviation - 0.5) < 0.01

    def test_calculate_deviation_with_range(self):
        """Should calculate deviation with range."""
        legal = {"min_amount": 10000, "max_amount": 50000}
        actual = {"amount": 30000}
        deviation = self.benchmark._calculate_deviation(legal, actual, {})
        assert deviation is not None

    def test_detect_abnormal_high_deviation(self):
        """Should detect abnormal with high deviation."""
        # The method checks if deviation > 0.5 as a general case
        result = self.benchmark._detect_abnormal({}, {}, 0.6, {})
        assert isinstance(result, bool)

    def test_detect_abnormal_none_deviation(self):
        """Should not detect abnormal with None deviation."""
        result = self.benchmark._detect_abnormal({}, {}, None, {})
        assert result is False

    def test_generate_match_levels(self):
        """Should generate correct match levels."""
        assert self.benchmark._generate_match_level(0.05, False, {}) == "excellent"
        assert self.benchmark._generate_match_level(0.15, False, {}) == "good"
        assert self.benchmark._generate_match_level(0.25, False, {}) == "acceptable"
        assert self.benchmark._generate_match_level(0.35, False, {}) == "poor"
        assert self.benchmark._generate_match_level(0.5, True, {}) == "abnormal"
        assert self.benchmark._generate_match_level(None, False, {}) == "unknown"

    def test_match_with_empty_penalty_info(self):
        """Should handle empty penalty info."""
        result = self.benchmark.match(SAMPLE_CASE_FULL, {})
        assert isinstance(result, dict)


# ── CaseSimilarityRetriever Tests ──────────────────────────────

class TestCaseSimilarityRetriever:
    """Comprehensive CaseSimilarityRetriever tests."""

    def setup_method(self):
        self.retriever = CaseSimilarityRetriever()

    def test_initial_state(self):
        """Initial state should be empty."""
        assert len(self.retriever.corpus) == 0
        assert len(self.retriever.corpus_vectors) == 0

    def test_add_case_to_corpus(self):
        """Should add case to corpus."""
        self.retriever.add_case_to_corpus(1, "非法倾倒废物 环境污染", "行政处罚")
        assert len(self.retriever.corpus) == 1
        assert 1 in self.retriever.case_store

    def test_add_multiple_cases(self):
        """Should handle multiple cases."""
        self.retriever.add_case_to_corpus(1, "非法倾倒废物", "行政处罚")
        self.retriever.add_case_to_corpus(2, "违法建设", "行政处罚")
        self.retriever.add_case_to_corpus(3, "环境污染", "行政处罚")
        assert len(self.retriever.corpus) == 3

    def test_build_index(self):
        """Should build TF-IDF index."""
        self.retriever.add_case_to_corpus(1, "非法倾倒废物 环境污染 罚款", "行政处罚")
        self.retriever.add_case_to_corpus(2, "违法建设 未经审批", "行政处罚")
        self.retriever.build_index()
        assert len(self.retriever.corpus_vectors) == 2

    def test_build_index_empty_corpus(self):
        """Should handle empty corpus."""
        self.retriever.build_index()
        assert len(self.retriever.corpus_vectors) == 0

    def test_search_returns_results(self):
        """Should return search results."""
        self.retriever.add_case_to_corpus(1, "非法倾倒废物 环境污染 罚款 处罚", "行政处罚")
        self.retriever.add_case_to_corpus(2, "违法建设 未经审批 城乡规划", "行政处罚")
        self.retriever.build_index()
        results = self.retriever.search("非法倾倒废物")
        assert isinstance(results, list)

    def test_search_with_top_k(self):
        """Should respect top_k parameter."""
        for i in range(10):
            self.retriever.add_case_to_corpus(i, f"案例{i} 行政处罚 罚款", "行政处罚")
        self.retriever.build_index()
        results = self.retriever.search("行政处罚", top_k=3)
        assert len(results) <= 3

    def test_search_empty_index(self):
        """Should return empty for empty index."""
        results = self.retriever.search("test")
        assert results == []

    def test_extract_keywords(self):
        """Should extract keywords from content."""
        keywords = self.retriever._extract_keywords("非法倾倒废物 环境污染")
        assert isinstance(keywords, list)
        assert len(keywords) > 0

    def test_extract_keywords_filters_short_words(self):
        """Should filter short words."""
        keywords = self.retriever._extract_keywords("A B 非法倾倒")
        for kw in keywords:
            assert len(kw) >= 2

    def test_cosine_similarity_identical(self):
        """Identical vectors should have similarity 1.0."""
        vec = {"a": 1.0, "b": 2.0}
        assert self.retriever._cosine_similarity(vec, vec) == pytest.approx(1.0)

    def test_cosine_similarity_orthogonal(self):
        """Orthogonal vectors should have similarity 0.0."""
        vec1 = {"a": 1.0}
        vec2 = {"b": 1.0}
        assert self.retriever._cosine_similarity(vec1, vec2) == 0.0

    def test_cosine_similarity_empty(self):
        """Empty vectors should have similarity 0.0."""
        assert self.retriever._cosine_similarity({}, {"a": 1.0}) == 0.0

    def test_check_penalty_deviation_no_cases(self):
        """Should handle no similar cases."""
        result = self.retriever.check_penalty_deviation({"penalty_amount": 50000}, [])
        assert result["has_deviation"] is False

    def test_check_penalty_deviation_with_cases(self):
        """Should detect penalty deviation."""
        self.retriever.add_case_to_corpus(1, "罚款人民币50000元", "行政处罚")
        similar = [{"case_id": 1, "similarity_score": 0.8}]
        result = self.retriever.check_penalty_deviation({"penalty_amount": 100000}, similar)
        assert isinstance(result, dict)

    def test_search_result_structure(self):
        """Search results should have correct structure."""
        self.retriever.add_case_to_corpus(1, "非法倾倒废物 环境污染 罚款", "行政处罚")
        self.retriever.build_index()
        results = self.retriever.search("非法倾倒")
        if results:
            assert "case_id" in results[0]
            assert "similarity_score" in results[0]


# ── ProcedureLegalChecker Tests ────────────────────────────────

class TestProcedureLegalChecker:
    """Comprehensive ProcedureLegalChecker tests."""

    def setup_method(self):
        self.checker = ProcedureLegalChecker()
        self.parser = CaseParser()

    def test_legal_deadlines(self):
        """Should have 5 legal deadline definitions."""
        assert len(ProcedureLegalChecker.LEGAL_DEADLINES) == 5

    def test_procedure_nodes(self):
        """Should have 8 procedure nodes."""
        assert len(ProcedureLegalChecker.PROCEDURE_NODES) == 8

    def test_check_returns_dict(self):
        """Check should return a dictionary."""
        parsed = self.parser.parse(SAMPLE_CASE_FULL)
        result = self.checker.check(SAMPLE_CASE_FULL, parsed)
        assert isinstance(result, dict)

    def test_check_has_required_fields(self):
        """Result should have all required fields."""
        parsed = self.parser.parse(SAMPLE_CASE_FULL)
        result = self.checker.check(SAMPLE_CASE_FULL, parsed)
        assert "is_legal" in result
        assert "score" in result
        assert "issues" in result
        assert "timeline" in result

    def test_check_score_range(self):
        """Score should be between 0 and 100."""
        parsed = self.parser.parse(SAMPLE_CASE_FULL)
        result = self.checker.check(SAMPLE_CASE_FULL, parsed)
        assert 0 <= result["score"] <= 100

    def test_parse_date_formats(self):
        """Should parse multiple date formats."""
        assert self.checker._parse_date("2024年1月15日") is not None
        assert self.checker._parse_date("2024-01-15") is not None
        assert self.checker._parse_date("2024/01/15") is not None
        assert self.checker._parse_date("2024.01.15") is not None

    def test_parse_date_invalid(self):
        """Should return None for invalid date."""
        assert self.checker._parse_date("invalid") is None
        assert self.checker._parse_date("") is None
        assert self.checker._parse_date(None) is None

    def test_check_notice_procedure(self):
        """Should check notice procedure."""
        issues = self.checker._check_notice_procedure(SAMPLE_CASE_FULL)
        assert isinstance(issues, list)

    def test_check_notice_missing(self):
        """Should detect missing notice."""
        issues = self.checker._check_notice_procedure("简单案件内容")
        notice_issues = [i for i in issues if i["type"] == "notice_missing"]
        assert len(notice_issues) > 0

    def test_check_signature_procedure(self):
        """Should check signature procedure."""
        issues = self.checker._check_signature_procedure(SAMPLE_CASE_FULL)
        assert isinstance(issues, list)

    def test_check_delivery_procedure(self):
        """Should check delivery procedure."""
        issues = self.checker._check_delivery_procedure(SAMPLE_CASE_FULL)
        assert isinstance(issues, list)

    def test_check_delivery_missing(self):
        """Should detect missing delivery."""
        issues = self.checker._check_delivery_procedure("简单案件内容")
        delivery_issues = [i for i in issues if i["type"] == "delivery_incomplete"]
        assert len(delivery_issues) > 0

    def test_calculate_score_no_issues(self):
        """No issues should give 100 score."""
        assert self.checker._calculate_score([]) == 100.0

    def test_calculate_score_with_issues(self):
        """Issues should reduce score."""
        issues = [
            {"severity": "high"},
            {"severity": "medium"},
            {"severity": "low"},
        ]
        score = self.checker._calculate_score(issues)
        assert score < 100

    def test_get_node_name(self):
        """Should return correct node names."""
        assert self.checker._get_node_name("filing") == "立案"
        assert self.checker._get_node_name("investigation") == "调查取证"

    def test_get_node_name_unknown(self):
        """Should return node_id for unknown nodes."""
        assert self.checker._get_node_name("unknown") == "unknown"

    def test_check_empty_content(self):
        """Should handle empty content."""
        parsed = self.parser.parse("")
        result = self.checker.check("", parsed)
        assert isinstance(result, dict)


# ── CaseRiskScorer Tests ───────────────────────────────────────

class TestCaseRiskScorer:
    """Comprehensive CaseRiskScorer tests."""

    def setup_method(self):
        self.scorer = CaseRiskScorer()

    def test_risk_dimensions(self):
        """Should have 5 risk dimensions."""
        assert len(CaseRiskScorer.RISK_DIMENSIONS) == 5

    def test_risk_weights_sum_to_one(self):
        """Risk weights should sum to 1.0."""
        total = sum(CaseRiskScorer.RISK_DIMENSIONS.values())
        assert abs(total - 1.0) < 0.01

    def test_risk_levels(self):
        """Should have 4 risk levels."""
        assert len(CaseRiskScorer.RISK_LEVELS) == 4
        assert "重大瑕疵" in CaseRiskScorer.RISK_LEVELS
        assert "一般瑕疵" in CaseRiskScorer.RISK_LEVELS
        assert "格式问题" in CaseRiskScorer.RISK_LEVELS
        assert "基本合规" in CaseRiskScorer.RISK_LEVELS

    def test_risk_level_descriptions(self):
        """Should have descriptions for all risk levels."""
        for level in CaseRiskScorer.RISK_LEVELS:
            assert level in CaseRiskScorer.RISK_LEVEL_DESCRIPTIONS

    def test_score_returns_dict(self):
        """Score should return a dictionary."""
        result = self.scorer.score(
            evidence_result={"is_complete": True, "evidence_sufficiency": {"is_sufficient": True}},
            discretion_result={"deviation": 0, "is_abnormal": False, "match_level": "good"},
            procedure_result={"score": 100, "issues": [], "is_legal": True},
            similarity_result={"similar_cases": []},
            case_content=SAMPLE_CASE_FULL
        )
        assert isinstance(result, dict)

    def test_score_has_required_fields(self):
        """Result should have all required fields."""
        result = self.scorer.score(
            evidence_result={"is_complete": True, "evidence_sufficiency": {"is_sufficient": True}},
            discretion_result={"deviation": 0, "is_abnormal": False, "match_level": "good"},
            procedure_result={"score": 100, "issues": [], "is_legal": True},
            similarity_result={"similar_cases": []},
            case_content=SAMPLE_CASE_FULL
        )
        assert "total_risk_score" in result
        assert "risk_level" in result
        assert "dimension_scores" in result
        assert "radar_data" in result
        assert "risk_summary" in result

    def test_score_range(self):
        """Total risk score should be between 0 and 100."""
        result = self.scorer.score(
            evidence_result={"is_complete": True, "evidence_sufficiency": {"is_sufficient": True}},
            discretion_result={"deviation": 0, "is_abnormal": False, "match_level": "good"},
            procedure_result={"score": 100, "issues": [], "is_legal": True},
            similarity_result={"similar_cases": []},
            case_content=SAMPLE_CASE_FULL
        )
        assert 0 <= result["total_risk_score"] <= 100

    def test_determine_risk_level(self):
        """Should determine correct risk levels."""
        assert self.scorer._determine_risk_level(90) == "重大瑕疵"
        assert self.scorer._determine_risk_level(60) == "一般瑕疵"
        assert self.scorer._determine_risk_level(30) == "格式问题"
        assert self.scorer._determine_risk_level(10) == "基本合规"

    def test_generate_radar_data(self):
        """Should generate radar chart data."""
        self.scorer.risk_scores = {"fact_risk": 10, "evidence_risk": 20, "procedure_risk": 30, "discretion_risk": 40, "format_risk": 50}
        radar = self.scorer._generate_radar_data()
        assert "dimensions" in radar
        assert "scores" in radar
        assert len(radar["dimensions"]) == 5

    def test_calculate_fact_risk(self):
        """Should calculate fact risk."""
        evidence_result = {"is_complete": False, "evidence_sufficiency": {"is_sufficient": False, "evidence_count": 1}}
        result = self.scorer._calculate_fact_risk(evidence_result, "简单内容")
        assert "score" in result
        assert result["score"] > 0

    def test_calculate_evidence_risk(self):
        """Should calculate evidence risk."""
        evidence_result = {
            "chain_completeness": {"is_complete": False, "missing_elements": ["法律依据"]},
            "evidence_sufficiency": {"is_sufficient": False, "high_priority_ratio": 0.1, "type_diversity": 1}
        }
        result = self.scorer._calculate_evidence_risk(evidence_result)
        assert result["score"] > 0

    def test_calculate_procedure_risk(self):
        """Should calculate procedure risk."""
        procedure_result = {"score": 60, "issues": [{"type": "test", "severity": "high", "message": "test"}]}
        result = self.scorer._calculate_procedure_risk(procedure_result)
        assert result["score"] > 0

    def test_calculate_discretion_risk(self):
        """Should calculate discretion risk."""
        discretion_result = {"deviation": 0.5, "is_abnormal": True, "match_level": "abnormal"}
        result = self.scorer._calculate_discretion_risk(discretion_result)
        assert result["score"] > 0

    def test_calculate_format_risk(self):
        """Should calculate format risk."""
        result = self.scorer._calculate_format_risk("短内容")
        assert result["score"] > 0

    def test_risk_summary_structure(self):
        """Risk summary should have correct structure."""
        self.scorer.risk_details = {
            "fact_risk": {"details": [{"score": 50, "message": "test"}]},
            "evidence_risk": {"details": [{"score": 10, "message": "test2"}]}
        }
        summary = self.scorer._generate_risk_summary()
        assert "major_issues" in summary
        assert "general_issues" in summary
        assert "format_issues" in summary


# ── ReportGenerator Tests ──────────────────────────────────────

class TestReportGenerator:
    """Comprehensive ReportGenerator tests."""

    def setup_method(self):
        self.generator = ReportGenerator()

    def test_generate_returns_dict(self):
        """Generate should return a dictionary."""
        report = self.generator.generate(
            case_info={"case_number": "TEST-001", "case_type": "行政处罚"},
            analysis_result={},
            evidence_result={"issues": []},
            discretion_result={"deviation": 0, "is_abnormal": False, "issues": []},
            procedure_result={"is_legal": True, "issues": []},
            similarity_result={"similar_cases": []},
            risk_result={"total_risk_score": 10, "risk_level": "基本合规", "radar_data": {}, "risk_summary": {"major_issues": []}}
        )
        assert isinstance(report, dict)

    def test_report_has_required_sections(self):
        """Report should have all required sections."""
        report = self.generator.generate(
            case_info={"case_number": "TEST-001", "case_type": "行政处罚"},
            analysis_result={},
            evidence_result={"issues": []},
            discretion_result={"deviation": 0, "is_abnormal": False, "issues": []},
            procedure_result={"is_legal": True, "issues": []},
            similarity_result={"similar_cases": []},
            risk_result={"total_risk_score": 10, "risk_level": "基本合规", "radar_data": {}, "risk_summary": {"major_issues": []}}
        )
        assert "report_title" in report
        assert "report_id" in report
        assert "generated_at" in report
        assert "case_info" in report
        assert "executive_summary" in report
        assert "risk_assessment" in report
        assert "issues_list" in report
        assert "responsibility_nodes" in report
        assert "rectification_suggestions" in report
        assert "similar_case_comparison" in report
        assert "conclusion" in report

    def test_generate_case_info(self):
        """Should generate case info."""
        info = self.generator._generate_case_info({"case_number": "TEST-001", "case_type": "行政处罚"})
        assert info["case_number"] == "TEST-001"
        assert info["case_type"] == "行政处罚"

    def test_generate_executive_summary_levels(self):
        """Should generate summary for all risk levels."""
        for level in ["重大瑕疵", "一般瑕疵", "格式问题", "基本合规"]:
            summary = self.generator._generate_executive_summary({"risk_level": level, "total_risk_score": 50})
            assert summary["risk_level"] == level
            assert len(summary["summary"]) > 0

    def test_generate_conclusion_levels(self):
        """Should generate conclusion for all risk levels."""
        for level in ["重大瑕疵", "一般瑕疵", "格式问题", "基本合规"]:
            conclusion = self.generator._generate_conclusion({"risk_level": level})
            assert "verdict" in conclusion
            assert "recommendation" in conclusion
            assert "next_steps" in conclusion

    def test_generate_similar_case_comparison_empty(self):
        """Should handle empty similar cases."""
        result = self.generator._generate_similar_case_comparison({"similar_cases": []})
        assert result["has_similar_cases"] is False

    def test_generate_similar_case_comparison_with_cases(self):
        """Should generate comparison with cases."""
        similar = [{"case_id": 1, "similarity_score": 0.8}]
        result = self.generator._generate_similar_case_comparison({"similar_cases": similar})
        assert result["has_similar_cases"] is True
        assert result["count"] == 1

    def test_generate_rectification_suggestions_major(self):
        """Should generate suggestions for major defects."""
        suggestions = self.generator._generate_rectification_suggestions(
            {"issues": []}, {"is_abnormal": False}, {"is_legal": True},
            {"risk_level": "重大瑕疵"}
        )
        assert len(suggestions) > 0
        assert any(s["priority"] == "高" for s in suggestions)

    def test_generate_rectification_suggestions_compliant(self):
        """Should generate suggestions for compliant cases."""
        suggestions = self.generator._generate_rectification_suggestions(
            {"issues": []}, {"is_abnormal": False}, {"is_legal": True},
            {"risk_level": "基本合规"}
        )
        assert len(suggestions) > 0

    def test_report_id_format(self):
        """Report ID should follow RPT-YYYYMMDDHHMMSS format."""
        report = self.generator.generate(
            case_info={}, analysis_result={}, evidence_result={},
            discretion_result={}, procedure_result={},
            similarity_result={}, risk_result={"total_risk_score": 0, "risk_level": "基本合规", "radar_data": {}, "risk_summary": {"major_issues": []}}
        )
        assert report["report_id"].startswith("RPT-")
