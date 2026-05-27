# Admin Law Review API Documentation

## Base URL
```
/api/v1
```

## Endpoints

### 1. POST /review_case

Comprehensive admin case review covering facts, evidence, and procedure compliance.

**Request Body:**
```json
{
  "case_id": "string",
  "facts": ["string"],
  "evidence": [
    {
      "evidence_id": "string",
      "description": "string",
      "type": "string (物证|书证|鉴定意见|证人证言|当事人陈述|...)",
      "weight": 0.0-1.0
    }
  ],
  "procedure_steps": [
    {
      "step": "string",
      "completed": true,
      "timestamp": "ISO datetime string"
    }
  ]
}
```

**Response:**
```json
{
  "case_id": "string",
  "fact_count": 0,
  "evidence_count": 0,
  "fact_coverage": {
    "<fact>": {
      "supporting_evidence": ["evidence_id"],
      "coverage_score": 0.0-1.0
    }
  },
  "evidence_assessment": [
    {
      "evidence_id": "string",
      "quality_score": 0.0-1.0,
      "assessment": "强|中|弱",
      "type": "string"
    }
  ],
  "procedure_compliance": [
    {
      "step": "string",
      "completed": true,
      "compliance_rate": 0|100,
      "timestamp": "string"
    }
  ],
  "overall_quality_score": 0.0-1.0,
  "review_timestamp": "ISO datetime"
}
```

---

### 2. POST /check_facts_evidence_consistency

Check consistency between facts and supporting evidence.

**Request Body:**
```json
{
  "case_id": "string",
  "facts": ["string"],
  "evidence_map": {
    "evidence_id": "supported_fact"
  }
}
```

**Response:**
```json
{
  "case_id": "string",
  "total_facts": 0,
  "inconsistencies_found": 0,
  "contradiction_score": 0.0-1.0,
  "inconsistencies": [
    {
      "fact": "string",
      "issue": "string",
      "severity": "high|medium|low"
    }
  ],
  "consistency_verdict": "证据充分|存疑需补充|事实认定存疑"
}
```

---

### 3. POST /assess_procedure_compliance

Assess whether procedure steps comply with legal requirements.

**Request Body:**
```json
{
  "case_id": "string",
  "procedure_steps": [
    {
      "step": "string",
      "completed": true
    }
  ],
  "required_procedures": ["string"]
}
```

**Response:**
```json
{
  "case_id": "string",
  "compliance_rate": 0.0-100.0,
  "required_steps": ["string"],
  "completed_steps": ["string"],
  "missing_steps": ["string"],
  "extra_steps": ["string"],
  "violations": [
    {
      "type": "missing_required_step|incomplete_step",
      "steps": ["string"],
      "severity": "critical|high|medium|low"
    }
  ],
  "verdict": "程序合法|程序违法|程序瑕疵"
}
```

---

### 4. GET /get_case_summary

Get a summary for a given case ID.

**Query Parameters:**
- `case_id` (string, required): The case identifier

**Response:**
```json
{
  "case_id": "string",
  "case_type": "行政处罚|行政许可|行政强制|行政复议",
  "case_status": "已立案|调查中|审理中|已结案",
  "summary": "string",
  "key_findings": ["string"],
  "decision": "维持原决定|发回重审",
  "confidence": 0.75-0.95
}
```

---

## Evidence Type Quality Weights

| Type | Weight Multiplier |
|------|-------------------|
| 物证 | 0.9 |
| 书证 | 0.9 |
| 鉴定意见 | 0.9 |
| 证人证言 | 0.6 |
| 当事人陈述 | 0.6 |
| 其他 | 0.4 |

## Consistency Verdict Thresholds

| Score Range | Verdict |
|-------------|---------|
| < 0.2 | 证据充分 |
| 0.2 - 0.5 | 存疑需补充 |
| >= 0.5 | 事实认定存疑 |

## Procedure Compliance Verdict

| Compliance Rate | Violations | Verdict |
|----------------|------------|---------|
| 100% | None | 程序合法 |
| < 70% | Any | 程序违法 |
| >= 70% | Any | 程序瑕疵 |