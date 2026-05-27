# backend/app/services/procedure_legal_checker.py
"""
程序合法性校验服务
检查期限、告知、签章、送达等程序问题，时间线合法性检测
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta

class ProcedureLegalChecker:
    """程序合法性校验器"""
    
    # 法定时限标准（单位：天）
    LEGAL_DEADLINES = {
        "investigation_to_decision": 30,      # 调查到决定30天
        "notice_to_decision": 3,               # 告知到决定3天（当事人放弃陈述申辩）
        "decision_to_delivery": 7,             # 决定到送达7天
        "filing_to_investigation": 7,          # 立案到开展调查7天
        "max_extendable_days": 30,             # 延期最大天数
    }
    
    # 程序节点定义
    PROCEDURE_NODES = [
        ("filing", "立案"),
        ("investigation", "调查取证"),
        ("evidence_collection", "证据采集"),
        ("fact_determination", "事实认定"),
        ("notice", "告知程序"),
        ("hearing", "听证程序"),
        ("penalty_decision", "处罚决定"),
        ("delivery", "送达执行"),
    ]
    
    def __init__(self):
        self.issues = []
        self.timeline = []
    
    def check(self, case_content: str, parsed_nodes: Dict[str, Any]) -> Dict[str, Any]:
        """
        校验程序合法性
        :param case_content: 案卷内容
        :param parsed_nodes: 解析后的节点
        :return: 校验结果
        """
        self.issues = []
        self.timeline = []
        
        # 1. 解析时间节点
        self._parse_timeline(case_content, parsed_nodes)
        
        # 2. 检查期限合法性
        deadline_issues = self._check_deadlines()
        
        # 3. 检查告知程序
        notice_issues = self._check_notice_procedure(case_content)
        
        # 4. 检查签章程序
        signature_issues = self._check_signature_procedure(case_content)
        
        # 5. 检查送达程序
        delivery_issues = self._check_delivery_procedure(case_content)
        
        # 6. 计算综合评分
        all_issues = deadline_issues + notice_issues + signature_issues + delivery_issues
        score = self._calculate_score(all_issues)
        
        is_legal = len([i for i in all_issues if i.get("severity") == "high"]) == 0
        
        return {
            "is_legal": is_legal,
            "score": score,
            "issues": all_issues,
            "timeline": self.timeline,
        }
    
    def _parse_timeline(self, content: str, parsed_nodes: Dict[str, Any]):
        """解析时间线"""
        # 从解析节点中提取时间
        for node in parsed_nodes.get("nodes", []):
            if node.get("date"):
                self.timeline.append({
                    "node_id": node["node_id"],
                    "node_name": node["name"],
                    "date_str": node["date"],
                    "date_obj": self._parse_date(node["date"])
                })
        
        # 从内容中提取额外时间点
        date_patterns = {
            "investigation_start": r"调查开始[日期]?\s*[:：]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
            "investigation_end": r"调查结束[日期]?\s*[:：]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
            "decision_date": r"决定[日期]?\s*[:：]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
            "notice_date": r"告知[日期]?\s*[:：]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
            "delivery_date": r"送达[日期]?\s*[:：]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
        }
        
        for key, pattern in date_patterns.items():
            match = re.search(pattern, content)
            if match:
                date_str = match.group(1)
                # 判断属于哪个节点
                node_map = {
                    "investigation_start": "investigation",
                    "investigation_end": "investigation",
                    "decision_date": "penalty_decision",
                    "notice_date": "notice",
                    "delivery_date": "delivery",
                }
                node_id = node_map.get(key, key)
                
                # 检查是否已存在
                existing = next((t for t in self.timeline if t["node_id"] == node_id), None)
                if not existing:
                    node_name = next((name for nid, name in self.PROCEDURE_NODES if nid == node_id), key)
                    self.timeline.append({
                        "node_id": node_id,
                        "node_name": node_name,
                        "date_str": date_str,
                        "date_obj": self._parse_date(date_str)
                    })
        
        # 按日期排序
        self.timeline.sort(key=lambda x: x["date_obj"] if x["date_obj"] else datetime.max)
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """解析日期字符串"""
        if not date_str:
            return None
        
        formats = [
            "%Y年%m月%d日",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%Y.%m.%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        return None
    
    def _check_deadlines(self) -> List[Dict[str, Any]]:
        """检查期限合法性"""
        issues = []
        
        if len(self.timeline) < 2:
            return [{
                "type": "insufficient_timeline",
                "severity": "medium",
                "message": "时间线信息不足，无法进行期限检测"
            }]
        
        # 检查各阶段时限
        stage_pairs = [
            ("filing", "investigation", "filing_to_investigation"),
            ("investigation", "penalty_decision", "investigation_to_decision"),
            ("notice", "penalty_decision", "notice_to_decision"),
            ("penalty_decision", "delivery", "decision_to_delivery"),
        ]
        
        for start_node, end_node, deadline_key in stage_pairs:
            start_date = self._get_date(start_node)
            end_date = self._get_date(end_node)
            
            if start_date and end_date:
                days = (end_date - start_date).days
                max_days = self.LEGAL_DEADLINES.get(deadline_key, 30)
                
                if days > max_days:
                    issues.append({
                        "type": "deadline_exceeded",
                        "severity": "high",
                        "message": f"{self._get_node_name(start_node)}到{self._get_node_name(end_node)}超过法定时限{ max_days}天，实际{days}天",
                        "stage": f"{start_node}_to_{end_node}",
                        "days": days,
                        "max_days": max_days
                    })
        
        return issues
    
    def _check_notice_procedure(self, content: str) -> List[Dict[str, Any]]:
        """检查告知程序"""
        issues = []
        
        # 检查是否包含告知书
        has_notice = "告知" in content or "告知书" in content
        
        if not has_notice:
            issues.append({
                "type": "notice_missing",
                "severity": "high",
                "message": "缺少行政处罚告知程序"
            })
            return issues
        
        # 检查告知内容完整性
        notice_elements = [
            ("当事人", "当事人信息"),
            ("违法事实", "违法事实"),
            ("处罚依据", "处罚依据"),
            ("处罚内容", "处罚内容"),
            ("陈述申辩", "陈述申辩权"),
        ]
        
        for keyword, element_name in notice_elements:
            if keyword not in content:
                issues.append({
                    "type": "notice_incomplete",
                    "severity": "medium",
                    "message": f"告知书缺少必要内容: {element_name}"
                })
        
        return issues
    
    def _check_signature_procedure(self, content: str) -> List[Dict[str, Any]]:
        """检查签章程序"""
        issues = []
        
        # 检查签章元素
        signature_elements = [
            ("当事人", "当事人签字"),
            ("执法人员", "执法人员签章"),
            ("负责人", "负责人签章"),
            ("行政机关", "行政机关印章"),
        ]
        
        missing_signatures = []
        for keyword, element_name in signature_elements:
            if keyword not in content:
                missing_signatures.append(element_name)
        
        if missing_signatures:
            issues.append({
                "type": "signature_missing",
                "severity": "medium",
                "message": f"文书缺少签章: {', '.join(missing_signatures)}"
            })
        
        return issues
    
    def _check_delivery_procedure(self, content: str) -> List[Dict[str, Any]]:
        """检查送达程序"""
        issues = []
        
        # 检查送达凭证
        delivery_elements = [
            ("送达", "送达记录"),
            ("签收", "签收凭证"),
        ]
        
        for keyword, element_name in delivery_elements:
            if keyword not in content:
                issues.append({
                    "type": "delivery_incomplete",
                    "severity": "medium",
                    "message": f"送达程序缺少: {element_name}"
                })
        
        return issues
    
    def _calculate_score(self, issues: List[Dict[str, Any]]) -> float:
        """计算程序合法性评分"""
        if not issues:
            return 100.0
        
        base_score = 100.0
        
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity == "high":
                base_score -= 20
            elif severity == "medium":
                base_score -= 10
            else:
                base_score -= 5
        
        return max(0, base_score)
    
    def _get_date(self, node_id: str) -> Optional[datetime]:
        """获取指定节点日期"""
        for t in self.timeline:
            if t["node_id"] == node_id:
                return t["date_obj"]
        return None
    
    def _get_node_name(self, node_id: str) -> str:
        """获取节点名称"""
        for nid, name in self.PROCEDURE_NODES:
            if nid == node_id:
                return name
        return node_id
