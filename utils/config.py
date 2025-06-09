"""配置文件"""
import os

class Config:
    # 数据库配置
    DATABASE_PATH = 'supplier_evaluation.db'

    # 文件路径配置
    DATA_DIR = 'data'
    OUTPUT_DIR = 'output'
    CHARTS_DIR = os.path.join(OUTPUT_DIR, 'charts')
    REPORTS_DIR = os.path.join(OUTPUT_DIR, 'reports')

    # 确保目录存在
    for dir_path in [DATA_DIR, OUTPUT_DIR, CHARTS_DIR, REPORTS_DIR]:
        os.makedirs(dir_path, exist_ok=True)

    # 评估权重配置
    EVALUATION_WEIGHTS = {
        'property': 0.4,      # 物管处权重
        'functional': 0.6     # 职能部门权重
    }

    # 维度权重配置
    DIMENSION_WEIGHTS = {
        'property': {
            'dim1': 0.15,  # 绿化专业知识与技能
            'dim2': 0.25,  # 人员管理与现场协作
            'dim3': 0.20,  # 服务质量与养护效果
            'dim4': 0.15,  # 客户满意度与市场反馈
            'dim5': 0.10,  # 成本效益与定价透明
            'dim6': 0.05,  # 安全环保与作业规范
            'dim7': 0.05,  # 规模实力与应急响应
            'dim8': 0.05   # 合规管理与合同履约
        },
        'functional': {
            'dim1': 0.15,  # 绿化专业知识与实践经验
            'dim2': 0.25,  # 人员管理与现场协作
            'dim3': 0.20,  # 服务质量与养护标准
            'dim4': 0.15,  # 客户评价与市场声誉
            'dim5': 0.10,  # 成本效益与定价模式
            'dim6': 0.05,  # 现场作业安全与环保
            'dim7': 0.05,  # 规模与灵活性
            'dim8': 0.05   # 合规性与法律事项
        }
    }

    # 字体配置
    FONT_PATH = 'simhei.ttf'  # 需要提供中文字体文件

    # 报告配置
    REPORT_TITLE = "供应商评估报告"

    # 项目复杂度权重
    SCALE_WEIGHTS = {
        'A': 1,  # 小型
        'B': 2,  # 中型
        'C': 4  # 大型
    }
    # 项目规模权重
    COMPLEXITY_WEIGHTS = {
        'A': 1,  # 低复杂度
        'B': 2,  # 中复杂度
        'C': 4  # 高复杂度
    }
    # 正面案例加分
    POSITIVE_SCORES = {
        'a': 0.05,  # 轻微正面影响
        'b': 0.10,  # 中度正面影响
        'c': 0.20,  # 显著正面影响
        'd': 0.30  # 卓越贡献
    }
    # 负面案例扣分
    NEGATIVE_SCORES = {
        'a': -0.05,  # 轻微
        'b': -0.10,  # 一般
        'c': -0.20,  # 严重
        'd': -0.30  # 极严重
    }
    # 样本量调整参数
    SAMPLE_ADJUSTMENT_CONFIG = {
        'enable': True,                  # 是否启用样本量调整
        'method': 'linear',                  # 'ci' / 'eb' / 'linear'
        # —— CI 下限法参数 ——
        'confidence_level': 0.95,        # 置信水平
        # z‐critical table（不用安装 scipy，常见置信水平）
        'z_table': {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576
        },
        # —— EB 平滑法参数 ——
        'eb_prior_mean': 2.5,            # 全局先验均值（例如中点3分）
        'eb_lambda': 5.6,                # 收缩强度 λ
        # —— 线性惩罚/奖励法（保留原实现） ——
        'min_sample_size': 3,
        'optimal_sample_size': 7,
        'max_penalty': 0.2,
        'max_bonus': 0.15,
    }
    # 是否启用LLM
    ENABLE_LLM = False
    # 是否导入数据
    IMPORT_DATA = False
    # 报告生成模式
    """
    ALL 全部生成
    SUMMARY_ONLY 仅生成总结报告
    SUPPLIER_ONLY 进生成供应商报告
    other （任意其他选项）不生成报告
    """
    GENERATE_REPORTS_MODE = 'NO'
    # 设置评价等级
    """获取分数等级"""
    SCORE_LEVEL = {
        '优秀': 80,
        '良好': 70,
        '合格': 60,
        '基本合格': 50
    }
