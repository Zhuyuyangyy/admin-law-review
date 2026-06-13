<div align="center">

# AdminLawReview

**AI-Powered Administrative Law Case Compliance Review System**

Evidence Chain Validation | Discretion Deviation Detection | Risk Entropy Scoring | Similar Case Retrieval

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Persistent-003B57?logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF?logo=githubactions&logoColor=white)](.github/workflows/ci.yml)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Coverage](https://img.shields.io/badge/Coverage-80%25+-brightgreen)](tests/)

</div>

---

## Overview

AdminLawReview is an AI-powered compliance review system for administrative law enforcement case files. It automates the detection of procedural defects, evidence chain gaps, discretionary penalty deviations, and risk issues in administrative penalty cases. The system implements a **five-dimensional risk entropy model** that evaluates cases across fact risk, evidence risk, procedure risk, discretion risk, and format risk, producing actionable compliance reports with remediation guidance.

**Key Differentiators:**
- Evidence chain closed-loop validation (fact -> evidence -> legal basis -> penalty)
- Discretion deviation detection with multi-factor adjustment
- Virtual process coordinate mapping for procedural defect detection
- TF-IDF-based similar case retrieval for equal-penalty consistency
- Five-dimensional risk entropy scoring with radar chart visualization

## Key Features

- **Case File Structure Parsing** -- Parses case files into structured nodes: case filing, investigation, evidence, notification, penalty, and service; maps process nodes to a 2D coordinate system (x: time, y: importance)
- **Evidence Chain Validation** -- Verifies closed-loop integrity: fact -> evidence -> legal basis -> penalty; checks evidence type diversity and high-priority evidence ratio; outputs chain completeness score
- **Discretion Benchmark Matching** -- Compares actual penalties against statutory standards; accounts for 5 discretion factors (violation severity, illegal gains, duration, subjective attitude, harm consequences); detects abnormal penalty deviations
- **Similar Case Retrieval** -- TF-IDF algorithm with jieba tokenization for Chinese text similarity; detects unequal-penalty-for-equal-cases problems; displays matched keywords
- **Procedure Legality Verification** -- Checks deadlines, notifications, signatures, and service compliance; virtual process coordinate-based legality detection; timeline validity verification
- **Five-Dimensional Risk Entropy Scoring** -- Weighted risk model: fact risk (30%), evidence risk (25%), procedure risk (20%), discretion risk (15%), format risk (10%); outputs 4-tier risk levels with radar chart data
- **Compliance Report Generation** -- Problem checklist with responsible nodes; remediation suggestions; compliance determination conclusion

## Architecture

```
                     +---------------------------+
                     |   Vue3 Frontend           |
                     |   (index.html)            |
                     +-------------+-------------+
                                   |
                                   | HTTP / REST
                                   v
                     +-------------+-------------+
                     |   FastAPI Backend         |
                     |   (Port 8000)             |
                     +-------------+-------------+
                                   |
              +--------------------+--------------------+
              |                    |                    |
    +---------v--------+ +--------v---------+ +--------v---------+
    | Case Parser      | | Evidence Chain   | | Discretion       |
    | (Structure       | | Checker          | | Benchmark        |
    |  Extraction)     | | (Closed-Loop)    | | (Deviation Det.) |
    +------------------+ +------------------+ +------------------+
              |                    |                    |
    +---------v--------+ +--------v---------+ +--------v---------+
    | Procedure Legal  | | Case Similarity  | | Report           |
    | Checker          | | Retriever        | | Generator        |
    | (Timeline +      | | (TF-IDF +        | | (Risk Summary    |
    |  Coordinate)     | |  jieba)          | |  + Remediation)  |
    +------------------+ +------------------+ +------------------+
                                   |
                        +----------v----------+
                        | Case Risk Scorer    |
                        | (5-Dim Entropy)     |
                        +---------------------+
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Backend Framework | FastAPI + Uvicorn | Async REST API server |
| Frontend | Vue3 (Single File) | Browser-based review dashboard |
| Database | SQLite | Case and audit log storage |
| NLP Tokenizer | jieba | Chinese text segmentation for similarity |
| Similarity | TF-IDF (scikit-learn style) | Similar case retrieval |
| Rule Engine | JSON rule library | Compliance rule definitions |
| Data Validation | Pydantic | Request/response schemas |
| Testing | pytest | Unit and integration tests |
| CI/CD | GitHub Actions | Lint + test + Docker pipeline |
| Containerization | Docker + docker-compose | Production deployment |
| Language | Python 3.11+ | Core runtime |

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Docker (optional, for containerized deployment)

### Installation

```bash
git clone https://github.com/<your-org>/admin-law-review.git
cd admin-law-review
pip install -r requirements.txt
```

### Run the Backend

```bash
# Option 1: Direct run
python main.py

# Option 2: Using uvicorn
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Option 3: Using startup scripts
# Windows
start.bat

# Linux/macOS
bash start.sh
```

API documentation: `http://localhost:8000/docs`

### Run the Frontend

Open `frontend/index.html` directly in a browser. No build step required.

### Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage report
pytest tests/ -v --cov=backend/app --cov-report=term-missing

# Run specific test module
pytest tests/test_services.py -v
```

### Lint

```bash
pip install ruff
ruff check backend/ tests/
ruff format backend/ tests/
```

### Docker

```bash
# Build and run with Docker
docker build -t admin-law-review .
docker run -p 8000:8000 admin-law-review

# Or use docker-compose for full stack
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/upload_case` | POST | Upload case file |
| `/api/analyze_case` | POST | Full case compliance analysis |
| `/api/check_evidence_chain` | POST | Check evidence chain integrity |
| `/api/match_discretion` | POST | Match discretion benchmarks |
| `/api/search_similar_cases` | POST | Retrieve similar historical cases |
| `/api/check_procedure` | POST | Verify procedure legality |
| `/api/get_risk_report/{case_id}` | GET | Get risk report for a case |
| `/api/get_case/{case_id}` | GET | Get case information |
| `/api/audit_logs` | GET | Retrieve audit logs |
| `/api/health` | GET | Health check |
| `/api/v1/review_case` | POST | Comprehensive case review |
| `/api/v1/check_facts_evidence_consistency` | POST | Facts-evidence consistency check |
| `/api/v1/assess_procedure_compliance` | POST | Procedure compliance assessment |
| `/api/v1/get_case_summary` | GET | Get case summary |

## Project Structure

```
admin-law-review/
|-- backend/
|   |-- app/
|   |   |-- main.py                           # FastAPI application entry
|   |   |-- api/
|   |   |   +-- routes.py                     # API route handlers
|   |   |-- core/
|   |   |   +-- database.py                   # SQLite database initialization
|   |   |-- models/
|   |   |   +-- schemas.py                    # Pydantic data models
|   |   |-- rules/
|   |   |   +-- admin_law_rules.json          # Compliance rule definitions
|   |   +-- services/
|   |       |-- case_parser.py                # Case file structure parser
|   |       |-- evidence_chain_checker.py     # Evidence chain validation
|   |       |-- discretion_benchmark.py       # Discretion deviation detection
|   |       |-- case_similarity_retriever.py  # TF-IDF similar case search
|   |       |-- procedure_legal_checker.py    # Procedure legality verification
|   |       |-- case_risk_scorer.py           # 5-dimension risk entropy scorer
|   |       +-- report_generator.py           # Compliance report generation
|   |-- requirements.txt
|   +-- API_DOC.md                            # API documentation
|-- frontend/
|   +-- index.html                            # Vue3 dashboard
|-- tests/
|   |-- __init__.py
|   |-- conftest.py                           # Test configuration
|   |-- test_smoke.py                         # Smoke tests
|   |-- test_services.py                      # Service unit tests
|   |-- test_api.py                           # API integration tests
|   +-- test_edge_cases.py                    # Edge case tests
|-- docs/
|   |-- ARCHITECTURE.md                       # Architecture documentation
|   |-- DEPLOYMENT.md                         # Deployment guide
|   |-- API_REFERENCE.md                      # API reference
|   +-- figures/                              # Architecture diagrams
|-- .github/workflows/ci.yml                 # CI pipeline
|-- docker-compose.yml                        # Docker Compose configuration
|-- CONTRIBUTING.md                           # Contribution guidelines
|-- TODO.md                                   # Innovation suggestions
|-- INNOVATION_ROADMAP.md                     # Patent and innovation roadmap
|-- OPTIMIZATION_REPORT.md                    # Project optimization report
|-- Dockerfile
|-- main.py                                   # Top-level entry point
|-- .gitignore
+-- README.md
```

## Rule Library

| Rule ID | Type | Description | Severity |
|---------|------|-------------|----------|
| RULE_AL_001 | fact_unclear | Facts not clearly established | High |
| RULE_AL_002 | evidence_incomplete | Evidence chain incomplete | High |
| RULE_AL_003 | wrong_legal_basis | Incorrect legal basis citation | High |
| RULE_AL_004 | unequal_penalty | Unequal penalty for equal cases | Medium |
| RULE_AL_005 | procedure_defect | Procedural defect | Medium |
| RULE_AL_006 | discretion_abnormal | Abnormal discretionary range | Medium |
| RULE_AL_007 | document_format | Non-standard document format | Low |
| RULE_AL_008 | evidence_insufficient | Evidence materials insufficient | Medium |
| RULE_AL_009 | notice_incomplete | Notice procedure incomplete | Medium |
| RULE_AL_010 | signature_missing | Document signature missing | Low |

## Risk Levels

| Level | Score Range | Description |
|-------|------------|-------------|
| Major Defect | 80-100 | Serious legal violation; penalty decision may be revoked |
| General Defect | 50-80 | Multiple procedural or substantive issues; remediation recommended |
| Format Issue | 20-50 | Basically compliant; minor formatting issues only |
| Basically Compliant | 0-20 | Meets statutory requirements |

## Innovation Highlights

### Evidence Chain Closed-Loop Validation

Verifies that case files contain a complete evidentiary chain:
- **Fact** -> **Evidence** -> **Legal Basis** -> **Penalty**
- Checks evidence type diversity (requires 2+ types, 3+ for full score)
- Evaluates high-priority evidence ratio (physical evidence, documentary evidence, expert opinions weighted higher)
- Outputs chain completeness score and missing link identification

### Five-Dimensional Risk Entropy Model

Computes case risk across 5 weighted dimensions:

| Dimension | Weight | Description |
|-----------|--------|-------------|
| Fact Risk | 30% | Clarity and completeness of fact determination |
| Evidence Risk | 25% | Evidence chain integrity and sufficiency |
| Procedure Risk | 20% | Legal procedure compliance |
| Discretion Risk | 15% | Penalty deviation from statutory standards |
| Format Risk | 10% | Document format and completeness |

**Patent Pending:** Administrative law case risk entropy grading assessment system

### Discretion Deviation Detection

Compares actual penalties against statutory standards with 5 adjustment factors:
- Violation severity (minor/normal/severe/especially severe)
- Illegal gains (none/minor/substantial)
- Duration (short/medium/long)
- Subjective attitude (cooperative/normal/resistant)
- Consequences (minor/normal/severe/especially severe)

**Patent Pending:** Penalty discretion deviation identification method for equal-penalty enforcement

## Database Schema

| Table | Purpose |
|-------|---------|
| `rules` | Compliance rule definitions |
| `cases` | Uploaded case records |
| `evidence_records` | Evidence materials |
| `penalty_records` | Penalty information |
| `analysis_results` | Analysis output storage |
| `similar_cases` | Similar case matches |
| `audit_logs` | System audit trail |

## Benchmarks

| Metric | Value |
|--------|-------|
| Evidence chain detection coverage | 4 required elements |
| Risk dimension count | 5 (weighted) |
| Rule library size | 10 rules (extensible) |
| Similarity algorithm | TF-IDF with jieba tokenization |
| Discretion factor count | 5 adjustment factors |
| Test coverage | 80%+ |

## Research

This project implements research concepts from:
- Information entropy applied to legal compliance assessment
- TF-IDF similarity for legal case matching
- Evidence chain theory in administrative law enforcement

**Patent Portfolio (4 filings pending):**
1. Evidence chain closed-loop-based administrative case compliance review method
2. Equal-penalty-oriented administrative penalty discretion deviation identification method
3. Virtual process coordinate-based procedural defect detection method
4. Administrative case risk entropy grading assessment system

## Roadmap

See [INNOVATION_ROADMAP.md](INNOVATION_ROADMAP.md) for the detailed innovation and patent roadmap.

- [x] V1.0: Core compliance review engine
- [x] V1.1: Five-dimensional risk entropy model
- [ ] V2.0: LLM-powered case file intelligent parsing
- [ ] V2.1: Knowledge graph integration for legal provision reasoning
- [ ] V3.0: Multi-case batch audit with statistical analysis
- [ ] V3.1: Integration with government case management systems
- [ ] V3.2: Cross-jurisdictional case comparison and benchmarking

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions, collaboration, or enterprise inquiries, please open a GitHub issue or contact the maintainers.
