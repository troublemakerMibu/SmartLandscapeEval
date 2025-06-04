"""主程序入口"""
import os
import json
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
from data_processing.service_info_processor import ServiceInfoProcessor
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
        self.service_info_processor = ServiceInfoProcessor(self.db_manager)

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

    def analyze_supplier(self, supplier_name: str, service_area: str = None) -> Dict:
        """分析单个供应商"""
        print(f"\n正在分析供应商: {supplier_name}")

        # 获取评估数据
        evaluations = self.db_manager.get_supplier_evaluations(supplier_name)

        if not evaluations:
            print(f"警告: 未找到供应商 {supplier_name} 的评估数据")
            return None

        # 从评估数据中获取服务地区
        if not service_area and evaluations:
            service_area = evaluations[0].get('service_area', '未知')

        # 计算维度得分
        dimension_scores = self.score_calculator.calculate_dimension_scores(evaluations)

        # 计算综合得分
        total_score = self.score_calculator.calculate_weighted_score(dimension_scores)

        # 分别计算物管处和职能部门得分
        property_score = 0
        functional_score = 0

        if dimension_scores['property']:
            # 计算物管处的加权平均分
            weighted_sum = 0
            weight_sum = 0

            for dim, score in dimension_scores['property'].items():
                if dim in self.config.DIMENSION_WEIGHTS['property']:
                    dim_weight = self.config.DIMENSION_WEIGHTS['property'][dim]
                    weighted_sum += score * dim_weight
                    weight_sum += dim_weight

            if weight_sum > 0:
                property_score = (weighted_sum / weight_sum / 5) * 100

            print(f"物管处得分: {property_score:.2f}")

        if dimension_scores['functional']:
            # 计算职能部门的加权平均分
            weighted_sum = 0
            weight_sum = 0

            for dim, score in dimension_scores['functional'].items():
                if dim in self.config.DIMENSION_WEIGHTS['functional']:
                    dim_weight = self.config.DIMENSION_WEIGHTS['functional'][dim]
                    weighted_sum += score * dim_weight
                    weight_sum += dim_weight

            if weight_sum > 0:
                functional_score = (weighted_sum / weight_sum / 5) * 100

            print(f"职能部门得分: {functional_score:.2f}")

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
            'service_area': service_area,
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

        print(f"供应商 {supplier_name}({service_area}) 分析完成，综合得分: {total_score:.2f}")

        return analysis_result

    def import_service_info(self, excel_path: str):
        """导入供应商服务情况"""
        if os.path.exists(excel_path):
            self.service_info_processor.import_service_info(excel_path)
        else:
            print(f"警告: 未找到服务情况文件 {excel_path}")

    def generate_all_reports(self):
        """生成所有供应商报告"""
        print("\n开始生成供应商评估报告...")

        # 获取所有供应商
        suppliers_with_area = self.db_manager.get_all_suppliers()

        if not suppliers_with_area:
            print("错误: 数据库中没有供应商数据")
            return

        # 分析所有供应商
        all_results = {}
        results_by_area = defaultdict(dict)

        for supplier_name, service_area in suppliers_with_area:
            result = self.analyze_supplier(supplier_name, service_area)
            if result:
                all_results[supplier_name] = result
                results_by_area[service_area][supplier_name] = result

        # 计算总排名
        supplier_scores = {
            supplier: result['total_score']
            for supplier, result in all_results.items()
        }
        total_rankings = self.score_calculator.rank_suppliers(supplier_scores)

        # 计算分地区排名
        rankings_by_area = {}
        for area, area_results in results_by_area.items():
            area_scores = {
                supplier: result['total_score']
                for supplier, result in area_results.items()
            }
            area_rankings = self.score_calculator.rank_suppliers(area_scores)
            rankings_by_area[area] = area_rankings

        # 为每个供应商生成详细报告
        for supplier, score, rank in total_rankings:
            if supplier in all_results:
                # 获取供应商的服务地区
                service_area = all_results[supplier]['service_area']

                # 找到地区内排名
                area_rank = None
                if service_area in rankings_by_area:
                    for s, _, r in rankings_by_area[service_area]:
                        if s == supplier:
                            area_rank = r
                            break

                all_results[supplier]['rank'] = rank
                all_results[supplier]['area_rank'] = area_rank
                if Config.GENERATE_REPORTS_MODE == 'ALL' or Config.GENERATE_REPORTS_MODE  == 'SUPPLIER_ONLY':
                    # 生成PDF报告
                    report_path = os.path.join(
                        self.config.REPORTS_DIR,
                        f'{supplier}_评估报告_{datetime.now().strftime("%Y%m%d")}.pdf'
                    )
                    print(f'开始生成供应商：{supplier}评估报告')
                    self.report_generator.generate_supplier_report(
                        supplier,
                        all_results[supplier],
                        report_path
                    )

                    print(f"已生成报告: {report_path}")

        # 生成分地区汇总排名报告
        summary_path = os.path.join(
            self.config.REPORTS_DIR,
            f'供应商评估汇总报告_{datetime.now().strftime("%Y%m%d")}.pdf'
        )

        # 准备带地区信息的排名数据
        total_rankings_with_area = []
        for supplier, score, rank in total_rankings:
            service_area = all_results[supplier]['service_area']
            total_rankings_with_area.append(((supplier, service_area), score, rank))

        # 准备分地区排名数据
        rankings_by_area_with_info = {}
        for area, rankings in rankings_by_area.items():
            area_rankings_with_info = []
            for supplier, score, rank in rankings:
                area_rankings_with_info.append(((supplier, area), score, rank))
            rankings_by_area_with_info[area] = area_rankings_with_info
        if Config.GENERATE_REPORTS_MODE == 'ALL' or Config.GENERATE_REPORTS_MODE  == 'SUMMARY_ONLY':
            self.report_generator.generate_summary_report_by_area(
                rankings_by_area_with_info,
                total_rankings_with_area,
                summary_path,
                db_manager=self.db_manager  # 传递数据库管理器
            )
            print(f"\n已生成汇总报告: {summary_path}")

        # 打印排名结果
        print("\n=== 供应商综合排名（所有地区） ===")
        print(f"{'排名':<5} {'供应商名称':<30} {'服务地区':<10} {'综合得分':<10} {'评级':<10}")
        print("-" * 70)
        for supplier, score, rank in total_rankings:
            level = self.score_calculator.get_score_level(score)
            service_area = all_results[supplier]['service_area']
            print(f"{rank:<5} {supplier:<30} {service_area:<10} {score:<10.2f} {level:<10}")

        # 打印分地区排名
        for area, rankings in rankings_by_area.items():
            print(f"\n=== {area}供应商排名 ===")
            print(f"{'地区排名':<8} {'供应商名称':<30} {'综合得分':<10} {'评级':<10}")
            print("-" * 60)
            for supplier, score, rank in rankings:
                level = self.score_calculator.get_score_level(score)
                print(f"{rank:<8} {supplier:<30} {score:<10.2f} {level:<10}")

    def run(self):
        """运行主程序"""
        print("=== 供应商评估系统 ===")
        print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # # 1. 加载问卷配置（如果有JSON文件）
        # # self.load_questionnaires('property_questionnaire.json', 'functional_questionnaire.json')
        #
        if Config.IMPORT_DATA:
            # 2. 导入Excel数据

            property_excel = os.path.join(self.config.DATA_DIR, 'property_evaluation.xlsx')
            functional_excel = os.path.join(self.config.DATA_DIR, 'functional_evaluation.xlsx')

            if os.path.exists(property_excel) or os.path.exists(functional_excel):
                self.import_excel_data(property_excel, functional_excel)
            service_info_excel = os.path.join(self.config.DATA_DIR, '绿化外包供应商服务情况一览表.xlsx')
            if os.path.exists(service_info_excel):
                self.import_service_info(service_info_excel)
            else:
                print("提示: 请将Excel文件放置在data目录下")
                print(f"  - 物管处数据: {property_excel}")
                print(f"  - 职能部门数据: {functional_excel}")
                print(f"  - 供应商服务情况一览表: {service_info_excel}")
                return
        self.test_database_content()
        # 3. 生成所有报告
        self.generate_all_reports()

        print(f"\n处理完成! 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"报告输出目录: {self.config.REPORTS_DIR}")
        print(f"图表输出目录: {self.config.CHARTS_DIR}")

    def test_database_content(self):
        """测试数据库内容"""
        print("\n=== 测试数据库内容 ===")

        # 直接查询数据库
        with self.db_manager._get_connection() as conn:
            cursor = conn.cursor()

            # 查询所有评估记录
            cursor.execute('''
                SELECT e.*, s.name as supplier_name
                FROM evaluations e
                JOIN suppliers s ON e.supplier_id = s.id
                ORDER BY s.name, e.evaluation_type
            ''')

            all_records = cursor.fetchall()
            print(f"\n数据库中总评估记录数: {len(all_records)}")

            # 按供应商和类型统计
            supplier_stats = {}
            for record in all_records:
                supplier = record['supplier_name']
                eval_type = record['evaluation_type']

                if supplier not in supplier_stats:
                    supplier_stats[supplier] = {'property': 0, 'functional': 0}

                supplier_stats[supplier][eval_type] += 1

            print("\n各供应商评估记录统计:")
            for supplier, stats in supplier_stats.items():
                print(f"  {supplier}:")
                print(f"    物管处评估: {stats['property']} 条")
                print(f"    职能部门评估: {stats['functional']} 条")

            # 查看一个供应商的详细数据
            if supplier_stats:
                test_supplier = list(supplier_stats.keys())[0]
                print(f"\n查看 {test_supplier} 的详细评估数据:")

                cursor.execute('''
                    SELECT * FROM evaluations e
                    JOIN suppliers s ON e.supplier_id = s.id
                    WHERE s.name = ?
                ''', (test_supplier,))

                for i, record in enumerate(cursor.fetchall()):
                    print(f"\n  记录 {i+1}:")
                    print(f"    类型: {record['evaluation_type']}")
                    print(f"    评估人: {record['evaluator_name']}")
                    print(f"    部门: {record['evaluator_dept']}")

                    # 解析scores
                    try:
                        scores = json.loads(record['scores'])
                        print(f"    评分数: {len(scores)}")
                        if scores:
                            print(f"    评分示例: {list(scores.items())[:3]}")
                    except:
                        print(f"    评分解析失败")


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
