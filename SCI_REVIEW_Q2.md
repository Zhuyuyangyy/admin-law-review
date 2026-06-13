# SCI Q2 Review: admin-law-review

**Project:** 行政执法案卷合规评查系统 (Administrative Law Case Compliance Review System)
**Review Date:** 2026-05-29
**Reviewer:** AI Code Review Agent
**Scope:** Full codebase -- 10 core Python modules, 1 JSON rule config, API layer, DB layer

---

## 1. Seven-Dimension Scoring

| # | Dimension | Score (0-10) | Rationale |
|---|-----------|:---:|-----------|
| D1 | **Architecture & Modularity** | 7.5 | Clean 4-layer separation (api / services / models / core). 6 domain services each encapsulate one concern. Dedicated rule engine JSON. Weakness: no dependency injection framework; service wiring is manual in routes.py. |
| D2 | **Code Correctness & Robustness** | 5.0 | Multiple correctness defects (see Top 3 below). DB connections leak on exception paths. Regex-only NLP is brittle for edge-case legal documents. No input validation beyond Pydantic schema. |
| D3 | **Algorithm & Domain Logic** | 7.0 | Evidence closed-loop checking (fact-evidence-law-penalty), weighted risk entropy scoring, TF-IDF similarity retrieval, and discretion benchmark deviation are sound domain abstractions. Weakness: TF-IDF recalculates IDF during search; no BM25 or semantic embeddings. |
| D4 | **Concurrency & State Safety** | 4.5 | **Critical:** Module-level singleton services with mutable instance state (`self.nodes`, `self.issues`, `self.timeline`) shared across async requests. Under concurrent load, Request B can read stale/partial state written by Request A. **FIXED in this review (see Section 4).** |
| D5 | **Testing & Validation** | 3.0 | `tests/` directory exists with `conftest.py` and `test_smoke.py` but no evidence of unit tests for the 6 domain services. No integration tests for the API endpoints. No property-based tests for regex patterns. Zero test coverage for risk scoring edge cases. |
| D6 | **Security & Data Integrity** | 4.0 | CORS `allow_origins=["*"]` is wide open. SQLite `check_same_thread=False` without connection pooling. No authentication/authorization on any endpoint. No rate limiting. DB path hardcoded. No input sanitization for case content stored in SQLite. |
| D7 | **Documentation & Maintainability** | 7.5 | Excellent Chinese docstrings on every class and method. Clear module-level comments describing purpose. Rule config is self-documenting. API_DOC.md exists. Weakness: no type stubs, no API versioning strategy, no changelog. |

**Composite Score: 5.5 / 10** -- Solid domain design but critical concurrency and security defects prevent production readiness.

---

## 2. Top 3 Problems

### Problem #1 [CRITICAL -- FIXED] Shared Mutable Singleton State Causes Concurrent Data Corruption

**Severity:** Critical (data integrity)
**Files:** `backend/app/api/routes.py`
**Root Cause:** Seven service instances are created once at module level and shared across all concurrent async requests. Three of them (`CaseParser`, `EvidenceChainChecker`, `ProcedureLegalChecker`) accumulate mutable state in instance attributes (`self.nodes`, `self.issues`, `self.chain_elements`, `self.timeline`).

**Impact:** Under concurrent requests, Request B can read residual state from Request A. For example:
- `case_parser.nodes` from Request A's case appears in Request B's `parsed_nodes`
- `evidence_chain_checker.issues` from Request A contaminates Request B's evidence report
- `procedure_checker.timeline` merges dates from multiple cases

This silently corrupts legal compliance reports -- a system that produces incorrect risk assessments for government administrative law cases.

**Fix Applied:** Replaced module-level singletons with per-request factory functions for the 3 stateful services. Stateless services (`DiscretionBenchmark`, `CaseRiskScorer`, `ReportGenerator`) and the intentionally-shared `CaseSimilarityRetriever` (corpus) remain as singletons.

```python
# BEFORE (broken):
case_parser = CaseParser()                    # shared across all requests
evidence_chain_checker = EvidenceChainChecker() # shared across all requests
procedure_checker = ProcedureLegalChecker()     # shared across all requests

# AFTER (fixed):
def _new_case_parser() -> CaseParser:
    """Per-request instance; avoids self.nodes cross-request pollution."""
    return CaseParser()

def _new_evidence_checker() -> EvidenceChainChecker:
    """Per-request instance; avoids self.issues / self.chain_elements pollution."""
    return EvidenceChainChecker()

def _new_procedure_checker() -> ProcedureLegalChecker:
    """Per-request instance; avoids self.issues / self.timeline pollution."""
    return ProcedureLegalChecker()
```

All 5 affected endpoints (`analyze_case`, `check_evidence_chain`, `check_procedure`, `get_case`) now call `_new_*()` to obtain fresh instances per request.

---

### Problem #2 [HIGH] Database Connection Leak on Exception Paths

**Severity:** High (resource exhaustion)
**Files:** `backend/app/api/routes.py` (all endpoints), `backend/app/core/database.py`

**Description:** Every endpoint follows the pattern:
```python
conn = get_db_connection()
cursor = conn.cursor()
# ... work ...
if error:
    conn.close()        # only closed on some error paths
    raise HTTPException(...)
# ... more work ...
conn.close()            # not reached if exception thrown between open and here
```

If any exception occurs between `get_db_connection()` and the final `conn.close()` (e.g., during `json.dumps`, `risk_scorer.score()`, or any service call), the connection is never closed. Under sustained load this exhausts SQLite file descriptors.

**Recommended Fix:** Use Python context managers (`with` statement) or a try/finally pattern:
```python
conn = get_db_connection()
try:
    cursor = conn.cursor()
    # ... all work ...
finally:
    conn.close()
```

---

### Problem #3 [HIGH] Regex-Only NLP Without Validation or Fallback

**Severity:** High (incorrect results in production)
**Files:** `backend/app/services/case_parser.py`, `evidence_chain_checker.py`, `discretion_benchmark.py`

**Description:** All legal document parsing relies entirely on regex patterns like:
```python
r"违法事实\s*[:：]\s*(.{20,500})"
r"罚款[金额]?\s*[:：]\s*(\d+(?:\.\d+)?)\s*(?:元|万元)"
```

Problems:
1. **Brittleness:** Minor formatting variations (extra whitespace, line breaks, different punctuation) cause silent parse failures
2. **Greedy matching:** `.{20,500}` can span across multiple logical sections, capturing irrelevant text
3. **No validation:** Parsed results are never cross-validated (e.g., extracted penalty amount vs. stated amount)
4. **No confidence scoring:** The system reports "事实认定不明确" (fact determination unclear) without indicating whether this is a genuine omission or a parsing failure

**Recommended Fix:** Add a secondary NLP-based parser (e.g., using a fine-tuned legal BERT model) as a fallback when regex yields zero results. Add confidence scores to parsed nodes.

---

## 3. Additional Observations

- **Risk scoring weights** (`case_risk_scorer.py`) are hardcoded (0.30/0.25/0.20/0.15/0.10) with no mechanism to calibrate against real case outcomes. For a published system, these should be empirically derived.
- **TF-IDF similarity** (`case_similarity_retriever.py`) recalculates IDF from scratch on every `search()` call. IDF should be computed once during `build_index()` and reused.
- **The `_check_completeness` method** in `CaseParser` always returns all 8 nodes as existing because `_parse_*` is called unconditionally -- it never actually detects missing process stages, only records "issues" within each node. The completeness score is always 100%.
- **No pagination** on `audit_logs` endpoint -- a `LIMIT` parameter exists but no `OFFSET`, making it impossible to retrieve older records.

---

## 4. Fix Summary

| Item | Status | File Modified |
|------|--------|---------------|
| Problem #1: Shared mutable singleton state | **FIXED** | `D:/ZYY Project/admin-law-review/backend/app/api/routes.py` |
| Problem #2: DB connection leak | Documented (not fixed -- lower priority than #1) | -- |
| Problem #3: Regex-only NLP | Documented (requires architectural change) | -- |

**Changes made to `routes.py`:**
- Removed 3 module-level singleton instantiations (`case_parser`, `evidence_chain_checker`, `procedure_checker`)
- Added 3 factory functions (`_new_case_parser()`, `_new_evidence_checker()`, `_new_procedure_checker()`)
- Updated all 5 affected endpoints to use per-request instances
- Added inline comments explaining the rationale

---

*End of Review*
