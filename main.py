"""主程序入口"""
import os
import json
from datetime import datetime
from typing import Dict, List

from database.db_manager import DatabaseManager
from data_processing.questionnaire_parser import QuestionnaireParser
from data_processing.excel_processor import ExcelProcessor
from data_processing.score_calculator import ScoreCalculator
from visualization.radar_chart import RadarChartGenerator
from visualization.word_cloud import WordCloudGenerator
from visualization.report_generator import ReportGenerator
from utils.config import Config

class SupplierEvaluationSystem:
    def __init__(self):
        self.config = Config()
        self.db_manager = DatabaseManager(self.config.DATABASE_PATH)
        self.questionnaire_parser = QuestionnaireParser()
        self.excel_processor = ExcelProcessor(self.db_manager)
        self.score_calculator = ScoreCalculator()
        self.radar_generator = RadarChartGenerator()
        self.wordcloud_generator = WordCloudGenerator()
        self.report_generator = ReportGenerator()

    def load_questionnaires(self, property_json_path: str, functional_json_path: str):
        """加载问卷JSON文件"""
        print("正在加载问卷配置...")

        with open(property_json_path, 'r', encoding='utf-8') as f:
            property_questionnaire = json.load(f)

        with open(functional_json_path, 'r', encoding='utf-8') as f:
            functional_questionnaire = json.load(f)

        # 解析问卷结构
        self.property_structure = self.questionnaire_parser.parse_questionnaire(property_questionnaire)
        self.functional_structure = self.questionnaire_parser.parse_questionnaire(functional_questionnaire)

        print("问卷配置加载完成")

    def import_excel_data(self, property_excel_path: str, functional_excel_path: str):
        """导入Excel数据"""
        print("正在导入Excel数据...")

        # 导入物管处数据
        if os.path.exists(property_excel_path):
            print(f"导入物管处数据: {property_excel_path}")
            self.excel_processor.process_property_excel(property_excel_path)

        # 导入职能部门数据
        if os.path.exists(functional_excel_path):
            print(f"导入职能部门数据: {functional_excel_path}")
            self.excel_processor.process_functional_excel(functional_excel_path)

        print("数据导入完成")

    def analyze_supplier(self, supplier_name: str) -> Dict:
        """分析单个供应商"""
        print(f"\n正在分析供应商: {supplier_name}")

        # 获取评估数据
        evaluations = self.db_manager.get_supplier_evaluations(supplier_name)

        if not evaluations:
            print(f"警告: 未找到供应商 {supplier_name} 的评估数据")
            return None

        # 计算维度得分
        dimension_scores = self.score_calculator.calculate_dimension_scores(evaluations)

        # 计算综合得分
        total_score = self.score_calculator.calculate_weighted_score(dimension_scores)

        # 分别计算物管处和职能部门得分
        property_score = 0
        functional_score = 0

        if dimension_scores['property']:
            property_total = sum(
                score * self.config.DIMENSION_WEIGHTS['property'].get(dim, 0)
                for dim, score in dimension_scores['property'].items()
            )
            property_score = (property_total / 5) * 100

        if dimension_scores['functional']:
            functional_total = sum(
                score * self.config.DIMENSION_WEIGHTS['functional'].get(dim, 0)
                for dim, score in dimension_scores['functional'].items()
            )
            functional_score = (functional_total / 5) * 100

        # 收集反馈信息
        positive_feedbacks = []
        negative_feedbacks = []

        for eval in evaluations:
            feedback = eval.get('feedback', {})
            if 'positive_description' in feedback:
                positive_feedbacks.append(feedback['positive_description'])
            if 'negative_description' in feedback:
                negative_feedbacks.append(feedback['negative_description'])
            if 'suggestions' in feedback:
                negative_feedbacks.append(feedback['suggestions'])

        # 生成可视化图表
        radar_path = os.path.join(self.config.CHARTS_DIR, f'{supplier_name}_radar.png')
        wordcloud_path = os.path.join(self.config.CHARTS_DIR, f'{supplier_name}_wordcloud.png')

        # 生成雷达图
        self.radar_generator.create_radar_chart(
            dimension_scores,
            supplier_name,
            radar_path
        )

        # 生成词云
        feedbacks = [eval.get('feedback', {}) for eval in evaluations]
        self.wordcloud_generator.create_word_cloud(
            feedbacks,
            supplier_name,
            wordcloud_path
        )

        analysis_result = {
            'supplier_name': supplier_name,
            'total_score': total_score,
            'property_score': property_score,
            'functional_score': functional_score,
            'level': self.score_calculator.get_score_level(total_score),
            'dimension_scores': dimension_scores,
            'positive_feedbacks': positive_feedbacks,
            'negative_feedbacks': negative_feedbacks,
            'radar_chart_path': radar_path,
            'wordcloud_path': wordcloud_path,
            'evaluation_count': len(evaluations)
        }

        print(f"供应商 {supplier_name} 分析完成，综合得分: {total_score:.2f}")

        return analysis_result

    def generate_all_reports(self):
        """生成所有供应商报告"""
        print("\n开始生成供应商评估报告...")

        # 获取所有供应商
        suppliers = self.db_manager.get_all_suppliers()

        if not suppliers:
            print("错误: 数据库中没有供应商数据")
            return

        # 分析所有供应商
        all_results = {}
        for supplier in suppliers:
            result = self.analyze_supplier(supplier)
            if result:
                all_results[supplier] = result

        # 计算排名
        supplier_scores = {
            supplier: result['total_score']
            for supplier, result in all_results.items()
        }
        rankings = self.score_calculator.rank_suppliers(supplier_scores)

        # 为每个供应商生成详细报告
        for supplier, score, rank in rankings:
            if supplier in all_results:
                all_results[supplier]['rank'] = rank

                # 生成PDF报告
                report_path = os.path.join(
                    self.config.REPORTS_DIR,
                    f'{supplier}_评估报告_{datetime.now().strftime("%Y%m%d")}.pdf'
                )

                self.report_generator.generate_supplier_report(
                    supplier,
                    all_results[supplier],
                    report_path
                )

                print(f"已生成报告: {report_path}")

        # 生成汇总排名报告
        summary_path = os.path.join(
            self.config.REPORTS_DIR,
            f'供应商评估汇总报告_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

        self.report_generator.generate_summary_report(rankings, summary_path)
        print(f"\n已生成汇总报告: {summary_path}")

        # 打印排名结果
        print("\n=== 供应商综合排名 ===")
        print(f"{'排名':<5} {'供应商名称':<30} {'综合得分':<10} {'评级':<10}")
        print("-" * 60)
        for supplier, score, rank in rankings:
            level = self.score_calculator.get_score_level(score)
            print(f"{rank:<5} {supplier:<30} {score:<10.2f} {level:<10}")

    def run(self):
        """运行主程序"""
        print("=== 供应商评估系统 ===")
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. 加载问卷配置（如果有JSON文件）
        # self.load_questionnaires('property_questionnaire.json', 'functional_questionnaire.json')

        # 2. 导入Excel数据
        property_excel = os.path.join(self.config.DATA_DIR, 'property_evaluation.xlsx')
        functional_excel = os.path.join(self.config.DATA_DIR, 'functional_evaluation.xlsx')

        if os.path.exists(property_excel) or os.path.exists(functional_excel):
            self.import_excel_data(property_excel, functional_excel)
        else:
            print("提示: 请将Excel文件放置在data目录下")
            print(f"  - 物管处数据: {property_excel}")
            print(f"  - 职能部门数据: {functional_excel}")
            return

        # 3. 生成所有报告
        self.generate_all_reports()

        print(f"\n处理完成! 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"报告输出目录: {self.config.REPORTS_DIR}")
        print(f"图表输出目录: {self.config.CHARTS_DIR}")

def main():
    """主函数"""
    try:
        system = SupplierEvaluationSystem()
        system.run()
    except Exception as e:
        print(f"\n错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
