# SCI Q2 Review -- Round 2: admin-law-review

**Project:** 行政执法案卷合规评查系统 (Administrative Law Case Compliance Review System)
**Review Date:** 2026-05-29
**Reviewer:** AI Code Review Agent
**Scope:** Full codebase -- 10 core Python modules, 1 JSON rule config, API layer, DB layer, 4 test files
**Baseline:** Round 1 review (SCI_REVIEW_Q2.md)

---

## 0. Round 1 Fix Verification

### Problem #1: Shared Mutable Singleton State [CRITICAL -- FIXED, VERIFIED]

**Status: Confirmed Fixed.**

Verified in `backend/app/api/routes.py`:
- Lines 28-31: Four stateless services remain as module-level singletons (`discretion_benchmark`, `similarity_retriever`, `risk_scorer`, `report_generator`). This is correct -- they either reset mutable state at the start of each method call, or never mutate instance state.
- Lines 34-46: Three factory functions (`_new_case_parser`, `_new_evidence_checker`, `_new_procedure_checker`) create fresh instances per request.
- All 5 affected endpoints confirmed using per-request instances:
  - `analyze_case` (lines 112, 116, 134)
  - `check_evidence_chain` (lines 199, 201)
  - `check_procedure` (lines 307, 309)
  - `get_case` (line 394)

**Concurrency safety of remaining singletons confirmed:**
- `CaseRiskScorer.score()`: resets `self.risk_scores` and `self.risk_details` at entry (line 53-54).
- `DiscretionBenchmark.match()`: stateless -- uses only local variables. `self.benchmarks` is read-only after `__init__`.
- `ReportGenerator.generate()`: stateless -- uses only local variables and parameters.
- `CaseSimilarityRetriever`: intentionally shared corpus; no per-request mutation in `search()`.

---

## 1. Seven-Dimension Scoring (Round 2)

| # | Dimension | R1 Score | R2 Score | Delta | Rationale |
|---|-----------|:--------:|:--------:|:-----:|-----------|
| D1 | **Architecture & Modularity** | 7.5 | 7.5 | -- | Unchanged. Clean 4-layer separation. Weakness: dual API surface (v1_router in `backend/app/main.py` uses `random.choice` for case summaries -- this is mock/placeholder code in production routing). |
| D2 | **Code Correctness & Robustness** | 5.0 | 5.5 | +0.5 | DB connection leak remains (see Problem #2). Regex-only NLP remains. New finding: `_check_completeness` in `CaseParser` always returns 100% (see Section 2). New finding: operator precedence bug in `_parse_penalty_decision`. Offset by expanded test coverage catching more regressions. |
| D3 | **Algorithm & Domain Logic** | 7.0 | 7.0 | -- | Unchanged. Closed-loop evidence checking, weighted risk entropy, TF-IDF similarity, discretion deviation are sound. IDF recalculation on every `search()` call persists. |
| D4 | **Concurrency & State Safety** | 4.5 | 7.5 | +3.0 | **Major improvement.** Critical shared-mutable-singleton bug fixed and verified. Remaining concern: SQLite `check_same_thread=False` without connection pooling is a latent concurrency risk under true multi-threaded deployment (though safe under uvicorn's single-threaded async model). |
| D5 | **Testing & Validation** | 3.0 | 6.5 | +3.5 | **Major improvement.** Round 1 had zero service-level tests. Round 2 has: `test_smoke.py` (module imports + basic smoke), `test_services.py` (100+ unit tests across all 7 services), `test_api.py` (API integration tests), `test_edge_cases.py` (boundary/error conditions). No concurrency tests, no security tests, no property-based tests for regex. |
| D6 | **Security & Data Integrity** | 4.0 | 4.0 | -- | Unchanged. CORS `allow_origins=["*"]` persists. No auth/authz. No rate limiting. DB path hardcoded. No input sanitization. SQLite `check_same_thread=False`. |
| D7 | **Documentation & Maintainability** | 7.5 | 7.5 | -- | Unchanged. Excellent Chinese docstrings. Rule config self-documenting. |

**R1 Composite Score: 5.5 / 10**
**R2 Composite Score: 6.5 / 10** (+1.0)

Improvements driven by concurrency fix (+3.0 on D4) and expanded test coverage (+3.5 on D5). Correctness slightly improved (+0.5 on D2) due to tests catching regressions, offset by newly discovered logic bugs.

---

## 2. Remaining and New Problems

### Problem #1 [HIGH -- UNFIXED] Database Connection Leak on Exception Paths

**Severity:** High (resource exhaustion)
**Files:** `backend/app/api/routes.py` (all 8 endpoints), `backend/app/core/database.py`
**Status:** Documented in Round 1, NOT fixed.

Every endpoint follows this pattern:
```python
conn = get_db_connection()
cursor = conn.cursor()
# ... work that may throw ...
conn.close()  # never reached if exception thrown above
```

Additionally, `upload_case` has a specific leak path at line 67:
```python
if existing:
    conn.close()                    # closed here
    raise HTTPException(...)        # OK for this path
# ... but if INSERT fails between line 71 and line 81, conn is leaked
```

**Impact:** Under sustained load with exceptions, SQLite file descriptors are exhausted. The `log_audit` function in `database.py` also opens a separate connection for every audit write (line 128-135), compounding the problem.

**Recommended Fix:** Wrap all DB access in try/finally:
```python
conn = get_db_connection()
try:
    cursor = conn.cursor()
    # ... all work ...
    conn.commit()
finally:
    conn.close()
```

---

### Problem #2 [MEDIUM -- NEW] `_check_completeness` Always Returns 100%

**Severity:** Medium (incorrect compliance assessment)
**File:** `backend/app/services/case_parser.py`, lines 351-363

**Description:** The `_check_completeness` method checks whether all required node IDs exist in `self.nodes`. However, all 8 `_parse_*` methods **unconditionally** append a `ProcessNode` to `self.nodes` -- even when no data is found (they record "未明确记载" or "未进行有效调查取证" as content). Therefore `self.nodes` always contains all 8 node IDs, `missing` is always empty, and `completeness_score` is always 100%.

**Impact:** The system never detects truly missing process stages. A case with zero filing information, no investigation records, and no delivery evidence still reports 100% completeness. This undermines the risk scoring pipeline, which uses completeness as an input.

**Recommended Fix:** Only append nodes to `self.nodes` when meaningful data is found. Use a separate list (e.g., `self.all_node_ids`) to track which nodes were *attempted*, and only add to `self.nodes` when the parse succeeds. Alternatively, add a `found` boolean flag to `ProcessNode` and filter on it in `_check_completeness`.

---

### Problem #3 [MEDIUM -- NEW] Operator Precedence Bug in `_parse_penalty_decision`

**Severity:** Medium (incorrect node content)
**File:** `backend/app/services/case_parser.py`, line 304

**Description:**
```python
content=found_content or f"罚款金额: {penalty_amount}" if penalty_amount else "处罚决定内容不明确",
```

Due to Python operator precedence, this evaluates as:
```python
content=(found_content or (f"罚款金额: {penalty_amount}" if penalty_amount else "处罚决定内容不明确"))
```

But the intended logic is likely:
```python
content=(found_content or f"罚款金额: {penalty_amount}") if penalty_amount else "处罚决定内容不明确"
```

When `found_content` is empty string `""` and `penalty_amount` is `"50000元"`, the current code correctly produces `"罚款金额: 50000元"` (because `"" or expr` evaluates to `expr`). However, when both `found_content` and `penalty_amount` are empty/None, the node content becomes `"处罚决定内容不明确"` which is correct by accident. The real risk is that the intent is ambiguous and the code is fragile -- any refactor could break it.

**Recommended Fix:** Use explicit parentheses or an if/else block:
```python
if found_content:
    node_content = found_content
elif penalty_amount:
    node_content = f"罚款金额: {penalty_amount}"
else:
    node_content = "处罚决定内容不明确"
```

---

### Problem #4 [HIGH -- UNFIXED] Regex-Only NLP Without Validation or Fallback

**Severity:** High (incorrect results in production)
**Files:** `case_parser.py`, `evidence_chain_checker.py`, `discretion_benchmark.py`
**Status:** Documented in Round 1, NOT fixed. Requires architectural change.

All legal document parsing relies on regex patterns. Key risks:
1. Minor formatting variations cause silent parse failures
2. Greedy `.{20,500}` patterns can span logical sections
3. No confidence scoring -- system cannot distinguish "genuine omission" from "parse failure"
4. No cross-validation of extracted values

---

### Problem #5 [MEDIUM -- NEW] v1_router Contains Mock/Placeholder Logic

**Severity:** Medium (data integrity in production)
**File:** `backend/app/main.py`

The `get_case_summary` endpoint (line 77-78) uses `random.choice` to generate case type, status, and decision:
```python
"case_type": random.choice(["行政处罚", "行政许可", "行政强制", "行政复议"]),
"case_status": random.choice(["已立案", "调查中", "审理中", "已结案"]),
"decision": "维持原决定" if random.random() > 0.3 else "发回重审",
"confidence": round(random.uniform(0.75, 0.95), 2)
```

This router is mounted in production (`main.py` line 37). Any client calling `/api/v1/get_case_summary` receives randomized data. The `review_case` and `check_facts_evidence_consistency` endpoints also use simplified heuristics (word-split matching) rather than the domain services.

---

## 3. Additional Observations (Carried from Round 1)

- **Risk scoring weights** (`case_risk_scorer.py`) remain hardcoded (0.30/0.25/0.20/0.15/0.10) with no calibration mechanism.
- **TF-IDF similarity** (`case_similarity_retriever.py`) recalculates IDF from scratch on every `search()` call (lines 87-95). IDF should be computed once during `build_index()` and stored.
- **No pagination** on `audit_logs` endpoint -- `LIMIT` exists but no `OFFSET`.
- **`log_audit` opens a new DB connection** every call (database.py lines 128-135), even when called from within an endpoint that already has an open connection. This is wasteful and compounds the connection leak.
- **CORS `allow_origins=["*"]`** with `allow_credentials=True` is a security anti-pattern (main.py line 19-25).
- **No authentication/authorization** on any endpoint.
- **`check_same_thread=False`** on SQLite connection (database.py line 11) is unsafe if the app is deployed with multiple worker threads.

---

## 4. Round 2 Fix Summary

| Item | Round 1 Status | Round 2 Status | File |
|------|----------------|----------------|------|
| Problem #1: Shared mutable singleton state | FIXED | **VERIFIED FIXED** | `routes.py` |
| Problem #2: DB connection leak | Documented | **UNFIXED** | `routes.py`, `database.py` |
| Problem #3: Regex-only NLP | Documented | **UNFIXED** (architectural) | Multiple services |
| New: `_check_completeness` always 100% | -- | **NEW, UNFIXED** | `case_parser.py` |
| New: Operator precedence in penalty parsing | -- | **NEW, UNFIXED** | `case_parser.py` |
| New: v1_router mock logic in production | -- | **NEW, UNFIXED** | `backend/app/main.py` |

---

## 5. Test Coverage Assessment (Round 2)

| Category | Round 1 | Round 2 | Notes |
|----------|---------|---------|-------|
| Module imports | 0 | 9 tests | `test_smoke.py` |
| Service unit tests | 0 | 80+ tests | `test_services.py` -- all 7 services |
| API integration tests | 0 | 15+ tests | `test_api.py` -- all endpoints |
| Edge case tests | 0 | 40+ tests | `test_edge_cases.py` -- boundary conditions |
| Concurrency tests | 0 | 0 | No concurrent request testing |
| Security tests | 0 | 0 | No auth/injection testing |
| Property-based tests | 0 | 0 | No Hypothesis-based regex testing |

---

## 6. Recommendations for Round 3

1. **Fix DB connection leak** (Problem #1): Wrap all endpoint DB access in try/finally. Pass connection to `log_audit` instead of creating new ones.
2. **Fix `_check_completeness`** (Problem #2): Only count nodes with meaningful parsed data as "present".
3. **Fix operator precedence** (Problem #3): Add explicit parentheses or if/else in `_parse_penalty_decision`.
4. **Remove or isolate v1_router mock code** (Problem #5): Either implement properly or move to a test-only mount.
5. **Add concurrency tests**: Use `asyncio.gather` to send multiple simultaneous requests and verify no state leakage.
6. **Cache IDF** in `CaseSimilarityRetriever.build_index()` and reuse in `search()`.

---

*End of Round 2 Review*
