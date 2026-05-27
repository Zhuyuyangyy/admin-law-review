# 行政执法案卷合规评查与裁量偏差风险控制系统 V1.0

## 项目概述

基于证据链闭环的行政执法案卷合规评查系统，支持裁量基准匹配、风险熵分级评估和同案相似度检索。

## 核心功能

### 1. 案卷结构解析 (`case_parser.py`)
- 解析立案、调查、证据、告知、处罚、送达等流程节点
- **虚拟流程坐标映射**：将流程节点映射到二维坐标系（x: 时间维度, y: 重要度维度）
- 检测流程完整性

### 2. 证据链完整性检测 (`evidence_chain_checker.py`)
- 判断事实—证据—法条—处罚是否闭环
- 证据充分性检测（类型多样性、高优先级证据占比）
- 输出证据链评分

### 3. 裁量基准匹配 (`discretion_benchmark.py`)
- 对照自由裁量标准检测处罚幅度
- 考虑违法情节、持续时间等裁量因素
- 计算裁量偏差，识别异常裁量

### 4. 同案相似度检索 (`case_similarity_retriever.py`)
- 基于TF-IDF算法检索历史相似案例
- 检测同案不同罚问题
- 匹配关键词展示

### 5. 程序合法性校验 (`procedure_legal_checker.py`)
- 检查期限、告知、签章、送达等程序问题
- **虚拟流程坐标**：基于流程坐标检测程序节点合法性
- 时间线合法性检测

### 6. 案卷风险熵评分 (`case_risk_scorer.py`)
- 五维风险评估：事实风险、证据风险、程序风险、裁量风险、格式风险
- 输出：重大瑕疵、一般瑕疵、格式问题、基本合规
- 多维风险耦合计算

### 7. 风险分级报告 (`report_generator.py`)
- 问题清单、责任节点、整改建议
- 合规判定结论

## 四大专利核心

1. **一种基于证据链闭环的行政执法案卷合规评查方法** - 证据链完整性检测
2. **一种面向同案同罚的行政处罚裁量偏差识别方法** - 裁量基准匹配
3. **一种基于虚拟流程坐标的执法程序瑕疵检测方法** - 虚拟流程坐标
4. **一种行政执法案卷风险熵分级评估系统** - 风险熵评分

## 技术架构

- **后端**: Python 3.12 + FastAPI + uvicorn
- **规则引擎**: 本地规则库 JSON
- **相似度检索**: TF-IDF 算法 + jieba分词
- **数据库**: SQLite
- **前端**: Vue3 单文件应用（浏览器直接打开）

## 目录结构

```
admin-law-review/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py          # API路由
│   │   ├── core/
│   │   │   └── database.py       # 数据库初始化
│   │   ├── models/
│   │   │   └── schemas.py        # 数据模型
│   │   ├── services/
│   │   │   ├── case_parser.py              # 案卷结构解析
│   │   │   ├── evidence_chain_checker.py  # 证据链检测
│   │   │   ├── discretion_benchmark.py    # 裁量基准
│   │   │   ├── case_similarity_retriever.py # 相似度检索
│   │   │   ├── procedure_legal_checker.py # 程序合法性
│   │   │   ├── case_risk_scorer.py        # 风险熵评分
│   │   │   └── report_generator.py        # 报告生成
│   │   ├── rules/
│   │   │   └── admin_law_rules.json       # 规则库
│   │   └── main.py              # FastAPI入口
│   ├── requirements.txt
│   └── start.bat               # 启动脚本
└── frontend/
    └── index.html              # Vue3前端
```

## 启动方式

### 后端启动
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8015 --reload
```
或双击运行 `start.bat`

### 前端访问
直接用浏览器打开 `frontend/index.html`

## API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/upload_case` | POST | 上传案卷 |
| `/api/analyze_case` | POST | 分析案卷合规性 |
| `/api/check_evidence_chain` | POST | 检测证据链完整性 |
| `/api/match_discretion` | POST | 匹配裁量基准 |
| `/api/search_similar_cases` | POST | 检索相似案例 |
| `/api/check_procedure` | POST | 校验程序合法性 |
| `/api/get_risk_report/{case_id}` | GET | 获取风险报告 |
| `/api/get_case/{case_id}` | GET | 获取案卷信息 |
| `/api/audit_logs` | GET | 审计日志 |
| `/api/health` | GET | 健康检查 |

## 数据库表

- `rules` - 规则表
- `cases` - 案件表
- `evidence_records` - 证据记录表
- `penalty_records` - 处罚记录表
- `analysis_results` - 分析结果表
- `similar_cases` - 相似案件表
- `audit_logs` - 审计日志表

## 规则库

| 规则ID | 类型 | 描述 | 严重程度 |
|--------|------|------|----------|
| RULE_AL_001 | fact_unclear | 事实认定不清 | high |
| RULE_AL_002 | evidence_incomplete | 证据链不完整 | high |
| RULE_AL_003 | wrong_legal_basis | 处罚依据引用错误 | high |
| RULE_AL_004 | unequal_penalty | 同案不同罚 | medium |
| RULE_AL_005 | procedure_defect | 程序瑕疵 | medium |
| RULE_AL_006 | discretion_abnormal | 自由裁量幅度异常 | medium |
| RULE_AL_007 | document_format | 文书格式不规范 | low |

## 风险等级

- **重大瑕疵** (80-100分): 存在严重违法问题，可能导致处罚决定被撤销
- **一般瑕疵** (50-80分): 存在较多程序或实体问题，建议补正
- **格式问题** (20-50分): 基本合规，仅有少量格式问题
- **基本合规** (0-20分): 符合法定要求

## 示例案卷内容

上传案卷时，请包含以下内容以获得完整分析：

```
案件编号: (X)罚字[2024]001号
立案日期: 2024-01-15

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
依据《环境保护法》第六十三条...

【处罚决定】
罚款人民币50000元

【送达凭证】
当事人签字确认
```
