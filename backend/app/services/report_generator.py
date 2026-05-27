# backend/app/services/report_generator.py
"""
风险分级报告生成服务
输出问题清单、责任节点、整改建议
"""
import json
from typing import Dict, List, Any
from datetime import datetime

class ReportGenerator:
    """风险分级报告生成器"""
    
    def __init__(self):
        self.report_sections = []
    
    def generate(self, case_info: Dict, analysis_result: Dict,
                 evidence_result: Dict, discretion_result: Dict,
                 procedure_result: Dict, similarity_result: Dict,
                 risk_result: Dict) -> Dict[str, Any]:
        """
        生成完整的风险分级报告
        """
        report = {
            "report_title": "行政执法案卷合规评查报告",
            "report_id": f"RPT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "generated_at": datetime.now().strftime("%Y年%m月%d日 %H:%M:%S"),
            "case_info": self._generate_case_info(case_info),
            "executive_summary": self._generate_executive_summary(risk_result),
            "risk_assessment": self._generate_risk_assessment(risk_result),
            "issues_list": self._generate_issues_list(evidence_result, discretion_result, procedure_result, risk_result),
            "responsibility_nodes": self._generate_responsibility_nodes(evidence_result, discretion_result, procedure_result),
            "rectification_suggestions": self._generate_rectification_suggestions(
                evidence_result, discretion_result, procedure_result, risk_result
            ),
            "similar_case_comparison": self._generate_similar_case_comparison(similarity_result),
            "conclusion": self._generate_conclusion(risk_result),
        }
        
        return report
    
    def _generate_case_info(self, case_info: Dict) -> Dict[str, Any]:
        """生成案件基本信息"""
        return {
            "case_number": case_info.get("case_number", "未知"),
            "case_type": case_info.get("case_type", "行政处罚"),
            "filing_date": case_info.get("filing_date", "未知"),
            "status": case_info.get("status", "待评查"),
        }
    
    def _generate_executive_summary(self, risk_result: Dict) -> Dict[str, Any]:
        """生成执行摘要"""
        risk_level = risk_result.get("risk_level", "未知")
        total_score = risk_result.get("total_risk_score", 0)
        
        summary_templates = {
            "重大瑕疵": f"该案卷综合风险得分为{total_score}分，风险等级为【{risk_level}】。案卷存在严重违法问题，证据链存在重大缺陷，建议立即启动复查程序。",
            "一般瑕疵": f"该案卷综合风险得分为{total_score}分，风险等级为【{risk_level}】。案卷存在较多程序或实体问题，建议在规定时间内完成补正。",
            "格式问题": f"该案卷综合风险得分为{total_score}分，风险等级为【{risk_level}】。案卷基本合规，仅有少量格式问题需要修正。",
            "基本合规": f"该案卷综合风险得分为{total_score}分，风险等级为【{risk_level}】。案卷符合法定要求，可以继续后续程序。",
        }
        
        return {
            "risk_level": risk_level,
            "total_score": total_score,
            "summary": summary_templates.get(risk_level, f"综合风险评分: {total_score}"),
            "is_qualified": risk_level in ["格式问题", "基本合规"],
        }
    
    def _generate_risk_assessment(self, risk_result: Dict) -> Dict[str, Any]:
        """生成风险评估详情"""
        radar_data = risk_result.get("radar_data", {})
        
        return {
            "total_score": risk_result.get("total_risk_score", 0),
            "risk_level": risk_result.get("risk_level", "未知"),
            "risk_description": risk_result.get("risk_description", ""),
            "dimension_scores": risk_result.get("dimension_scores", {}),
            "radar_chart": {
                "labels": radar_data.get("dimensions", []),
                "data": radar_data.get("scores", []),
            },
            "completeness": risk_result.get("completeness", False),
            "legality": risk_result.get("legality", False),
        }
    
    def _generate_issues_list(self, evidence_result: Dict, discretion_result: Dict,
                              procedure_result: Dict, risk_result: Dict) -> List[Dict[str, Any]]:
        """生成问题清单"""
        all_issues = []
        
        # 证据链问题
        evidence_issues = evidence_result.get("issues", [])
        for issue in evidence_issues:
            all_issues.append({
                "category": "证据链",
                "type": issue.get("type", "unknown"),
                "severity": issue.get("severity", "medium"),
                "description": issue.get("message", ""),
                "rule_id": "RULE_AL_002",
            })
        
        # 裁量问题
        discretion_issues = discretion_result.get("issues", [])
        for issue in discretion_issues:
            all_issues.append({
                "category": "裁量基准",
                "type": issue.get("type", "unknown"),
                "severity": issue.get("severity", "medium"),
                "description": issue.get("message", ""),
                "rule_id": "RULE_AL_006",
            })
        
        # 程序问题
        procedure_issues = procedure_result.get("issues", [])
        for issue in procedure_issues:
            all_issues.append({
                "category": "程序合法性",
                "type": issue.get("type", "unknown"),
                "severity": issue.get("severity", "medium"),
                "description": issue.get("message", ""),
                "rule_id": "RULE_AL_005",
            })
        
        # 风险汇总中的问题
        risk_summary = risk_result.get("risk_summary", {})
        major_issues = risk_summary.get("major_issues", [])
        for issue in major_issues:
            all_issues.append({
                "category": issue.get("dimension", "综合"),
                "type": issue.get("type", "unknown"),
                "severity": "high",
                "description": issue.get("message", ""),
                "rule_id": "RULE_AL_001",
            })
        
        # 按严重程度排序
        severity_order = {"high": 0, "medium": 1, "low": 2}
        all_issues.sort(key=lambda x: severity_order.get(x.get("severity", "medium"), 1))
        
        return all_issues
    
    def _generate_responsibility_nodes(self, evidence_result: Dict, discretion_result: Dict,
                                       procedure_result: Dict) -> List[Dict[str, Any]]:
        """生成责任节点"""
        nodes = []
        
        # 根据问题类型确定责任节点
        issues = []
        issues.extend([(i.get("type"), i.get("severity")) for i in evidence_result.get("issues", [])])
        issues.extend([(i.get("type"), i.get("severity")) for i in discretion_result.get("issues", [])])
        issues.extend([(i.get("type"), i.get("severity")) for i in procedure_result.get("issues", [])])
        
        # 立案阶段责任人
        if any("filing" in str(i[0]) for i in issues):
            nodes.append({
                "node": "立案",
                "responsible_role": "案件承办人",
                "issue": "立案程序不规范",
                "severity": "medium"
            })
        
        # 调查阶段责任人
        if any("investigation" in str(i[0]) or "evidence" in str(i[0]) for i in issues):
            nodes.append({
                "node": "调查取证",
                "responsible_role": "调查人员",
                "issue": "调查取证不规范/证据不足",
                "severity": "high"
            })
        
        # 告知阶段责任人
        if any("notice" in str(i[0]) for i in issues):
            nodes.append({
                "node": "告知程序",
                "responsible_role": "案件承办人",
                "issue": "告知程序缺失或不完整",
                "severity": "high"
            })
        
        # 处罚决定阶段责任人
        if any("penalty" in str(i[0]) or "discretion" in str(i[0]) for i in issues):
            nodes.append({
                "node": "处罚决定",
                "responsible_role": "审批负责人",
                "issue": "裁量不当或处罚依据错误",
                "severity": "high"
            })
        
        # 送达阶段责任人
        if any("delivery" in str(i[0]) for i in issues):
            nodes.append({
                "node": "送达执行",
                "responsible_role": "送达人员",
                "issue": "送达程序不规范",
                "severity": "medium"
            })
        
        return nodes
    
    def _generate_rectification_suggestions(self, evidence_result: Dict, discretion_result: Dict,
                                            procedure_result: Dict, risk_result: Dict) -> List[Dict[str, Any]]:
        """生成整改建议"""
        suggestions = []
        
        # 根据风险等级生成建议
        risk_level = risk_result.get("risk_level", "未知")
        
        if risk_level == "重大瑕疵":
            suggestions.append({
                "priority": "高",
                "category": "立即整改",
                "suggestion": "建议立即启动案件复查程序，重新调查取证，补正证据链缺陷。",
                "action": "启动复查程序"
            })
            suggestions.append({
                "priority": "高",
                "category": "证据补充",
                "suggestion": "建议补充高优先级证据（物证、书证、鉴定意见），确保证据类型多样化。",
                "action": "补充证据材料"
            })
        
        if risk_level in ["重大瑕疵", "一般瑕疵"]:
            # 程序整改建议
            if not procedure_result.get("is_legal", True):
                suggestions.append({
                    "priority": "中",
                    "category": "程序补正",
                    "suggestion": "建议补正程序瑕疵，特别关注时限要求和告知程序完整性。",
                    "action": "补正程序"
                })
            
            # 裁量整改建议
            if discretion_result.get("is_abnormal", False) or abs(discretion_result.get("deviation", 0)) > 0.2:
                suggestions.append({
                    "priority": "中",
                    "category": "重新裁量",
                    "suggestion": f"当前裁量偏差为{discretion_result.get('deviation', 0)*100:.1f}%，建议参照裁量基准重新确定处罚幅度。",
                    "action": "重新裁量"
                })
        
        if risk_level in ["格式问题", "一般瑕疵", "重大瑕疵"]:
            suggestions.append({
                "priority": "低",
                "category": "格式规范",
                "suggestion": "建议规范文书格式，确保案件编号、当事人信息、日期等要素完整。",
                "action": "规范格式"
            })
        
        # 如果没有问题
        if not suggestions:
            suggestions.append({
                "priority": "低",
                "category": "持续改进",
                "suggestion": "案卷基本合规，建议持续加强规范化建设。",
                "action": "归档"
            })
        
        return suggestions
    
    def _generate_similar_case_comparison(self, similarity_result: Dict) -> Dict[str, Any]:
        """生成相似案例对比"""
        similar_cases = similarity_result.get("similar_cases", [])
        
        if not similar_cases:
            return {
                "has_similar_cases": False,
                "message": "当前系统无相似案例记录",
                "cases": []
            }
        
        return {
            "has_similar_cases": True,
            "count": len(similar_cases),
            "cases": [
                {
                    "case_id": case.get("case_id"),
                    "similarity_score": f"{case.get('similarity_score', 0)*100:.1f}%",
                }
                for case in similar_cases[:5]
            ],
            "message": f"发现{len(similar_cases)}个相似案例"
        }
    
    def _generate_conclusion(self, risk_result: Dict) -> Dict[str, Any]:
        """生成结论"""
        risk_level = risk_result.get("risk_level", "未知")
        
        conclusions = {
            "重大瑕疵": {
                "verdict": "不合规",
                "recommendation": "建议立即启动复查程序，补充证据链缺陷，纠正程序问题，重新作出处罚决定。",
                "next_steps": ["启动复查程序", "补充证据", "重新裁量", "重新审批"]
            },
            "一般瑕疵": {
                "verdict": "待整改",
                "recommendation": "建议在规定时间内完成整改，补正程序和实体问题后重新提交审查。",
                "next_steps": ["制定整改计划", "补正问题", "重新提交审查"]
            },
            "格式问题": {
                "verdict": "基本合规",
                "recommendation": "案卷基本符合法定要求，建议修正格式问题后归档。",
                "next_steps": ["修正格式", "归档"]
            },
            "基本合规": {
                "verdict": "合规",
                "recommendation": "案卷符合法定要求，可以继续后续程序。",
                "next_steps": ["继续后续程序", "归档"]
            },
        }
        
        return conclusions.get(risk_level, {
            "verdict": "待评定",
            "recommendation": "风险等级不明确，需要进一步评查。",
            "next_steps": ["进一步评查"]
        })
