"""评分计算器"""
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict
import math
from utils.config import Config

class ScoreCalculator:
    def __init__(self):
        # 维度权重配置
        self.dimension_weights = Config.DIMENSION_WEIGHTS
        # 评估类型权重（物管处40%，职能部门60%）
        self.type_weights = Config.EVALUATION_WEIGHTS
        # 项目规模权重映射
        self.scale_weights = Config.SCALE_WEIGHTS
        # 项目复杂度权重映射
        self.complexity_weights = Config.COMPLEXITY_WEIGHTS
        # 正面案例加分映射
        self.positive_scores = Config.POSITIVE_SCORES
        # 负面案例扣分映射
        self.negative_scores = Config.NEGATIVE_SCORES

        # 新增：样本量调整参数
        self.sample_adjustment_config = Config.SAMPLE_ADJUSTMENT_CONFIG

    def calculate_dimension_scores(self, evaluations: List[Dict]) -> Dict[str, Dict[str, float]]:
        """计算各维度得分（考虑租摆服务特殊规则）"""
        # 按评估类型分组
        property_evals = [e for e in evaluations if e.get('evaluation_type') == 'property']
        functional_evals = [e for e in evaluations if e.get('evaluation_type') == 'functional']

        print(f"\n=== 计算维度得分 ===")
        print(f"物管处评估数: {len(property_evals)}")
        print(f"职能部门评估数: {len(functional_evals)}")

        # 分别计算两种类型的维度得分
        dimension_scores = {
            'property': self._calculate_property_dimensions(property_evals),
            'functional': self._calculate_functional_dimensions(functional_evals)
        }

        # 添加样本信息
        dimension_scores['sample_info'] = {
            'property_count': len(property_evals),
            'functional_count': len(functional_evals),
            'total_count': len(evaluations)
        }

        return dimension_scores

    def _calculate_sample_adjustment(self, sample_size: int, scores: List[float]) -> Dict[str, float]:
        """计算基于样本量的调整系数"""
        if not self.sample_adjustment_config['enable']:
            return {'factor': 1.0, 'confidence_interval': 0}

        adjustment_info = {
            'sample_size': sample_size,
            'factor': 1.0,
            'confidence_interval': 0,
            'std_dev': 0,
            'reliability_score': 1.0,
            'cv': 0  # 变异系数
        }

        if sample_size == 0 or not scores:
            return adjustment_info

        # 1. 计算基本统计量
        if sample_size > 1:
            mean_score = np.mean(scores)
            std_dev = np.std(scores, ddof=1)  # 样本标准差
            adjustment_info['std_dev'] = std_dev

            # 变异系数
            if mean_score > 0:
                cv = std_dev / mean_score
                adjustment_info['cv'] = cv

        # 2. 计算可靠性分数（基于样本量）
        min_samples = self.sample_adjustment_config['min_sample_size']
        optimal_samples = self.sample_adjustment_config['optimal_sample_size']

        if sample_size < min_samples:
            # 样本量不足，施加惩罚
            # 使用平方根函数，使惩罚更平滑
            # reliability = math.sqrt(sample_size / min_samples)
            reliability = sample_size / min_samples
            penalty = (1 - reliability) * self.sample_adjustment_config['max_penalty']
            adjustment_info['factor'] = 1 - penalty
            adjustment_info['reliability_score'] = reliability

        elif sample_size < optimal_samples:
            # 样本量适中，线性插值
            progress = (sample_size - min_samples) / (optimal_samples - min_samples)
            bonus = progress * self.sample_adjustment_config['max_bonus'] * 0.5  # 适中奖励
            adjustment_info['factor'] = 1 + bonus
            adjustment_info['reliability_score'] = 0.8 + 0.2 * progress

        else:
            # 样本量充足，给予奖励但有上限20%
            excess_ratio = math.log(1 + (sample_size - optimal_samples) / optimal_samples)
            bonus = min(excess_ratio * 0.2, self.sample_adjustment_config['max_bonus'])
            adjustment_info['factor'] = 1 + bonus
            adjustment_info['reliability_score'] = 1.0

        # 3. 考虑评分的一致性
        if sample_size > 1 and adjustment_info['cv'] > 0:
            # 变异系数越小，评分越一致，可靠性越高
            # CV < 0.15: 非常一致
            # CV < 0.3: 比较一致
            # CV > 0.5: 差异较大

            if adjustment_info['cv'] < 0.15:
                consistency_bonus = 0.02
            elif adjustment_info['cv'] < 0.3:
                consistency_bonus = 0.01
            elif adjustment_info['cv'] > 0.5:
                consistency_bonus = -0.02
            else:
                consistency_bonus = 0

            # 应用一致性调整
            adjustment_info['factor'] = max(0.9, min(1.1,
                adjustment_info['factor'] + consistency_bonus))

        return adjustment_info

    def _calculate_property_dimensions(self, evaluations: List[Dict]) -> Dict[str, float]:
        """计算物管处维度得分（处理租摆服务特殊规则）"""
        if not evaluations:
            return {}

        # 存储每个项目的维度得分和权重
        project_scores = []
        all_adjusted_scores = []  # 用于计算样本调整

        for eval_idx, eval in enumerate(evaluations):
            scores = eval.get('scores', {})
            feedback = eval.get('feedback', {})

            print(f"\n  评估记录 {eval_idx + 1}:")
            print(f"    评估人: {eval.get('evaluator_name')} - {eval.get('evaluator_dept')}")

            # 获取项目规模和复杂度
            project_scale = self._extract_project_info(scores, 'scale')
            project_complexity = self._extract_project_info(scores, 'complexity')
            has_rental = self._extract_project_info(scores, 'rental')

            # 计算项目权重
            scale_weight = self.scale_weights.get(project_scale, 1)
            complexity_weight = self.complexity_weights.get(project_complexity, 1)
            project_weight = scale_weight * complexity_weight

            print(f"    项目信息:")
            print(f"      规模: {project_scale} (权重 {scale_weight})")
            print(f"      复杂度: {project_complexity} (权重 {complexity_weight})")
            print(f"      项目总权重: {project_weight}")
            print(f"      包含租摆服务: {'是' if has_rental else '否'}")

            # 计算各维度得分
            dimension_scores = {}
            for dim_num in range(1, 9):
                dim = f'dim{dim_num}'
                dim_scores = []

                # 收集该维度的所有评分
                for key, score in scores.items():
                    if key.startswith(f'{dim}_'):
                        # 特殊处理：dim1_3是租摆服务相关问题
                        if key == 'dim1_3' and not has_rental:
                            print(f"      跳过 {key} (无租摆服务)")
                            continue

                        try:
                            score_value = float(score)
                            dim_scores.append(score_value)
                        except:
                            continue

                # 计算维度平均分
                if dim_scores:
                    dimension_scores[dim] = np.mean(dim_scores)
                    print(f"      {dim}: {np.mean(dim_scores):.2f} (共{len(dim_scores)}项)")
                else:
                    dimension_scores[dim] = 0

            # 计算基础分（加权平均）
            base_score = sum(
                dimension_scores.get(dim, 0) * self.dimension_weights['property'].get(dim, 0)
                for dim in dimension_scores
            )

            # 处理开放性反馈调整
            print(f"    反馈调整:")
            adjustment = self._calculate_feedback_adjustment(feedback)
            adjusted_score = base_score + adjustment

            # 限制在1-5分范围内
            adjusted_score = max(1, min(5, adjusted_score))
            all_adjusted_scores.append(adjusted_score)

            print(f"    得分汇总:")
            print(f"      基础分: {base_score:.3f}")
            print(f"      调整分: {adjustment:+.3f}")
            print(f"      最终分: {adjusted_score:.3f}")

            project_scores.append({
                'dimension_scores': dimension_scores,
                'base_score': base_score,
                'adjusted_score': adjusted_score,
                'weight': project_weight
            })

        # 计算样本量调整
        sample_adjustment = self._calculate_sample_adjustment(
            len(evaluations),
            all_adjusted_scores
        )

        print(f"\n  样本量分析:")
        print(f"    样本数: {sample_adjustment['sample_size']}")
        print(f"    标准差: {sample_adjustment['std_dev']:.3f}")
        print(f"    变异系数: {sample_adjustment['cv']:.3f}")
        print(f"    可靠性: {sample_adjustment['reliability_score']:.3f}")
        print(f"    调整系数: {sample_adjustment['factor']:.3f}")

        # 说明调整原因
        if sample_adjustment['factor'] < 1.0:
            print(f"    说明: 样本量较少，评分可靠性降低，施加{(1-sample_adjustment['factor'])*100:.1f}%惩罚")
        elif sample_adjustment['factor'] > 1.0:
            print(f"    说明: 样本量充足且评分一致，给予{(sample_adjustment['factor']-1)*100:.1f}%奖励")

        # 计算加权平均的维度得分
        if not project_scores:
            return {}

        # 按项目权重计算各维度的加权平均
        weighted_dimensions = {}
        total_weight = sum(p['weight'] for p in project_scores)

        print(f"\n  物管处维度加权平均计算:")
        print(f"    总权重: {total_weight}")

        for dim in ['dim1', 'dim2', 'dim3', 'dim4', 'dim5', 'dim6', 'dim7', 'dim8']:
            weighted_sum = sum(
                p['dimension_scores'].get(dim, 0) * p['weight']
                for p in project_scores
            )
            if total_weight > 0:
                # 应用样本量调整
                raw_score = weighted_sum / total_weight
                adjusted_score = raw_score * sample_adjustment['factor']
                weighted_dimensions[dim] = adjusted_score

                if abs(raw_score - adjusted_score) > 0.001:
                    print(f"    {dim}: 原始={raw_score:.2f}, 调整后={adjusted_score:.2f}")
                else:
                    print(f"    {dim}: {adjusted_score:.2f}")

        # 添加样本调整信息
        weighted_dimensions['_sample_adjustment'] = sample_adjustment

        return weighted_dimensions

    def _calculate_functional_dimensions(self, evaluations: List[Dict]) -> Dict[str, float]:
        """计算职能部门维度得分"""
        if not evaluations:
            return {}

        # 收集所有维度的评分
        dimension_scores = defaultdict(list)
        all_scores = []

        for eval in evaluations:
            scores = eval.get('scores', {})

            # 按维度收集评分
            for key, score in scores.items():
                if '_' in key:
                    dim = key.split('_')[0]
                    if dim.startswith('dim') and len(dim) == 4:
                        score_value = float(score)
                        dimension_scores[dim].append(score_value)
                        all_scores.append(score_value)

        # 计算样本量调整
        sample_adjustment = self._calculate_sample_adjustment(
            len(evaluations),
            all_scores
        )

        print(f"\n  职能部门样本量分析:")
        print(f"    样本数: {sample_adjustment['sample_size']}")
        print(f"    可靠性: {sample_adjustment['reliability_score']:.3f}")
        print(f"    调整系数: {sample_adjustment['factor']:.3f}")

        # 计算各维度平均分并应用调整
        avg_dimensions = {}
        for dim, scores in dimension_scores.items():
            if scores:
                raw_score = np.mean(scores)
                adjusted_score = raw_score * sample_adjustment['factor']
                avg_dimensions[dim] = adjusted_score

        # 添加样本调整信息
        avg_dimensions['_sample_adjustment'] = sample_adjustment

        return avg_dimensions

    # ... 其余方法保持不变 ...

    def _extract_impact_level(self, case_text: str) -> str:
        """从案例文本中提取影响程度等级"""
        if not case_text:
            return ''

        # 案例格式: "类型,影响程度"
        # 例如: "a) 专业技术类（如解决复杂植物问题）,a) 轻微正面影响"

        # 简单方法：查找最后出现的 a) b) c) d)
        case_lower = case_text.lower()

        # 从后往前查找，找到第一个匹配的就返回
        for i in range(len(case_lower) - 1, -1, -1):
            if i > 0 and case_lower[i] == ')':
                if case_lower[i - 1] in ['a', 'b', 'c', 'd']:
                    return case_lower[i - 1]

        return ''

    def _extract_project_info(self, scores: Dict, info_type: str) -> any:
        """从评分数据中提取项目信息"""
        if info_type == 'scale':
            # 查找项目规模
            scale_fields = [
                '您的项目整体绿化预算/规模属于：',
                '项目规模'
            ]

            for field in scale_fields:
                if field in scores:
                    value = str(scores[field]).strip()
                    # 处理可能的格式：A.小型, B.中型, C.大型 或直接 A, B, C
                    if '.' in value:
                        return value.split('.')[0].upper()
                    elif value.upper() in ['A', 'B', 'C']:
                        return value.upper()
                    # 处理中文
                    elif '小' in value:
                        return 'A'
                    elif '中' in value:
                        return 'B'
                    elif '大' in value:
                        return 'C'

            return 'B'  # 默认中型

        elif info_type == 'complexity':
            # 查找项目复杂度
            complexity_fields = [
                '您所负责项目的绿化复杂度属于：',
                '项目复杂度'
            ]

            for field in complexity_fields:
                if field in scores:
                    value = str(scores[field]).strip()
                    if '.' in value:
                        return value.split('.')[0].upper()
                    elif value.upper() in ['A', 'B', 'C']:
                        return value.upper()
                    # 处理中文
                    elif '低' in value:
                        return 'A'
                    elif '中' in value:
                        return 'B'
                    elif '高' in value:
                        return 'C'

            return 'B'  # 默认中等复杂度

        elif info_type == 'rental':
            # 查找是否包含租摆服务
            rental_fields = [
                '贵项目是否包含绿化租摆服务？',
                '是否包含租摆服务'
            ]

            for field in rental_fields:
                if field in scores:
                    value = str(scores[field]).strip().upper()
                    # 处理可能的格式：A.是, B.否 或 A, B 或 是, 否
                    if 'A' in value or '是' in value:
                        return True
                    elif 'B' in value or '否' in value:
                        return False

            # 如果dim1_3有非零评分，说明有租摆服务
            if 'dim1_3' in scores:
                try:
                    score_value = float(scores.get('dim1_3', 0))
                    return score_value > 0
                except:
                    pass

            return False

    def _calculate_feedback_adjustment(self, feedback: Dict) -> float:
        """计算开放性反馈的加减分"""
        adjustment = 0

        # 处理正面案例
        positive_case = feedback.get('positive_case', '')
        if positive_case:
            # 提取影响程度（查找最后一个逗号后的内容）
            impact = self._extract_impact_level(positive_case)
            if impact in self.positive_scores:
                adjustment += self.positive_scores[impact]
                print(f"      正面案例: {positive_case}")
                print(f"      影响等级: {impact} -> +{self.positive_scores[impact]}")

        # 处理负面案例
        negative_case = feedback.get('negative_case', '')
        if negative_case:
            # 提取影响程度
            impact = self._extract_impact_level(negative_case)
            if impact in self.negative_scores:
                adjustment += self.negative_scores[impact]
                print(f"      负面案例: {negative_case}")
                print(f"      影响等级: {impact} -> {self.negative_scores[impact]}")

        # 限制总调整分数
        adjustment = max(-0.5, min(0.5, adjustment))

        return adjustment

    def calculate_weighted_score(self, dimension_scores: Dict[str, Dict[str, float]]) -> float:
        """计算加权总分"""
        total_score = 0

        print("\n=== 计算加权总分 ===")

        # 提取样本信息
        sample_info = dimension_scores.get('sample_info', {})
        if sample_info:
            print(f"样本统计:")
            print(f"  物管处评估: {sample_info.get('property_count', 0)} 份")
            print(f"  职能部门评估: {sample_info.get('functional_count', 0)} 份")
            print(f"  总计: {sample_info.get('total_count', 0)} 份")

        for eval_type in ['property', 'functional']:
            type_score = 0
            type_weight = self.type_weights[eval_type]

            if not dimension_scores.get(eval_type):
                print(f"\n{eval_type} 无数据")
                continue

            print(f"\n{eval_type} 类型计算:")

            # 获取样本调整信息
            sample_adjustment = dimension_scores[eval_type].get('_sample_adjustment', {})
            if sample_adjustment:
                print(f"  样本调整系数: {sample_adjustment.get('factor', 1.0):.3f}")

            # 计算该类型的加权平均分
            weighted_sum = 0
            weight_sum = 0

            for dim, score in dimension_scores[eval_type].items():
                if dim.startswith('_'):  # 跳过元数据
                    continue

                if dim in self.dimension_weights[eval_type]:
                    dim_weight = self.dimension_weights[eval_type][dim]
                    weighted_sum += score * dim_weight
                    weight_sum += dim_weight
                    print(f"  {dim}: 分数={score:.2f}, 权重={dim_weight:.2f}, 贡献={score * dim_weight:.3f}")

            # 确保权重和为1
            if weight_sum > 0 and abs(weight_sum - 1.0) > 0.01:
                print(f"  权重和为 {weight_sum:.2f}, 进行归一化")
                type_score = weighted_sum / weight_sum
            else:
                type_score = weighted_sum

            # 标准化到100分制
            type_score = (type_score / 5) * 100

            print(f"  {eval_type} 最终得分: {type_score:.2f} (权重: {type_weight * 100}%)")

            # 加入总分
            total_score += type_score * type_weight

        print(f"\n综合得分: {total_score:.2f}")

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
        if score >= 80:
            return "优秀"
        elif score >= 70:
            return "良好"
        elif score >= 60:
            return "合格"
        elif score >= 55:
            return "基本合格"
        else:
            return "不合格"
