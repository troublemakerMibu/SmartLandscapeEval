"""评分计算器"""
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
from utils.config import Config

class ScoreCalculator:
    def __init__(self):
        # 维度权重配置
        self.dimension_weights = Config.DIMENSION_WEIGHTS

        # 评估类型权重配置
        self.type_weights = Config.EVALUATION_WEIGHTS

    def calculate_dimension_scores(self, evaluations: List[Dict]) -> Dict[str, Dict[str, float]]:
        """计算各维度得分"""
        # 初始化
        dimension_scores = {
            'property': defaultdict(list),
            'functional': defaultdict(list)
        }

        # 调试信息
        print(f"\n=== 计算维度得分 ===")
        print(f"总评估记录数: {len(evaluations)}")

        # 统计各类型评估数量
        property_count = 0
        functional_count = 0

        for i, eval in enumerate(evaluations):
            eval_type = eval.get('evaluation_type', '')
            evaluator_name = eval.get('evaluator_name', '未知')
            evaluator_dept = eval.get('evaluator_dept', '未知')
            scores = eval.get('scores', {})

            print(f"\n评估记录 {i+1}:")
            print(f"  类型: {eval_type}")
            print(f"  评估人: {evaluator_name}")
            print(f"  部门: {evaluator_dept}")
            print(f"  评分项数: {len(scores)}")

            if eval_type == 'property':
                property_count += 1
            elif eval_type == 'functional':
                functional_count += 1

            # 处理分数
            if not scores:
                print(f"  警告: 此评估记录没有评分数据")
                continue

            # 按维度聚合分数
            score_by_dim = defaultdict(list)
            for key, score in scores.items():
                if score is None or score == '':
                    continue

                try:
                    score_value = float(score)
                except:
                    print(f"  警告: 无法转换分数 {key}: {score}")
                    continue

                # 从key中提取维度编号
                # key格式可能是 'dim1_1', 'dim1_2' 等
                if '_' in key:
                    dim = key.split('_')[0]
                else:
                    dim = key

                # 确保是有效的维度
                if dim.startswith('dim') and len(dim) == 4:
                    score_by_dim[dim].append(score_value)
                else:
                    print(f"  警告: 无法识别的维度键 {key}")

            # 计算每个维度的平均分并加入总体统计
            for dim, dim_scores in score_by_dim.items():
                if dim_scores:
                    avg_score = np.mean(dim_scores)
                    dimension_scores[eval_type][dim].append(avg_score)
                    print(f"  {dim}: 平均分 {avg_score:.2f} (共{len(dim_scores)}项)")

        print(f"\n评估统计:")
        print(f"  物管处评估数: {property_count}")
        print(f"  职能部门评估数: {functional_count}")

        # 计算各维度最终平均分
        avg_scores = {
            'property': {},
            'functional': {}
        }

        for eval_type in ['property', 'functional']:
            print(f"\n{eval_type} 维度最终平均分:")
            if not dimension_scores[eval_type]:
                print(f"  无数据")
            else:
                for dim in ['dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim6', 'dim7', 'dim8']:
                    if dim in dimension_scores[eval_type] and dimension_scores[eval_type][dim]:
                        scores = dimension_scores[eval_type][dim]
                        avg_score = np.mean(scores)
                        avg_scores[eval_type][dim] = avg_score
                        print(f"  {dim}: {avg_score:.2f} (样本数: {len(scores)})")
                    else:
                        print(f"  {dim}: 无数据")

        return avg_scores

    def calculate_weighted_score(self, dimension_scores: Dict[str, Dict[str, float]]) -> float:
        """计算加权总分"""
        total_score = 0

        print("\n=== 计算加权总分 ===")

        for eval_type in ['property', 'functional']:
            type_score = 0
            type_weight = self.type_weights[eval_type]

            print(f"\n{eval_type} 类型计算:")

            # 检查是否有数据
            if not dimension_scores.get(eval_type):
                print(f"  无数据")
                continue

            # 计算该类型的加权平均分
            weighted_sum = 0
            weight_sum = 0

            for dim in ['dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim6', 'dim7', 'dim8']:
                if dim in dimension_scores[eval_type] and dim in self.dimension_weights[eval_type]:
                    score = dimension_scores[eval_type][dim]
                    dim_weight = self.dimension_weights[eval_type][dim]
                    weighted_sum += score * dim_weight
                    weight_sum += dim_weight
                    print(f"  {dim}: 分数={score:.2f}, 权重={dim_weight:.2f}, 贡献={score * dim_weight:.3f}")

            # 计算类型得分
            if weight_sum > 0:
                # 确保权重和为1
                if abs(weight_sum - 1.0) > 0.01:
                    print(f"  警告: 权重和为 {weight_sum:.2f}, 进行归一化")
                    type_score = weighted_sum / weight_sum
                else:
                    type_score = weighted_sum

                # 标准化到100分制（原始分数是1-5分）
                type_score = (type_score / 5) * 100

                print(f"  原始加权平均: {weighted_sum:.3f}")
                print(f"  权重和: {weight_sum:.3f}")
                print(f"  {eval_type} 最终得分: {type_score:.2f} (权重: {type_weight * 100}%)")

                # 加入总分
                total_score += type_score * type_weight
            else:
                print(f"  无有效维度数据")

        print(f"\n综合得分: {total_score:.2f}")
        print("=" * 50)

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
