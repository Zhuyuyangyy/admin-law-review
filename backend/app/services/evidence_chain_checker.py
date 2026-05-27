# backend/app/services/evidence_chain_checker.py
"""
证据链完整性检测服务
判断事实—证据—法条—处罚是否闭环，检测证据充分性
"""
import re
from typing import Dict, List, Any, Set, Tuple

class EvidenceChainChecker:
    """证据链完整性检测器"""
    
    # 证据充分性最低标准（每类事实至少需要的证据数量）
    MIN_EVIDENCE_PER_FACT = 2
    
    # 证据链闭环必需元素
    REQUIRED_CHAIN_ELEMENTS = [
        "fact",      # 违法事实
        "evidence",  # 证据材料
        "legal_basis", # 法律依据
        "penalty",   # 处罚结果
    ]
    
    # 证据类型优先级（用于判断证据充分性）
    EVIDENCE_PRIORITY = {
        "物证": 10,
        "书证": 9,
        "鉴定意见": 8,
        "勘验笔录": 7,
        "视听资料": 6,
        "电子数据": 5,
        "证人证言": 4,
        "当事人陈述": 3,
    }
    
    def __init__(self):
        self.issues = []
        self.chain_elements = {}
    
    def check(self, case_content: str, parsed_nodes: Dict[str, Any]) -> Dict[str, Any]:
        """
        检测证据链完整性
        :param case_content: 案卷内容
        :param parsed_nodes: 案卷解析结果
        :return: 检测结果
        """
        self.issues = []
        self.chain_elements = {}
        
        # 1. 提取违法事实
        facts = self._extract_facts(case_content)
        self.chain_elements["fact"] = facts
        
        # 2. 提取证据材料
        evidence = self._extract_evidence(case_content)
        self.chain_elements["evidence"] = evidence
        
        # 3. 提取法律依据
        legal_basis = self._extract_legal_basis(case_content)
        self.chain_elements["legal_basis"] = legal_basis
        
        # 4. 提取处罚结果
        penalty = self._extract_penalty(case_content)
        self.chain_elements["penalty"] = penalty
        
        # 5. 检测证据链闭环
        chain_completeness = self._check_chain_completeness()
        
        # 6. 检测证据充分性
        evidence_sufficiency = self._check_evidence_sufficiency(facts, evidence)
        
        # 7. 计算综合评分
        score = self._calculate_score(chain_completeness, evidence_sufficiency)
        
        return {
            "is_complete": chain_completeness["is_complete"] and evidence_sufficiency["is_sufficient"],
            "score": score,
            "chain_completeness": chain_completeness,
            "evidence_sufficiency": evidence_sufficiency,
            "chain_elements": self.chain_elements,
            "issues": self.issues,
        }
    
    def _extract_facts(self, content: str) -> List[str]:
        """提取违法事实"""
        facts = []
        
        patterns = [
            r"违法事实\s*[:：]\s*(.{50,500})",
            r"认定事实\s*[:：]\s*(.{50,500})",
            r"主要事实\s*[:：]\s*(.{50,500})",
            r"当事人.*?(?:实施了|进行了|存在)(.{20,200})",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            facts.extend(matches)
        
        return facts
    
    def _extract_evidence(self, content: str) -> List[Dict[str, Any]]:
        """提取证据材料"""
        evidence_list = []
        
        evidence_types = list(self.EVIDENCE_PRIORITY.keys())
        
        for etype in evidence_types:
            pattern = rf"{etype}[：:]\s*[\"']?([^\"'。\n]{10,300})[\"']?"
            matches = re.findall(pattern, content)
            for match in matches:
                evidence_list.append({
                    "type": etype,
                    "content": match.strip(),
                    "priority": self.EVIDENCE_PRIORITY[etype]
                })
        
        # 如果通过类型匹配不到，尝试通用模式
        if not evidence_list:
            generic_patterns = [
                r"证据[材料]?\s*(?:一|二|三|四|五|六|七|八|九|十|[0-9]+)\s*[:：]\s*(.{20,300})",
                r"下列证据\s*(.{100,1000})",
                r"证据清单\s*(.{100,1000})",
            ]
            for pattern in generic_patterns:
                match = re.search(pattern, content)
                if match:
                    evidence_list.append({
                        "type": "其他证据",
                        "content": match.group(1).strip(),
                        "priority": 1
                    })
        
        return evidence_list
    
    def _extract_legal_basis(self, content: str) -> List[str]:
        """提取法律依据"""
        legal_basis = []
        
        patterns = [
            r"依据[《\[\]]?([^《\[\]]{5,30})[》\]]?\s*(?:第\d+条|第\d+款|第\d+项)",
            r"违反[《\[\]]?([^《\[\]]{5,30})[》\]]?\s*(?:第\d+条|第\d+款)",
            r"《([^《\[\]]{3,20})》\s*(?:第\d+条|第\d+款|第\d+项)",
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content)
            legal_basis.extend(matches)
        
        return legal_basis
    
    def _extract_penalty(self, content: str) -> Dict[str, Any]:
        """提取处罚结果"""
        penalty = {}
        
        # 罚款金额
        amount_patterns = [
            r"罚款[金额]?\s*[:：]\s*(\d+(?:\.\d+)?)\s*(?:元|万元)?",
            r"处以罚款\s*(\d+(?:\.\d+)?)\s*(?:元|万元)",
            r"罚款人民币\s*(\d+(?:\.\d+)?)\s*(?:元|万元)",
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, content)
            if match:
                amount_str = match.group(1)
                penalty["amount"] = float(amount_str)
                break
        
        # 处罚类型
        penalty_types = ["罚款", "责令停产停业", "吊销许可证", "没收违法所得", "警告", "行政拘留"]
        for ptype in penalty_types:
            if ptype in content:
                penalty["type"] = ptype
                break
        
        return penalty
    
    def _check_chain_completeness(self) -> Dict[str, Any]:
        """检测证据链各环节完整性"""
        missing_elements = []
        
        for element in self.REQUIRED_CHAIN_ELEMENTS:
            if element == "fact":
                if not self.chain_elements.get("fact"):
                    missing_elements.append("违法事实")
            elif element == "evidence":
                if not self.chain_elements.get("evidence"):
                    missing_elements.append("证据材料")
            elif element == "legal_basis":
                if not self.chain_elements.get("legal_basis"):
                    missing_elements.append("法律依据")
            elif element == "penalty":
                if not self.chain_elements.get("penalty"):
                    missing_elements.append("处罚结果")
        
        is_complete = len(missing_elements) == 0
        completeness_score = ((len(self.REQUIRED_CHAIN_ELEMENTS) - len(missing_elements)) 
                              / len(self.REQUIRED_CHAIN_ELEMENTS)) * 100
        
        if missing_elements:
            self.issues.append({
                "type": "evidence_chain_incomplete",
                "severity": "high",
                "message": f"证据链不完整，缺失环节: {', '.join(missing_elements)}",
                "missing_elements": missing_elements
            })
        
        return {
            "is_complete": is_complete,
            "score": completeness_score,
            "missing_elements": missing_elements
        }
    
    def _check_evidence_sufficiency(self, facts: List[str], evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检测证据充分性"""
        issues = []
        
        if not facts:
            issues.append({
                "type": "no_fact_found",
                "severity": "high",
                "message": "未找到违法事实认定"
            })
            return {"is_sufficient": False, "score": 0, "issues": issues}
        
        if not evidence:
            issues.append({
                "type": "no_evidence_found",
                "severity": "high",
                "message": "未找到证据材料"
            })
            self.issues.append({
                "type": "evidence_missing",
                "severity": "high",
                "message": "证据材料缺失"
            })
            return {"is_sufficient": False, "score": 0, "issues": issues}
        
        # 计算每个事实的证据支撑
        evidence_count_by_type = {}
        for ev in evidence:
            ev_type = ev["type"]
            evidence_count_by_type[ev_type] = evidence_count_by_type.get(ev_type, 0) + 1
        
        # 检查证据类型多样性
        type_diversity = len(evidence_count_by_type)
        diversity_score = min(type_diversity / 3 * 100, 100)  # 至少3种证据类型为满分
        
        # 检查高优先级证据占比
        high_priority_evidence = [e for e in evidence if e["priority"] >= 7]
        high_priority_ratio = len(high_priority_evidence) / len(evidence) if evidence else 0
        
        # 综合评分
        sufficiency_score = (
            diversity_score * 0.4 + 
            high_priority_ratio * 100 * 0.6
        )
        
        is_sufficient = (
            type_diversity >= 2 and 
            len(evidence) >= self.MIN_EVIDENCE_PER_FACT and 
            sufficiency_score >= 50
        )
        
        if type_diversity < 2:
            issues.append({
                "type": "low_evidence_diversity",
                "severity": "medium",
                "message": f"证据类型单一，仅有{type_diversity}种证据类型"
            })
            self.issues.append({
                "type": "evidence_type_limited",
                "severity": "medium",
                "message": f"证据类型不足，建议增加不同类型证据"
            })
        
        if len(evidence) < self.MIN_EVIDENCE_PER_FACT:
            issues.append({
                "type": "insufficient_evidence_count",
                "severity": "medium",
                "message": f"证据数量不足，仅有{len(evidence)}项"
            })
        
        if high_priority_ratio < 0.3:
            issues.append({
                "type": "low_high_priority_evidence",
                "severity": "medium",
                "message": "高优先级证据（物证、书证、鉴定意见）占比过低"
            })
        
        return {
            "is_sufficient": is_sufficient,
            "score": sufficiency_score,
            "evidence_count": len(evidence),
            "type_diversity": type_diversity,
            "high_priority_ratio": high_priority_ratio,
            "issues": issues
        }
    
    def _calculate_score(self, chain_completeness: Dict, evidence_sufficiency: Dict) -> float:
        """计算综合评分"""
        return (
            chain_completeness["score"] * 0.5 + 
            evidence_sufficiency["score"] * 0.5
        )
