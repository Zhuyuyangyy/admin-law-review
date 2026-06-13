# Architecture Documentation

## System Architecture

AdminLawReview follows a layered architecture pattern with clear separation of concerns:

```
+--------------------------------------------------+
|                   Frontend Layer                  |
|              Vue3 Single-Page App                |
+--------------------------------------------------+
                        |
                   HTTP / REST
                        |
+--------------------------------------------------+
|                   API Layer                       |
|         FastAPI Routes (routes.py)               |
+--------------------------------------------------+
                        |
+--------------------------------------------------+
|                Service Layer                      |
|  CaseParser | EvidenceChain | Discretion | ...   |
+--------------------------------------------------+
                        |
+--------------------------------------------------+
|                Data Layer                         |
|           SQLite (database.py)                   |
+--------------------------------------------------+
```

## Core Components

### 1. Case Parser (`case_parser.py`)

Parses administrative law case files into structured process nodes using regex-based pattern matching.

**Key Features:**
- Virtual process coordinate mapping (x: time dimension 0-100, y: importance dimension 0-100)
- 8 process nodes: filing, investigation, evidence, fact determination, notice, hearing, penalty decision, delivery
- Timeline construction from extracted dates
- Completeness scoring

### 2. Evidence Chain Checker (`evidence_chain_checker.py`)

Validates the closed-loop integrity of evidence chains.

**Chain Elements:**
- Fact (violation facts)
- Evidence (materials)
- Legal Basis (law references)
- Penalty (punishment result)

**Scoring:**
- Chain completeness: 50% weight
- Evidence sufficiency: 50% weight
- Evidence type diversity (minimum 2 types, 3+ for full score)
- High-priority evidence ratio (physical/documentary evidence weighted higher)

### 3. Discretion Benchmark (`discretion_benchmark.py`)

Detects abnormal penalty deviations by comparing against statutory standards.

**5 Discretion Factors:**
| Factor | Levels | Weight Range |
|--------|--------|--------------|
| Violation Severity | Minor/Normal/Severe/Especially Severe | 0.5 - 2.0 |
| Illegal Gains | None/Minor/Substantial | 0.5 - 1.5 |
| Duration | Short/Medium/Long | 0.8 - 1.3 |
| Subjective Attitude | Cooperative/Normal/Resistant | 0.7 - 1.3 |
| Consequences | Minor/Normal/Severe/Especially Severe | 0.8 - 1.6 |

**Match Levels:**
- Excellent: deviation <= 10%
- Good: deviation <= 20%
- Acceptable: deviation <= 30%
- Poor: deviation > 30%
- Abnormal: outside allowed range

### 4. Case Similarity Retriever (`case_similarity_retriever.py`)

TF-IDF-based similar case retrieval with Chinese text tokenization.

**Algorithm:**
1. Extract keywords using jieba tokenizer
2. Calculate TF (Term Frequency) per document
3. Calculate IDF (Inverse Document Frequency) across corpus
4. Compute TF-IDF vectors
5. Calculate cosine similarity between query and corpus
6. Return top-k most similar cases

### 5. Procedure Legal Checker (`procedure_legal_checker.py`)

Verifies procedural compliance including deadlines, notifications, signatures, and service.

**Legal Deadlines:**
| Stage | Max Days |
|-------|----------|
| Filing to Investigation | 7 |
| Investigation to Decision | 30 |
| Notice to Decision | 3 |
| Decision to Delivery | 7 |
| Extension Maximum | 30 |

### 6. Case Risk Scorer (`case_risk_scorer.py`)

Five-dimensional risk entropy model with weighted scoring.

**Dimensions:**
| Dimension | Weight | Description |
|-----------|--------|-------------|
| Fact Risk | 30% | Clarity and completeness |
| Evidence Risk | 25% | Chain integrity and sufficiency |
| Procedure Risk | 20% | Legal compliance |
| Discretion Risk | 15% | Penalty deviation |
| Format Risk | 10% | Document completeness |

**Risk Levels:**
| Level | Score Range | Description |
|-------|------------|-------------|
| Major Defect | 80-100 | Serious violation |
| General Defect | 50-80 | Multiple issues |
| Format Issue | 20-50 | Minor formatting |
| Basically Compliant | 0-20 | Meets requirements |

### 7. Report Generator (`report_generator.py`)

Generates comprehensive compliance reports with:
- Executive summary
- Risk assessment with radar chart data
- Issues list categorized by severity
- Responsibility nodes
- Rectification suggestions
- Similar case comparison
- Compliance conclusion

## Data Flow

```
1. User uploads case file
   -> Case stored in SQLite database

2. User requests analysis
   -> CaseParser extracts process nodes
   -> EvidenceChainChecker validates chain
   -> DiscretionBenchmark checks penalty
   -> ProcedureLegalChecker verifies compliance
   -> CaseSimilarityRetriever finds similar cases
   -> CaseRiskScorer computes risk score
   -> ReportGenerator creates report

3. User views risk report
   -> Comprehensive report with radar chart
   -> Issues list with remediation guidance
```

## Database Schema

```sql
-- Rules table
CREATE TABLE rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id TEXT UNIQUE NOT NULL,
    rule_type TEXT NOT NULL,
    description TEXT NOT NULL,
    severity TEXT NOT NULL,
    penalty TEXT,
    enabled INTEGER DEFAULT 1
);

-- Cases table
CREATE TABLE cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_number TEXT UNIQUE NOT NULL,
    case_type TEXT NOT NULL,
    content TEXT NOT NULL,
    filing_date TEXT,
    status TEXT DEFAULT 'pending',
    created_at TEXT DEFAULT (datetime('now'))
);

-- Evidence records
CREATE TABLE evidence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    evidence_type TEXT NOT NULL,
    content TEXT NOT NULL,
    submitted_date TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Penalty records
CREATE TABLE penalty_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    penalty_type TEXT NOT NULL,
    amount REAL,
    basis_article TEXT,
    discretion_basis TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Analysis results
CREATE TABLE analysis_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    risk_score REAL NOT NULL,
    risk_level TEXT NOT NULL,
    details_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

-- Similar cases
CREATE TABLE similar_cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    case_id INTEGER NOT NULL,
    similar_case_id INTEGER NOT NULL,
    similarity_score REAL NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (similar_case_id) REFERENCES cases(id)
);

-- Audit logs
CREATE TABLE audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    target_type TEXT,
    target_id INTEGER,
    details TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```

## Security Considerations

- CORS middleware configured for development (restrict in production)
- SQLite database with file-level access control
- Non-root Docker user for container security
- Health check endpoint for monitoring
- Audit logging for all operations
