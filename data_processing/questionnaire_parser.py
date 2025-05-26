"""问卷解析器"""
import json
from typing import Dict, List, Any

class QuestionnaireParser:
    def __init__(self):
        self.property_dimensions = {
            'dim1': '绿化专业知识与技能',
            'dim2': '人员管理与现场协作',
            'dim3': '服务质量与养护效果',
            'dim4': '客户满意度与市场反馈',
            'dim5': '成本效益与定价透明',
            'dim6': '安全环保与作业规范',
            'dim7': '规模实力与应急响应',
            'dim8': '合规管理与合同履约'
        }

        self.functional_dimensions = {
            'dim1': '绿化专业知识与实践经验',
            'dim2': '人员管理与现场协作',
            'dim3': '服务质量与养护标准',
            'dim4': '客户评价与市场声誉',
            'dim5': '成本效益与定价模式',
            'dim6': '现场作业安全与环保',
            'dim7': '规模与灵活性',
            'dim8': '合规性与法律事项'
        }

    def parse_questionnaire(self, questionnaire_json: Dict) -> Dict:
        """解析问卷JSON结构"""
        result = {
            'id': questionnaire_json.get('id'),
            'title': self._clean_html(questionnaire_json.get('title', '')),
            'questions': []
        }

        for item in questionnaire_json.get('children', []):
            if item.get('type') == 'Nps':  # 评分题
                question = {
                    'id': item.get('id'),
                    'title': self._clean_html(item.get('title', '')),
                    'type': 'score',
                    'dimension': self._extract_dimension(item.get('title', ''))
                }
                result['questions'].append(question)
            elif item.get('type') in ['FillBlank', 'Cascader']:  # 开放题
                question = {
                    'id': item.get('id'),
                    'title': self._clean_html(item.get('title', '')),
                    'type': 'text',
                    'category': self._extract_category(item.get('title', ''))
                }
                result['questions'].append(question)

        return result

    def _clean_html(self, text: str) -> str:
        """清理HTML标签"""
        import re
        clean_text = re.sub('<.*?>', '', text)
        return clean_text.strip()

    def _extract_dimension(self, title: str) -> str:
        """从题目中提取维度信息"""
        # 这里需要根据实际题目内容映射到对应维度
        # 简化处理，实际应该建立更完善的映射关系
        keywords_map = {
            '技术方案': 'dim1',
            '人员配置': 'dim2',
            '质量标准': 'dim3',
            '客户评价': 'dim4',
            '报价': 'dim5',
            '安全': 'dim6',
            '资源储备': 'dim7',
            '合规': 'dim8'
        }

        for keyword, dim in keywords_map.items():
            if keyword in title:
                return dim
        return 'other'

    def _extract_category(self, title: str) -> str:
        """提取开放题类别"""
        if '优秀案例' in title:
            return 'positive'
        elif '问题案例' in title:
            return 'negative'
        elif '改进建议' in title:
            return 'suggestion'
        return 'other'
