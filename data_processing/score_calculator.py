"""评分计算器"""
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict

class ScoreCalculator:
    def __init__(self):
        # 维度权重配置
        self.dimension_weights = {
            'property': {
                'dim1': 0.15,  # 绿化专业知识与技能
                'dim2': 0.15,  # 人员管理与现场协作
                'dim3': 0.20,  # 服务质量与养护效果
                'dim4': 0.10,  # 客户满意度与市场反馈
                'dim5': 0.10,  # 成本效益与定价透明
                'dim6': 0.15,  # 安全环保与作业规范
                'dim7': 0.10,  # 规模实力与应急响应
                'dim8': 0.05   # 合规管理与合同履约
            },
            'functional': {
                'dim1': 0.15,  # 绿化专业知识与实践经验
                'dim2': 0.10,  # 人员管理与现场协作
                'dim3': 0.15,  # 服务质量与养护标准
                'dim4': 0.10,  # 客户评价与市场声誉
                'dim5': 0.15,  # 成本效益与定价模式
                'dim6': 0.15,  # 现场作业安全与环保
                'dim7': 0.10,  # 规模与灵活性
                'dim8': 0.10   # 合规性与法律事项
            }
        }

        # 评估类型权重
        self.type_weights = {
            'property': 0.6,     # 物管处权重60%
            'functional': 0.4    # 职能部门权重40%
        }

    def calculate_dimension_scores(self, evaluations: List[Dict]) -> Dict[str, Dict[str, float]]:
        """计算各维度得分"""
        dimension_scores = {
            'property': defaultdict(list),
            'functional': defaultdict(list)
        }

        for eval in evaluations:
            eval_type = eval['evaluation_type']
            scores = eval['scores']

            # 按维度聚合分数
            for key, score in scores.items():
                dim = key.split('_')[0]  # 提取维度编号
                dimension_scores[eval_type][dim].append(score)

        # 计算平均分
        avg_scores = {
            'property': {},
            'functional': {}
        }

        for eval_type in ['property', 'functional']:
            for dim, scores in dimension_scores[eval_type].items():
                if scores:
                    avg_scores[eval_type][dim] = np.mean(scores)

        return avg_scores

    def calculate_weighted_score(self, dimension_scores: Dict[str, Dict[str, float]]) -> float:
        """计算加权总分"""
        total_score = 0

        for eval_type in ['property', 'functional']:
            type_score = 0
            type_weight = self.type_weights[eval_type]

            for dim, score in dimension_scores[eval_type].items():
                if dim in self.dimension_weights[eval_type]:
                    dim_weight = self.dimension_weights[eval_type][dim]
                    type_score += score * dim_weight

            # 标准化到100分制
            type_score = (type_score / 5) * 100
            total_score += type_score * type_weight

        return total_score

    def rank_suppliers(self, supplier_scores: Dict[str, float]) -> List[Tuple[str, float, int]]:
        """对供应商进行排名"""
        sorted_suppliers = sorted(
            supplier_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        ranked = []
        for rank, (supplier, score) in enumerate(sorted_suppliers, 1):
            ranked.append((supplier, score, rank))

        return ranked

    def get_score_level(self, score: float) -> str:
        """获取分数等级"""
        if score >= 90:
            return "优秀"
        elif score >= 80:
            return "良好"
        elif score >= 70:
            return "合格"
        elif score >= 60:
            return "基本合格"
        else:
            return "不合格"
