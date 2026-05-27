# backend/app/services/case_parser.py
"""
案卷结构解析服务
基于虚拟流程坐标映射，解析立案、调查、证据、告知、处罚、送达等流程节点
"""
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

@dataclass
class ProcessNode:
    """流程节点"""
    node_id: str
    node_type: str
    name: str
    date: Optional[str]
    content: str
    x_coord: float  # 虚拟流程横坐标
    y_coord: float  # 虚拟流程纵坐标
    issues: List[str]

class CaseParser:
    """案卷结构解析器"""
    
    # 虚拟流程坐标定义（x: 时间维度 0-100, y: 重要度维度 0-100）
    PROCESS_COORDS = {
        "filing": {"x": 5, "y": 60, "name": "立案"},
        "investigation": {"x": 20, "y": 80, "name": "调查取证"},
        "evidence": {"x": 35, "y": 85, "name": "证据采集"},
        "fact_determination": {"x": 45, "y": 70, "name": "事实认定"},
        "notice": {"x": 55, "y": 65, "name": "告知程序"},
        "hearing": {"x": 65, "y": 60, "name": "听证程序"},
        "penalty_decision": {"x": 75, "y": 75, "name": "处罚决定"},
        "delivery": {"x": 90, "y": 50, "name": "送达执行"},
    }
    
    def __init__(self):
        self.nodes = []
    
    def parse(self, case_content: str, case_type: str = "行政处罚") -> Dict[str, Any]:
        """
        解析案卷内容，提取流程节点
        :param case_content: 案卷文本内容
        :param case_type: 案件类型
        :return: 解析结果
        """
        self.nodes = []
        
        # 解析各个流程节点
        self._parse_filing(case_content)
        self._parse_investigation(case_content)
        self._parse_evidence(case_content)
        self._parse_fact_determination(case_content)
        self._parse_notice(case_content)
        self._parse_hearing(case_content)
        self._parse_penalty_decision(case_content)
        self._parse_delivery(case_content)
        
        # 构建虚拟流程坐标映射
        coord_map = self._build_coord_map()
        
        # 检测流程完整性
        completeness = self._check_completeness()
        
        return {
            "case_type": case_type,
            "node_count": len(self.nodes),
            "nodes": [self._node_to_dict(n) for n in self.nodes],
            "coord_map": coord_map,
            "completeness": completeness,
            "timeline": self._build_timeline(),
        }
    
    def _parse_filing(self, content: str):
        """解析立案阶段"""
        filing_patterns = [
            r"立案[审批]?[书表]?\s*[:：]\s*(.{10,200})",
            r"立案日期[：:]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
            r"案件编号[：:]\s*([A-Z0-9\-]{8,})",
            r"于\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)\s*立案",
        ]
        
        found_content = ""
        found_date = None
        
        for pattern in filing_patterns:
            match = re.search(pattern, content)
            if match:
                if "日期" in pattern or "立案" in match.group(0) and ("\d{4}" in match.group(0)):
                    found_date = match.group(1)
                else:
                    found_content = match.group(1)
        
        # 如果没找到日期，尝试从整体内容中提取
        if not found_date:
            date_match = re.search(r"(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)", content)
            if date_match:
                found_date = date_match.group(1)
        
        issues = []
        if not found_content and not found_date:
            issues.append("立案信息不完整")
        
        self.nodes.append(ProcessNode(
            node_id="filing",
            node_type="filing",
            name="立案",
            date=found_date,
            content=found_content or "未明确记载",
            x_coord=self.PROCESS_COORDS["filing"]["x"],
            y_coord=self.PROCESS_COORDS["filing"]["y"],
            issues=issues
        ))
    
    def _parse_investigation(self, content: str):
        """解析调查取证阶段"""
        investigation_patterns = [
            r"调查[笔录]?\s*[:：]?\s*(.{20,500})",
            r"调查人[员]?\s*[:：]\s*([^\n]{2,30})",
            r"调查日期[：:]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
            r"现场检查[笔录]?\s*(.{20,300})",
        ]
        
        found_content = ""
        found_date = None
        
        for pattern in investigation_patterns:
            match = re.search(pattern, content)
            if match:
                if "日期" in pattern:
                    found_date = match.group(1)
                else:
                    found_content += match.group(1)
        
        issues = []
        if not found_content:
            issues.append("调查取证记录缺失")
        
        self.nodes.append(ProcessNode(
            node_id="investigation",
            node_type="investigation",
            name="调查取证",
            date=found_date,
            content=found_content or "未进行有效调查取证",
            x_coord=self.PROCESS_COORDS["investigation"]["x"],
            y_coord=self.PROCESS_COORDS["investigation"]["y"],
            issues=issues
        ))
    
    def _parse_evidence(self, content: str):
        """解析证据采集阶段"""
        evidence_types = ["物证", "书证", "证人证言", "当事人陈述", "鉴定意见", "勘验笔录", "视听资料", "电子数据"]
        
        found_evidence = []
        for etype in evidence_types:
            pattern = rf"{etype}[：:]\s*(.{10,200})"
            match = re.search(pattern, content)
            if match:
                found_evidence.append({"type": etype, "content": match.group(1)})
        
        issues = []
        if len(found_evidence) < 2:
            issues.append(f"证据类型不足，仅发现{len(found_evidence)}种证据")
        
        self.nodes.append(ProcessNode(
            node_id="evidence",
            node_type="evidence",
            name="证据采集",
            date=None,
            content=f"已采集证据类型: {', '.join([e['type'] for e in found_evidence]) if found_evidence else '无'}",
            x_coord=self.PROCESS_COORDS["evidence"]["x"],
            y_coord=self.PROCESS_COORDS["evidence"]["y"],
            issues=issues
        ))
    
    def _parse_fact_determination(self, content: str):
        """解析事实认定阶段"""
        fact_patterns = [
            r"违法事实\s*[:：]\s*(.{20,500})",
            r"认定事实\s*[:：]\s*(.{20,500})",
            r"主要违法事实\s*[:：]\s*(.{20,500})",
        ]
        
        found_content = ""
        for pattern in fact_patterns:
            match = re.search(pattern, content)
            if match:
                found_content = match.group(1)
                break
        
        issues = []
        if not found_content:
            issues.append("事实认定部分缺失")
        
        self.nodes.append(ProcessNode(
            node_id="fact_determination",
            node_type="fact_determination",
            name="事实认定",
            date=None,
            content=found_content or "事实认定不明确",
            x_coord=self.PROCESS_COORDS["fact_determination"]["x"],
            y_coord=self.PROCESS_COORDS["fact_determination"]["y"],
            issues=issues
        ))
    
    def _parse_notice(self, content: str):
        """解析告知程序"""
        notice_patterns = [
            r"行政处罚告知书\s*(.{50,500})",
            r"告知[内容]?\s*[:：]\s*(.{20,300})",
            r"告知日期[：:]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
        ]
        
        found_content = ""
        found_date = None
        
        for pattern in notice_patterns:
            match = re.search(pattern, content)
            if match:
                if "日期" in pattern:
                    found_date = match.group(1)
                else:
                    found_content = match.group(1)
        
        issues = []
        if not found_content:
            issues.append("行政处罚告知缺失")
        
        self.nodes.append(ProcessNode(
            node_id="notice",
            node_type="notice",
            name="告知程序",
            date=found_date,
            content=found_content or "未有效告知",
            x_coord=self.PROCESS_COORDS["notice"]["x"],
            y_coord=self.PROCESS_COORDS["notice"]["y"],
            issues=issues
        ))
    
    def _parse_hearing(self, content: str):
        """解析听证程序"""
        hearing_patterns = [
            r"听证[笔录]?\s*(.{20,300})",
            r"听证[日期]?\s*[:：]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
            r"听证[申请]?\s*[:：]\s*(是|否|已|未)",
        ]
        
        found_content = ""
        found_date = None
        has_hearing = "听证" in content
        
        if has_hearing:
            for pattern in hearing_patterns:
                match = re.search(pattern, content)
                if match:
                    if "日期" in pattern:
                        found_date = match.group(1)
                    else:
                        found_content = match.group(1)
        
        issues = []
        # 注意：听证程序不是所有案件都必须，此处仅作记录
        
        self.nodes.append(ProcessNode(
            node_id="hearing",
            node_type="hearing",
            name="听证程序",
            date=found_date,
            content="已举行听证" if has_hearing else "未涉及听证程序",
            x_coord=self.PROCESS_COORDS["hearing"]["x"],
            y_coord=self.PROCESS_COORDS["hearing"]["y"],
            issues=issues
        ))
    
    def _parse_penalty_decision(self, content: str):
        """解析处罚决定"""
        penalty_patterns = [
            r"处罚决定[书]?\s*(.{50,500})",
            r"决定如下\s*[:：]\s*(.{50,500})",
            r"罚款[金额]?\s*[:：]\s*(\d+(?:\.\d+)?\s*(?:元|万元))",
            r"责令\s*(.{10,100})",
        ]
        
        found_content = ""
        penalty_amount = None
        
        for pattern in penalty_patterns:
            match = re.search(pattern, content)
            if match:
                if "罚款" in pattern and ("元" in match.group(0) or "万元" in match.group(0)):
                    penalty_amount = match.group(1)
                else:
                    found_content = match.group(0)
        
        issues = []
        if not found_content:
            issues.append("处罚决定不明确")
        
        self.nodes.append(ProcessNode(
            node_id="penalty_decision",
            node_type="penalty_decision",
            name="处罚决定",
            date=None,
            content=found_content or f"罚款金额: {penalty_amount}" if penalty_amount else "处罚决定内容不明确",
            x_coord=self.PROCESS_COORDS["penalty_decision"]["x"],
            y_coord=self.PROCESS_COORDS["penalty_decision"]["y"],
            issues=issues
        ))
    
    def _parse_delivery(self, content: str):
        """解析送达执行阶段"""
        delivery_patterns = [
            r"送达[凭证]?\s*(.{10,200})",
            r"送达日期[：:]\s*(\d{4}[年\-]\d{1,2}[月\-]\d{1,2}[日]?)",
            r"当事人[签字]?\s*(.{10,100})",
        ]
        
        found_content = ""
        found_date = None
        
        for pattern in delivery_patterns:
            match = re.search(pattern, content)
            if match:
                if "日期" in pattern:
                    found_date = match.group(1)
                else:
                    found_content = match.group(1)
        
        issues = []
        if not found_content and not found_date:
            issues.append("送达凭证缺失")
        
        self.nodes.append(ProcessNode(
            node_id="delivery",
            node_type="delivery",
            name="送达执行",
            date=found_date,
            content=found_content or "未明确记载送达情况",
            x_coord=self.PROCESS_COORDS["delivery"]["x"],
            y_coord=self.PROCESS_COORDS["delivery"]["y"],
            issues=issues
        ))
    
    def _build_coord_map(self) -> Dict[str, Dict[str, float]]:
        """构建虚拟流程坐标映射"""
        return {
            node_id: {"x": coords["x"], "y": coords["y"], "name": coords["name"]}
            for node_id, coords in self.PROCESS_COORDS.items()
        }
    
    def _check_completeness(self) -> Dict[str, Any]:
        """检测流程完整性"""
        required_nodes = ["filing", "investigation", "evidence", "fact_determination", "notice", "penalty_decision", "delivery"]
        existing_nodes = set(n.node_id for n in self.nodes)
        
        missing = [nid for nid in required_nodes if nid not in existing_nodes]
        completeness_score = (len(existing_nodes) / len(required_nodes)) * 100
        
        return {
            "score": completeness_score,
            "missing_nodes": missing,
            "is_complete": len(missing) == 0
        }
    
    def _build_timeline(self) -> List[Dict[str, Any]]:
        """构建时间线"""
        timeline = []
        for node in sorted(self.nodes, key=lambda n: n.x_coord):
            if node.date:
                timeline.append({
                    "node_id": node.node_id,
                    "node_name": node.name,
                    "date": node.date
                })
        return timeline
    
    def _node_to_dict(self, node: ProcessNode) -> Dict[str, Any]:
        """将节点转为字典"""
        return {
            "node_id": node.node_id,
            "node_type": node.node_type,
            "name": node.name,
            "date": node.date,
            "content": node.content,
            "x_coord": node.x_coord,
            "y_coord": node.y_coord,
            "issues": node.issues
        }
