# backend/app/services/case_risk_scorer.py
"""
案卷风险熵评分服务
输出重大瑕疵、一般瑕疵、格式问题，多维风险耦合
"""
import math
from typing import Dict, List, Any

class CaseRiskScorer:
    """案卷风险熵评分器"""
    
    # 风险维度权重
    RISK_DIMENSIONS = {
        "fact_risk": 0.30,       # 事实认定风险
        "evidence_risk": 0.25,   # 证据风险
        "procedure_risk": 0.20, # 程序风险
        "discretion_risk": 0.15, # 裁量风险
        "format_risk": 0.10,    # 格式风险
    }
    
    # 风险等级阈值
    RISK_LEVELS = {
        "重大瑕疵": (80, 100),
        "一般瑕疵": (50, 80),
        "格式问题": (20, 50),
        "基本合规": (0, 20),
    }
    
    # 风险等级描述
    RISK_LEVEL_DESCRIPTIONS = {
        "重大瑕疵": "案卷存在严重违法问题，可能导致处罚决定被撤销或责令重新处理",
        "一般瑕疵": "案卷存在较多程序或实体问题，建议补正后重新审查",
        "格式问题": "案卷基本合规，仅有少量格式或形式问题",
        "基本合规": "案卷符合法定要求，可以继续后续程序",
    }
    
    def __init__(self):
        self.risk_scores = {}
        self.risk_details = {}
    
    def score(self, evidence_result: Dict, discretion_result: Dict, 
              procedure_result: Dict, similarity_result: Dict,
              case_content: str) -> Dict[str, Any]:
        """
        计算案卷风险熵评分
        :param evidence_result: 证据链检测结果
        :param discretion_result: 裁量基准匹配结果
        :param procedure_result: 程序合法性检测结果
        :param similarity_result: 同案相似度检测结果
        :param case_content: 案卷内容
        :return: 风险评分结果
        """
        self.risk_scores = {}
        self.risk_details = {}
        
        # 1. 计算事实认定风险
        fact_risk = self._calculate_fact_risk(evidence_result, case_content)
        self.risk_scores["fact_risk"] = fact_risk["score"]
        self.risk_details["fact_risk"] = fact_risk
        
        # 2. 计算证据风险
        evidence_risk = self._calculate_evidence_risk(evidence_result)
        self.risk_scores["evidence_risk"] = evidence_risk["score"]
        self.risk_details["evidence_risk"] = evidence_risk
        
        # 3. 计算程序风险
        procedure_risk = self._calculate_procedure_risk(procedure_result)
        self.risk_scores["procedure_risk"] = procedure_risk["score"]
        self.risk_details["procedure_risk"] = procedure_risk
        
        # 4. 计算裁量风险
        discretion_risk = self._calculate_discretion_risk(discretion_result)
        self.risk_scores["discretion_risk"] = discretion_risk["score"]
        self.risk_details["discretion_risk"] = discretion_risk
        
        # 5. 计算格式风险
        format_risk = self._calculate_format_risk(case_content)
        self.risk_scores["format_risk"] = format_risk["score"]
        self.risk_details["format_risk"] = format_risk
        
        # 6. 计算综合风险熵（加权求和）
        total_risk = self._calculate_total_risk()
        
        # 7. 确定风险等级
        risk_level = self._determine_risk_level(total_risk)
        
        # 8. 生成风险雷达图数据
        radar_data = self._generate_radar_data()
        
        # 9. 生成风险汇总
        risk_summary = self._generate_risk_summary()
        
        return {
            "total_risk_score": total_risk,
            "risk_level": risk_level,
            "risk_description": self.RISK_LEVEL_DESCRIPTIONS.get(risk_level, ""),
            "dimension_scores": self.risk_scores,
            "dimension_details": self.risk_details,
            "radar_data": radar_data,
            "risk_summary": risk_summary,
            "completeness": evidence_result.get("is_complete", False),
            "legality": procedure_result.get("is_legal", False),
        }
    
    def _calculate_fact_risk(self, evidence_result: Dict, case_content: str) -> Dict[str, Any]:
        """计算事实认定风险"""
        score = 0.0
        details = []
        
        # 检查违法事实是否明确
        has_clear_fact = "违法事实" in case_content or "认定事实" in case_content
        if not has_clear_fact:
            score += 30
            details.append({"type": "fact_unclear", "score": 30, "message": "违法事实不明确"})
        
        # 检查证据链是否完整（事实认定依赖于证据链）
        if not evidence_result.get("is_complete", True):
            score += 35
            details.append({"type": "evidence_chain_incomplete", "score": 35, "message": "证据链不完整，事实认定依据不足"})
        
        # 检查证据充分性
        evidence_sufficiency = evidence_result.get("evidence_sufficiency", {})
        if not evidence_sufficiency.get("is_sufficient", True):
            score += 20
            details.append({
                "type": "evidence_insufficient",
                "score": 20,
                "message": f"证据充分性不足，仅有{evidence_sufficiency.get('evidence_count', 0)}项证据"
            })
        
        # 检查事实认定是否有证据支撑
        chain_elements = evidence_result.get("chain_elements", {})
        facts = chain_elements.get("fact", [])
        evidence = chain_elements.get("evidence", [])
        
        if not facts and not evidence:
            score += 25
            details.append({"type": "no_fact_or_evidence", "score": 25, "message": "事实和证据均缺失"})
        
        return {
            "score": min(100, score),
            "details": details,
            "weight": self.RISK_DIMENSIONS["fact_risk"],
        }
    
    def _calculate_evidence_risk(self, evidence_result: Dict) -> Dict[str, Any]:
        """计算证据风险"""
        score = 0.0
        details = []
        
        # 证据链完整性
        chain_completeness = evidence_result.get("chain_completeness", {})
        if not chain_completeness.get("is_complete", True):
            score += 40
            missing = chain_completeness.get("missing_elements", [])
            details.append({
                "type": "evidence_chain_defect",
                "score": 40,
                "message": f"证据链缺失环节: {', '.join(missing)}"
            })
        
        # 证据充分性
        evidence_sufficiency = evidence_result.get("evidence_sufficiency", {})
        if not evidence_sufficiency.get("is_sufficient", True):
            score += 30
            details.append({
                "type": "insufficient_evidence",
                "score": 30,
                "message": "证据不充分"
            })
        
        # 高优先级证据占比
        high_priority_ratio = evidence_sufficiency.get("high_priority_ratio", 1.0)
        if high_priority_ratio < 0.3:
            score += 15
            details.append({
                "type": "low_priority_evidence",
                "score": 15,
                "message": "高优先级证据占比过低"
            })
        
        # 证据类型多样性
        type_diversity = evidence_sufficiency.get("type_diversity", 0)
        if type_diversity < 2:
            score += 15
            details.append({
                "type": "low_evidence_diversity",
                "score": 15,
                "message": "证据类型单一"
            })
        
        return {
            "score": min(100, score),
            "details": details,
            "weight": self.RISK_DIMENSIONS["evidence_risk"],
        }
    
    def _calculate_procedure_risk(self, procedure_result: Dict) -> Dict[str, Any]:
        """计算程序风险"""
        score = 100 - procedure_result.get("score", 100)
        issues = procedure_result.get("issues", [])
        
        details = []
        for issue in issues:
            details.append({
                "type": issue.get("type", "unknown"),
                "score": 20 if issue.get("severity") == "high" else 10,
                "message": issue.get("message", "")
            })
        
        return {
            "score": min(100, score),
            "details": details,
            "weight": self.RISK_DIMENSIONS["procedure_risk"],
        }
    
    def _calculate_discretion_risk(self, discretion_result: Dict) -> Dict[str, Any]:
        """计算裁量风险"""
        score = 0.0
        details = []
        
        # 裁量偏差
        deviation = discretion_result.get("deviation")
        if deviation is not None:
            score += abs(deviation) * 50
            if abs(deviation) > 0.3:
                details.append({
                    "type": "significant_deviation",
                    "score": abs(deviation) * 50,
                    "message": f"裁量偏差过大: {deviation*100:.1f}%"
                })
        
        # 裁量异常
        if discretion_result.get("is_abnormal", False):
            score += 30
            details.append({
                "type": "discretion_abnormal",
                "score": 30,
                "message": "裁量幅度异常"
            })
        
        # 匹配等级
        match_level = discretion_result.get("match_level", "good")
        if match_level == "abnormal":
            score += 20
            details.append({
                "type": "poor_discretion_match",
                "score": 20,
                "message": "裁量基准匹配等级差"
            })
        elif match_level == "poor":
            score += 10
            details.append({
                "type": "acceptable_discretion_match",
                "score": 10,
                "message": "裁量基准匹配等级可接受"
            })
        
        return {
            "score": min(100, score),
            "details": details,
            "weight": self.RISK_DIMENSIONS["discretion_risk"],
        }
    
    def _calculate_format_risk(self, case_content: str) -> Dict[str, Any]:
        """计算格式风险"""
        score = 0.0
        details = []
        
        # 检查必要文书格式
        required_formats = [
            ("案件编号", "案件编号格式"),
            ("当事人", "当事人信息"),
            ("日期", "日期格式"),
        ]
        
        for keyword, format_name in required_formats:
            if keyword not in case_content:
                score += 8
                details.append({
                    "type": "format_missing",
                    "score": 8,
                    "message": f"文书缺少必要格式: {format_name}"
                })
        
        # 检查基本长度
        if len(case_content) < 100:
            score += 20
            details.append({
                "type": "content_too_short",
                "score": 20,
                "message": "案卷内容过短，可能不完整"
            })
        
        return {
            "score": min(100, score),
            "details": details,
            "weight": self.RISK_DIMENSIONS["format_risk"],
        }
    
    def _calculate_total_risk(self) -> float:
        """计算加权总风险"""
        total = 0.0
        for dim, dim_score in self.risk_scores.items():
            weight = self.RISK_DIMENSIONS.get(dim, 0)
            total += dim_score * weight
        
        return round(total, 2)
    
    def _determine_risk_level(self, total_risk: float) -> str:
        """确定风险等级"""
        for level, (min_score, max_score) in self.RISK_LEVELS.items():
            if min_score <= total_risk < max_score:
                return level
        return "基本合规"
    
    def _generate_radar_data(self) -> Dict[str, Any]:
        """生成雷达图数据"""
        dimensions = list(self.RISK_DIMENSIONS.keys())
        scores = [self.risk_scores.get(dim, 0) for dim in dimensions]
        
        dimension_labels = {
            "fact_risk": "事实风险",
            "evidence_risk": "证据风险",
            "procedure_risk": "程序风险",
            "discretion_risk": "裁量风险",
            "format_risk": "格式风险",
        }
        
        return {
            "dimensions": [dimension_labels.get(d, d) for d in dimensions],
            "scores": scores,
            "max_score": 100,
        }
    
    def _generate_risk_summary(self) -> Dict[str, Any]:
        """生成风险汇总"""
        all_issues = []
        
        for dim, details in self.risk_details.items():
            for issue in details.get("details", []):
                issue["dimension"] = dim
                all_issues.append(issue)
        
        # 按分数排序
        all_issues.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # 分类汇总
        major_issues = [i for i in all_issues if i.get("score", 0) >= 30]
        general_issues = [i for i in all_issues if 15 <= i.get("score", 0) < 30]
        format_issues = [i for i in all_issues if i.get("score", 0) < 15]
        
        return {
            "major_issues": major_issues,
            "general_issues": general_issues,
            "format_issues": format_issues,
            "total_issues": len(all_issues),
        }
