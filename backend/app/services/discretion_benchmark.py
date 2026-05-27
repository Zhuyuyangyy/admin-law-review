# backend/app/services/discretion_benchmark.py
"""
裁量基准匹配服务
对照自由裁量标准检测处罚幅度，计算裁量偏差
"""
import re
import json
from typing import Dict, List, Any, Optional

class DiscretionBenchmark:
    """裁量基准匹配器"""
    
    # 默认裁量基准（可从规则库加载）
    DEFAULT_BENCHMARKS = {
        "罚款": {
            "min_percent": 0.5,  # 最低为法定处罚下限的50%
            "max_percent": 2.0,  # 最高为法定处罚上限的200%
        },
        "责令停产停业": {
            "severity_weights": {"轻微": 1, "一般": 2, "严重": 3}
        },
        "吊销许可证": {
            "severity_weights": {"一般": 1, "严重": 2}
        }
    }
    
    # 裁量因素及其权重
    DISCRETION_FACTORS = {
        "违法情节": {"轻微": 0.5, "一般": 1.0, "严重": 1.5, "特别严重": 2.0},
        "违法所得": {"无所得": 0.5, "少量所得": 1.0, "大量所得": 1.5},
        "持续时间": {"短期": 0.8, "中期": 1.0, "长期": 1.3},
        "主观态度": {"配合": 0.7, "一般": 1.0, "抗拒": 1.3},
        "危害后果": {"轻微": 0.8, "一般": 1.0, "严重": 1.3, "特别严重": 1.6},
    }
    
    def __init__(self):
        self.benchmarks = self.DEFAULT_BENCHMARKS.copy()
    
    def load_custom_benchmarks(self, custom_benchmarks: Dict):
        """加载自定义裁量基准"""
        self.benchmarks.update(custom_benchmarks)
    
    def match(self, case_content: str, penalty_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        匹配裁量基准
        :param case_content: 案卷内容
        :param penalty_info: 处罚信息
        :return: 匹配结果
        """
        issues = []
        
        # 1. 提取法定处罚标准
        legal_penalty = self._extract_legal_penalty(case_content)
        
        # 2. 提取实际处罚
        actual_penalty = self._extract_actual_penalty(case_content, penalty_info)
        
        # 3. 提取裁量因素
        discretion_factors = self._extract_discretion_factors(case_content)
        
        # 4. 计算裁量偏差
        deviation = self._calculate_deviation(legal_penalty, actual_penalty, discretion_factors)
        
        # 5. 检测异常
        is_abnormal = self._detect_abnormal(legal_penalty, actual_penalty, deviation, discretion_factors)
        
        # 6. 生成匹配等级
        match_level = self._generate_match_level(deviation, is_abnormal, discretion_factors)
        
        if deviation and abs(deviation) > 0.3:
            direction = "过重" if deviation > 0 else "过轻"
            issues.append({
                "type": "discretion_deviation",
                "severity": "medium" if abs(deviation) <= 0.5 else "high",
                "message": f"裁量偏差{direction}，偏离幅度: {abs(deviation)*100:.1f}%"
            })
        
        if is_abnormal:
            issues.append({
                "type": "discretion_abnormal",
                "severity": "high",
                "message": "裁量幅度异常，建议重新裁量"
            })
        
        return {
            "penalty_type": penalty_info.get("penalty_type", "罚款"),
            "amount": actual_penalty.get("amount"),
            "benchmark_min": legal_penalty.get("min_amount"),
            "benchmark_max": legal_penalty.get("max_amount"),
            "deviation": deviation,
            "is_abnormal": is_abnormal,
            "match_level": match_level,
            "discretion_factors": discretion_factors,
            "legal_penalty_standard": legal_penalty,
            "issues": issues
        }
    
    def _extract_legal_penalty(self, content: str) -> Dict[str, Any]:
        """提取法定处罚标准"""
        legal_penalty = {}
        
        # 提取法定罚款范围
        amount_patterns = [
            r"处以\s*(\d+(?:\.\d+)?)\s*(?:以上|以下)?(?:元|万元)?\s*(?:以上|以下)?.*?罚款",
            r"罚款[为是]?\s*(\d+(?:\.\d+)?)\s*(?:元|万元)",
            r"处违法所得\s*(\d+(?:\.\d+)?)\s*(?:倍|%)?\s*(?:以上|以下)?",
            r"法定罚款[为是]?\s*(\d+(?:\.\d+)?)\s*~?\s*(\d+(?:\.\d+)?)\s*(?:元|万元)",
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, content)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[1]:
                    legal_penalty["min_amount"] = float(groups[0])
                    legal_penalty["max_amount"] = float(groups[1])
                else:
                    legal_penalty["fixed_amount"] = float(groups[0])
                break
        
        # 如果没找到法定标准，尝试从法律条文中提取
        if not legal_penalty:
            law_ref_pattern = r"《([^《\[\]]{3,20})》\s*(?:第(\d+)条|第(\d+)款)"
            matches = re.findall(law_ref_pattern, content)
            if matches:
                legal_penalty["law_reference"] = matches
        
        return legal_penalty
    
    def _extract_actual_penalty(self, content: str, penalty_info: Dict[str, Any]) -> Dict[str, Any]:
        """提取实际处罚"""
        actual_penalty = {}
        
        # 优先使用传入的处罚信息
        if penalty_info.get("amount"):
            actual_penalty["amount"] = penalty_info["amount"]
        
        if penalty_info.get("penalty_type"):
            actual_penalty["type"] = penalty_info["penalty_type"]
        
        # 从内容中提取
        if not actual_penalty.get("amount"):
            amount_patterns = [
                r"罚款[金额]?\s*[:：]\s*(\d+(?:\.\d+)?)\s*(?:元|万元)",
                r"处以罚款\s*(\d+(?:\.\d+)?)\s*(?:元|万元)",
                r"罚款人民币\s*(\d+(?:\.\d+)?)\s*(?:元|万元)",
            ]
            
            for pattern in amount_patterns:
                match = re.search(pattern, content)
                if match:
                    actual_penalty["amount"] = float(match.group(1))
                    break
        
        return actual_penalty
    
    def _extract_discretion_factors(self, content: str) -> Dict[str, Any]:
        """提取裁量因素"""
        factors = {}
        
        for factor_name, factor_weights in self.DISCRETION_FACTORS.items():
            for level, weight in factor_weights.items():
                if level in content:
                    factors[factor_name] = {
                        "level": level,
                        "weight": weight
                    }
                    break
        
        return factors
    
    def _calculate_deviation(self, legal_penalty: Dict, actual_penalty: Dict, 
                            factors: Dict[str, Any]) -> Optional[float]:
        """计算裁量偏差"""
        if not actual_penalty.get("amount"):
            return None
        
        # 使用固定金额作为基准
        if legal_penalty.get("fixed_amount"):
            baseline = legal_penalty["fixed_amount"]
            actual = actual_penalty["amount"]
            return (actual - baseline) / baseline if baseline else 0
        
        # 使用范围的中值作为基准
        if legal_penalty.get("min_amount") and legal_penalty.get("max_amount"):
            baseline = (legal_penalty["min_amount"] + legal_penalty["max_amount"]) / 2
            actual = actual_penalty["amount"]
            
            # 考虑裁量因素调整
            factor_adjustment = 1.0
            for factor in factors.values():
                factor_adjustment *= factor["weight"]
            
            adjusted_baseline = baseline * factor_adjustment
            return (actual - adjusted_baseline) / adjusted_baseline if adjusted_baseline else 0
        
        # 无法计算偏差
        return None
    
    def _detect_abnormal(self, legal_penalty: Dict, actual_penalty: Dict,
                       deviation: Optional[float], factors: Dict[str, Any]) -> bool:
        """检测裁量是否异常"""
        if deviation is None:
            return False
        
        # 计算调整后的基准范围
        penalty_type = actual_penalty.get("type", "罚款")
        
        if penalty_type in self.benchmarks:
            benchmark = self.benchmarks[penalty_type]
            if "min_percent" in benchmark and "max_percent" in benchmark:
                # 计算考虑因素后的实际允许范围
                factor_adjustment = 1.0
                for factor in factors.values():
                    factor_adjustment *= factor["weight"]
                
                min_allowed = benchmark["min_percent"] * factor_adjustment
                max_allowed = benchmark["max_percent"] * factor_adjustment
                
                return deviation < min_allowed - 1 or deviation > max_allowed - 1
        
        # 通用检测：偏差超过50%视为异常
        if deviation and abs(deviation) > 0.5:
            return True
        
        return False
    
    def _generate_match_level(self, deviation: Optional[float], is_abnormal: bool,
                             factors: Dict[str, Any]) -> str:
        """生成匹配等级"""
        if deviation is None:
            return "unknown"
        
        if is_abnormal:
            return "abnormal"
        
        deviation_abs = abs(deviation)
        
        if deviation_abs <= 0.1:
            return "excellent"  # 偏差在10%以内
        elif deviation_abs <= 0.2:
            return "good"  # 偏差在20%以内
        elif deviation_abs <= 0.3:
            return "acceptable"  # 偏差在30%以内
        else:
            return "poor"  # 偏差超过30%
