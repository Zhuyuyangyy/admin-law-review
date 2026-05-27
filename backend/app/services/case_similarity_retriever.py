# backend/app/services/case_similarity_retriever.py
"""
同案相似度检索服务
基于TF-IDF检索历史相似案例，检测处罚偏差
"""
import re
import math
from typing import Dict, List, Any, Tuple
from collections import Counter
import jieba

class CaseSimilarityRetriever:
    """同案相似度检索器"""
    
    def __init__(self):
        self.corpus = []  # 历史案例语料库
        self.corpus_vectors = []  # 语料库的TF-IDF向量
        self.case_store = {}  # 案例存储 {case_id: case_content}
    
    def add_case_to_corpus(self, case_id: int, case_content: str, case_type: str = "行政处罚"):
        """添加案例到语料库"""
        self.case_store[case_id] = {
            "content": case_content,
            "type": case_type
        }
        
        # 提取关键词构建简化的文档表示
        keywords = self._extract_keywords(case_content)
        self.corpus.append({
            "case_id": case_id,
            "keywords": keywords,
            "content_lower": case_content.lower()
        })
    
    def build_index(self):
        """构建TF-IDF索引"""
        if not self.corpus:
            return
        
        # 1. 计算每个文档的TF
        doc_tf = []
        for doc in self.corpus:
            word_counts = Counter(doc["keywords"])
            total_words = len(doc["keywords"])
            tf = {word: count / total_words for word, count in word_counts.items()}
            doc_tf.append(tf)
        
        # 2. 计算IDF
        all_words = set()
        for doc in self.corpus:
            all_words.update(doc["keywords"])
        
        doc_count = len(self.corpus)
        idf = {}
        for word in all_words:
            doc_freq = sum(1 for doc in self.corpus if word in doc["keywords"])
            idf[word] = math.log(doc_count / (doc_freq + 1)) + 1
        
        # 3. 计算TF-IDF向量
        self.corpus_vectors = []
        for tf in doc_tf:
            vector = {}
            for word, freq in tf.items():
                if word in idf:
                    vector[word] = freq * idf[word]
            self.corpus_vectors.append(vector)
    
    def search(self, query_content: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        检索相似案例
        :param query_content: 查询内容
        :param top_k: 返回前k个最相似的案例
        :return: 相似案例列表
        """
        if not self.corpus_vectors:
            return []
        
        # 1. 提取查询内容的关键词
        query_keywords = self._extract_keywords(query_content)
        
        # 2. 计算查询向量
        query_counter = Counter(query_keywords)
        total_words = len(query_keywords)
        query_tf = {word: count / total_words for word, count in query_counter.items()}
        
        # 计算IDF（复用已有的）
        all_words = set()
        for vec in self.corpus_vectors:
            all_words.update(vec.keys())
        
        doc_count = len(self.corpus)
        idf = {}
        for word in all_words:
            doc_freq = sum(1 for vec in self.corpus_vectors if word in vec)
            idf[word] = math.log(doc_count / (doc_freq + 1)) + 1
        
        query_vector = {}
        for word, freq in query_tf.items():
            if word in idf:
                query_vector[word] = freq * idf[word]
        
        # 3. 计算余弦相似度
        similarities = []
        for i, corpus_vector in enumerate(self.corpus_vectors):
            similarity = self._cosine_similarity(query_vector, corpus_vector)
            similarities.append({
                "case_id": self.corpus[i]["case_id"],
                "similarity_score": similarity,
                "keywords_matched": list(set(query_keywords) & set(self.corpus[i]["keywords"]))
            })
        
        # 4. 排序并返回top_k
        similarities.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similarities[:top_k]
    
    def _extract_keywords(self, content: str) -> List[str]:
        """提取关键词"""
        # 清洗内容
        content = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s]', ' ', content)
        
        # 使用jieba分词
        words = jieba.cut(content)
        
        # 过滤停用词和短词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这', '那', '他', '她', '它', '们', '这个', '那个', '什么', '怎么', '为什么'}
        
        keywords = [w for w in words if len(w) >= 2 and w not in stop_words]
        return keywords
    
    def _cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """计算余弦相似度"""
        # 获取共同词汇
        common_words = set(vec1.keys()) & set(vec2.keys())
        if not common_words:
            return 0.0
        
        # 计算点积
        dot_product = sum(vec1[word] * vec2[word] for word in common_words)
        
        # 计算模长
        norm1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        norm2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def check_penalty_deviation(self, current_case: Dict[str, Any], 
                               similar_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """检测处罚偏差（当前案例与相似案例的处罚对比）"""
        if not similar_cases:
            return {
                "has_deviation": False,
                "deviation_level": "unknown",
                "message": "无相似案例可对比"
            }
        
        current_penalty = current_case.get("penalty_amount")
        similar_penalties = []
        
        for similar in similar_cases:
            case_id = similar["case_id"]
            if case_id in self.case_store:
                penalty_info = self.case_store[case_id]
                # 尝试提取罚款金额
                amount_match = re.search(r'罚款\s*(\d+(?:\.\d+)?)\s*(?:元|万元)', penalty_info["content"])
                if amount_match:
                    similar_penalties.append(float(amount_match.group(1)))
        
        if current_penalty is None or not similar_penalties:
            return {
                "has_deviation": False,
                "deviation_level": "unknown", 
                "message": "无法提取处罚金额进行对比"
            }
        
        # 计算平均处罚
        avg_penalty = sum(similar_penalties) / len(similar_penalties)
        deviation = (current_penalty - avg_penalty) / avg_penalty if avg_penalty else 0
        
        deviation_level = "unknown"
        if abs(deviation) <= 0.1:
            deviation_level = "excellent"
        elif abs(deviation) <= 0.2:
            deviation_level = "good"
        elif abs(deviation) <= 0.3:
            deviation_level = "acceptable"
        else:
            deviation_level = "poor"
        
        return {
            "has_deviation": abs(deviation) > 0.2,
            "deviation": deviation,
            "deviation_level": deviation_level,
            "current_penalty": current_penalty,
            "avg_similar_penalty": avg_penalty,
            "penalty_difference": current_penalty - avg_penalty,
            "message": f"当前处罚偏差: {deviation*100:.1f}%"
        }
