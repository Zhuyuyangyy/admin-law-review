# API Reference

## Base URL

```
http://localhost:8000
```

## Authentication

Currently no authentication is required. For production deployment, implement appropriate authentication.

## Endpoints

### Health Check

```
GET /health
```

**Response:**
```json
{
  "status": "ok"
}
```

---

### Upload Case

```
POST /api/upload_case
```

**Request Body:**
```json
{
  "case_number": "(X)罚字[2024]001号",
  "case_type": "行政处罚",
  "content": "Full case content text...",
  "filing_date": "2024-01-15"
}
```

**Response:**
```json
{
  "case_id": 1,
  "case_number": "(X)罚字[2024]001号",
  "status": "上传成功"
}
```

**Errors:**
- `400`: Case number already exists
- `422`: Invalid request body
- `500`: Server error

---

### Analyze Case

```
POST /api/analyze_case?case_id={case_id}
```

**Query Parameters:**
- `case_id` (int, required): Case ID

**Response:**
```json
{
  "case_id": 1,
  "case_number": "(X)罚字[2024]001号",
  "risk_level": "基本合规",
  "risk_score": 15.5,
  "radar_data": {
    "dimensions": ["事实风险", "证据风险", "程序风险", "裁量风险", "格式风险"],
    "scores": [10, 20, 15, 5, 8],
    "max_score": 100
  },
  "parsed_nodes": {...},
  "evidence_result": {...},
  "discretion_result": {...},
  "procedure_result": {...},
  "similarity_result": {...}
}
```

---

### Check Evidence Chain

```
POST /api/check_evidence_chain?case_id={case_id}
```

**Response:**
```json
{
  "case_id": 1,
  "is_complete": true,
  "score": 85.0,
  "chain_completeness": {
    "is_complete": true,
    "score": 100.0,
    "missing_elements": []
  },
  "evidence_sufficiency": {
    "is_sufficient": true,
    "score": 70.0,
    "evidence_count": 4,
    "type_diversity": 3,
    "high_priority_ratio": 0.75
  },
  "issues": []
}
```

---

### Match Discretion

```
POST /api/match_discretion?case_id={case_id}
```

**Response:**
```json
{
  "case_id": 1,
  "penalty_type": "罚款",
  "amount": 50000.0,
  "benchmark_min": null,
  "benchmark_max": null,
  "deviation": null,
  "is_abnormal": false,
  "match_level": "unknown",
  "issues": []
}
```

---

### Search Similar Cases

```
POST /api/search_similar_cases?case_id={case_id}&top_k=5
```

**Query Parameters:**
- `case_id` (int, required): Case ID
- `top_k` (int, default: 5): Number of results

**Response:**
```json
{
  "case_id": 1,
  "similar_cases": [
    {
      "case_id": 2,
      "similarity_score": 0.85,
      "keywords_matched": ["非法倾倒", "废物", "罚款"]
    }
  ]
}
```

---

### Check Procedure

```
POST /api/check_procedure?case_id={case_id}
```

**Response:**
```json
{
  "case_id": 1,
  "is_legal": true,
  "score": 90.0,
  "issues": [],
  "timeline": [
    {
      "node_id": "filing",
      "node_name": "立案",
      "date": "2024-01-15"
    }
  ]
}
```

---

### Get Risk Report

```
GET /api/get_risk_report/{case_id}
```

**Response:**
```json
{
  "report_title": "行政执法案卷合规评查报告",
  "report_id": "RPT-20240115120000",
  "generated_at": "2024年01月15日 12:00:00",
  "case_info": {...},
  "executive_summary": {...},
  "risk_assessment": {...},
  "issues_list": [...],
  "responsibility_nodes": [...],
  "rectification_suggestions": [...],
  "similar_case_comparison": {...},
  "conclusion": {...}
}
```

---

### Get Case

```
GET /api/get_case/{case_id}
```

**Response:**
```json
{
  "id": 1,
  "case_number": "(X)罚字[2024]001号",
  "case_type": "行政处罚",
  "content": "...",
  "filing_date": "2024-01-15",
  "status": "analyzed",
  "created_at": "2024-01-15 12:00:00",
  "parsed_nodes": {...}
}
```

---

### Audit Logs

```
GET /api/audit_logs?limit=100
```

**Query Parameters:**
- `limit` (int, default: 100): Maximum number of logs

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "action": "upload_case",
      "target_type": "cases",
      "target_id": 1,
      "details": "上传案件: (X)罚字[2024]001号",
      "created_at": "2024-01-15 12:00:00"
    }
  ]
}
```

---

## V1 API Endpoints

### Review Case

```
POST /api/v1/review_case
```

**Request Body:**
```json
{
  "case_id": "string",
  "facts": ["fact1", "fact2"],
  "evidence": [
    {
      "evidence_id": "E001",
      "description": "string",
      "type": "物证",
      "weight": 0.9
    }
  ],
  "procedure_steps": [
    {
      "step": "立案",
      "completed": true,
      "timestamp": "2024-01-15T00:00:00"
    }
  ]
}
```

---

### Check Facts-Evidence Consistency

```
POST /api/v1/check_facts_evidence_consistency
```

**Request Body:**
```json
{
  "case_id": "string",
  "facts": ["fact1"],
  "evidence_map": {
    "E001": "fact1"
  }
}
```

---

### Assess Procedure Compliance

```
POST /api/v1/assess_procedure_compliance
```

**Request Body:**
```json
{
  "case_id": "string",
  "procedure_steps": [
    {"step": "立案", "completed": true}
  ],
  "required_procedures": ["立案", "调查", "告知", "决定"]
}
```

---

### Get Case Summary

```
GET /api/v1/get_case_summary?case_id={case_id}
```

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 400 | Bad Request (e.g., duplicate case number) |
| 404 | Not Found (e.g., case doesn't exist) |
| 422 | Validation Error (invalid request body) |
| 500 | Internal Server Error |
