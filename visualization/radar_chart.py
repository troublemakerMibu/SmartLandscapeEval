"""雷达图生成"""
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties
import matplotlib.font_manager as fm

class RadarChartGenerator:
    def __init__(self):
        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        self.dimension_names = {
            'property': {
                'dim1': '专业知识',
                'dim2': '人员管理',
                'dim3': '服务质量',
                'dim4': '客户满意',
                'dim5': '成本效益',
                'dim6': '安全环保',
                'dim7': '规模实力',
                'dim8': '合规管理'
            },
            'functional': {
                'dim1': '专业经验',
                'dim2': '现场协作',
                'dim3': '养护标准',
                'dim4': '市场声誉',
                'dim5': '定价模式',
                'dim6': '作业安全',
                'dim7': '灵活性',
                'dim8': '法律合规'
            }
        }

    def create_radar_chart(self, dimension_scores: dict[str, dict[str, float]],
                          supplier_name: str, save_path: str):
        """创建雷达图"""
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), subplot_kw=dict(projection='polar'))

        # 物管处评估雷达图
        self._plot_single_radar(
            ax1,
            dimension_scores['property'],
            'property',
            f'{supplier_name} - 物管处评估'
        )

        # 职能部门评估雷达图
        self._plot_single_radar(
            ax2,
            dimension_scores['functional'],
            'functional',
            f'{supplier_name} - 职能部门评估'
        )

        plt.tight_layout()
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

    def _plot_single_radar(self, ax, scores: dict[str, float], eval_type: str, title: str):
        """绘制单个雷达图"""
        # 准备数据
        dimensions = list(self.dimension_names[eval_type].keys())
        labels = list(self.dimension_names[eval_type].values())

        values = []
        for dim in dimensions:
            if dim in scores:
                # 将5分制转换为100分制
                values.append((scores[dim] / 5) * 100)
            else:
                values.append(0)

        # 闭合数据
        values += values[:1]

        # 计算角度
        angles = np.linspace(0, 2 * np.pi, len(dimensions), endpoint=False).tolist()
        angles += angles[:1]

        # 绘制
        ax.plot(angles, values, 'o-', linewidth=2, color='#1f77b4')
        ax.fill(angles, values, alpha=0.25, color='#1f77b4')

        # 设置标签
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels, fontsize=12)

        # 设置范围
        ax.set_ylim(0, 100)
        ax.set_yticks([20, 40, 60, 80, 100])
        ax.set_yticklabels(['20', '40', '60', '80', '100'], fontsize=10)

        # 添加网格
        ax.grid(True)

        # 设置标题
        ax.set_title(title, fontsize=16, pad=20)

        # 添加分数标注
        for angle, value, label in zip(angles[:-1], values[:-1], labels):
            ax.text(angle, value + 5, f'{value:.1f}',
                   ha='center', va='center', fontsize=10)
