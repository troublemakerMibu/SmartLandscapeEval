"""Excel数据处理器"""
import pandas as pd
import numpy as np
from typing import Dict, List
from datetime import datetime
from database.models import Evaluation
from utils.supplier_config import get_supplier_service_area

class ExcelProcessor:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def process_property_excel(self, file_path: str):
        """处理物管处Excel数据"""
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            try:
                supplier_name = row['绿化外包供应商']
                # 获取供应商服务地区
                service_area = get_supplier_service_area(supplier_name)
                supplier_id = self.db_manager.insert_supplier(supplier_name, service_area)

                # 提取评分数据
                scores = self._extract_property_scores(row)
                feedback = self._extract_feedback(row)

                # 处理日期
                eval_date = None
                if '日期' in row and pd.notna(row['日期']):
                    try:
                        eval_date = pd.to_datetime(row['日期'])
                    except:
                        eval_date = datetime.now()
                else:
                    eval_date = datetime.now()

                evaluation = Evaluation(
                    supplier_id=supplier_id,
                    evaluator_name=str(row.get('姓名', '')),
                    evaluator_dept=str(row.get('物管处名称（全称）', '')),
                    evaluator_phone=str(row.get('手机号码', '')),
                    evaluation_type='property',
                    evaluation_date=eval_date,
                    scores=scores,
                    feedback=feedback
                )

                self.db_manager.insert_evaluation(evaluation)
                print(f"成功导入物管处评估记录: {supplier_name}({service_area}) - {evaluation.evaluator_name}")

            except Exception as e:
                print(f"处理物管处数据时出错: {str(e)}")
                continue

    def process_functional_excel(self, file_path: str):
        """处理职能部门Excel数据"""
        df = pd.read_excel(file_path)

        for _, row in df.iterrows():
            try:
                supplier_name = row['考核供应商名称']
                # 获取供应商服务地区
                service_area = get_supplier_service_area(supplier_name)
                supplier_id = self.db_manager.insert_supplier(supplier_name, service_area)

                # 提取评分数据
                scores = self._extract_functional_scores(row)
                feedback = self._extract_feedback(row)

                evaluation = Evaluation(
                    supplier_id=supplier_id,
                    evaluator_name=str(row.get('姓名', '')),
                    evaluator_dept=str(row.get('部门', '')),
                    evaluator_phone=str(row.get('手机号码', '')),
                    evaluation_type='functional',
                    evaluation_date=datetime.now(),
                    scores=scores,
                    feedback=feedback
                )

                self.db_manager.insert_evaluation(evaluation)
                print(f"成功导入职能部门评估记录: {supplier_name}({service_area}) - {evaluation.evaluator_name}")

            except Exception as e:
                print(f"处理职能部门数据时出错: {str(e)}")
                continue

    # ... 其余方法保持不变 ...

    def _extract_property_scores(self, row) -> Dict[str, float]:
        """提取物管处评分"""
        score_columns = {
            'dim1_1': '植物知识与养护技能： 供应商团队对植物种类、生长习性及养护方法的了解程度和操作规范性如何？',
            'dim1_2': '病虫害防治与处理能力： 供应商对病虫害的识别、预防和有效处理能力如何？',
            'dim1_3': '绿化设计理解与实施能力（仅限租摆服务） ：供应商是否能较好地理解设计意图并高质量地实施植物配置与摆放？',
            'dim1_4': '季节性及气候适应性经验： 供应商是否能根据季节气候变化，制定并实施有针对性的养护方案？',
            'dim2_1': '人员组织与调度能力： 供应商在人员组织、调度和响应现场需求方面的能力如何？',
            'dim2_2': '现场团队管理与监督： 您观察到供应商的现场团队是否有规范的管理和监督，员工责任心和执行力如何？',
            'dim2_3': '与项目现场人员协作： 供应商团队与贵物管处现场人员的沟通协作是否顺畅、高效？',
            'dim2_4': '异常情况应对能力： 供应商在面对突发事件（如突发天气、植物损坏）时的响应速度和处理效果如何？',
            'dim2_5': '现场沟通与报告机制： 供应商是否能及时、准确地进行现场沟通和工作汇报？',
            'dim2_6': '服务态度与响应性： 供应商的服务态度是否积极主动，对您的要求或反馈能否迅速响应？',
            'dim2_7': '供应商的专业形象： 您认为供应商的企业形象、员工着装及行为举止是否专业得体？',
            'dim3_1': '绿植健康与外观： 贵项目区域的绿植整体健康状况、长势以及外观美观度如何？',
            'dim3_2': '维护任务及时性与规范性： 供应商是否严格按照约定时间和标准完成维护任务（如浇水、修剪、施肥）',
            'dim3_3': '现场环境整洁度： 供应商在作业过程中和作业结束后，是否能保持现场环境的整洁？',
            'dim3_4': '养护方案针对性与有效性： 供应商提供的养护方案是否针对贵项目特点，并取得了良好效果？',
            'dim4_1': '现有客户反馈： 您对该供应商在现有项目（贵项目）上的服务是否满意，是否会向其他项目推荐？',
            'dim4_2': '行业口碑与信誉： 据您了解，该供应商在行业内的声誉和口碑如何？',
            'dim5_1': '定价透明度与合理性： 供应商的报价是否清晰、透明，各项服务内容与费用是否明确？',
            'dim5_2': '报价包含项与潜在费用： 供应商的报价是否全面详细，基本包含所有服务，无隐藏费用？',
            'dim5_3': '服务内容与价格匹配度： 您认为该供应商提供的服务与您所支付的费用相比，性价比如何？',
            'dim5_4': '额外收费合理性： 在合同执行过程中，供应商提出的额外服务或费用是否合理？',
            'dim6_1': '安全操作规程与培训： 您是否观察到供应商员工遵守安全操作规程，并配备相应安全设备？',
            'dim6_2': '安全设备使用与管理： 供应商是否规范使用各类安全设备，并定期检查维护？',
            'dim6_3': '现场安全管理与监督： 作业现场是否有专人负责安全管理，能有效排除安全隐患？',
            'dim6_4': '环保措施与废弃物处理： 供应商对绿化废弃物的处理是否符合环保要求，现场无随意堆放现象？',
            'dim6_5': '对公共设施的保护： 供应商在作业过程中是否注意保护周边公共设施，避免损坏或污染？',
            'dim7_1': '人员配置充足性： 供应商派驻的人员数量是否能满足项目需求，在工作高峰期能否及时补充人力？',
            'dim7_2': '应对突发或临时需求能力： 供应商在面对临时性的增加工作或紧急要求时，是否能灵活调配资源并高效完成？',
            'dim8_1': '劳动合同与社保合规： 您是否观察到供应商有规范的员工管理，包括劳动合同、社保等方面？',
            'dim8_2': '合同执行与履约能力： 供应商是否严格按照合同约定提供服务，履约能力如何？'
        }

        scores = {}
        for key, col_name in score_columns.items():
            if col_name in row:
                value = row[col_name]
                if pd.notna(value):
                    try:
                        scores[key] = float(value)
                    except:
                        print(f"警告: 无法转换评分 {col_name}: {value}")

        return scores

    def _extract_functional_scores(self, row) -> Dict[str, float]:
        """提取职能部门评分"""
        score_columns = {
            'dim1_1': '技术方案专业性： 供应商提交的技术方案、养护计划是否体现专业水平，内容科学合理？',
            'dim1_2': '专业资质完备性： 供应商及其核心技术人员是否具备相应的专业资质证书（如园艺师、绿化工程师等）？',
            'dim1_3': '技术问题解决能力： 当遇到复杂绿化技术问题时，供应商是否能提供专业的解决方案？',
            'dim1_4': '专业建议与创新 ： 供应商是否主动提出有价值的专业建议或采用新技术改进服务质量？',
            'dim2_1': '组织架构合理性： 供应商的人员配置和组织架构是否合理，关键岗位是否配备有经验的管理人员？',
            'dim2_2': '人员稳定性： 供应商的核心管理和技术人员是否稳定，人员流动是否在合理范围内？',
            'dim2_3': '内部协调配合： 供应商在多项目管理和与公司各部门配合方面的表现如何？',
            'dim2_4': '沟通响应效率： 供应商对公司内部部门的需求或问题，响应是否及时有效？',
            'dim2_5': '服务态度专业性： 供应商员工的整体服务态度、专业形象和职业素养如何？',
            'dim3_1': '质量标准制定： 供应商是否制定了明确、可操作的服务质量标准和考核指标？',
            'dim3_2': '质量管理体系： 供应商是否建立了完善的质量管理体系，包括自检、整改、持续改进机制？',
            'dim3_3': '服务标准化程度： 供应商在不同项目间是否能保持服务质量的一致性和标准化？',
            'dim3_4': '问题处理及时性： 当出现服务质量问题时，供应商的发现、报告和处理是否及时有效？',
            'dim4_1': '行业口碑调研： 通过市场调研了解到的供应商在行业内的声誉和口碑如何？',
            'dim4_2': '参考客户质量： 供应商提供的参考客户推荐质量如何，是否为知名企业或长期合作伙伴？',
            'dim4_3': '荣誉资质情况： 供应商是否获得过行业奖项、政府表彰或权威机构认可？',
            'dim5_1': '报价透明规范： 供应商的报价是否详细透明，成本构成清晰，便于审计和成本分析？',
            'dim5_2': '价格竞争优势： 在保证服务质量前提下，供应商的报价在市场中是否具有竞争力？',
            'dim5_3': '结算流程规范： 供应商的费用结算流程是否规范，发票开具是否及时、准确、合规？',
            'dim5_4': '成本优化能力： 供应商是否主动提出成本控制或优化方案，并在实际中体现成本效益？',
            'dim6_1': '安全管理体系： 供应商是否建立了完善的安全生产管理体系和应急预案？',
            'dim6_2': '环保管理规范： 供应商是否建立了完善的环境保护管理体系和废弃物处理流程？',
            'dim6_3': '保险配置完备： 供应商是否按要求购买了足额的劳务/工程保险，有效覆盖潜在风险？',
            'dim6_4': '安全事故记录： 供应商的安全作业记录如何，是否曾发生安全事故或环保违规？',
            'dim7_1': '资源储备充足性： 供应商的人力、设备等资源储备是否充足，组织架构是否健全？',
            'dim7_2': '多项目承接能力： 供应商是否具备同时承接多个项目的管理能力和资源调配能力？',
            'dim7_3': '应急响应机制： 供应商是否建立了有效的应急响应机制，能快速处理突发情况和临时需求？',
            'dim8_1': '法规遵循程度： 供应商对绿化服务相关法律法规的了解程度及遵循情况如何？',
            'dim8_2': '合同条款合规性： 供应商在合同谈判中是否确保条款清晰、公平，充分保护双方权益？',
            'dim8_3': '资质证照完备： 供应商是否具备开展绿化服务所需的全部营业执照、专业资质和行业许可？',
            'dim8_4': '风险防控能力： 供应商是否能有效识别和规避潜在的法律或合规风险？',
            'dim8_5': '履约诚信度： 供应商的合同执行情况和履约能力如何，是否严格按约定提供服务？'
        }

        scores = {}
        for key, col_name in score_columns.items():
            if col_name in row:
                value = row[col_name]
                if pd.notna(value):
                    try:
                        scores[key] = float(value)
                    except:
                        print(f"警告: 无法转换评分 {col_name}: {value}")

        return scores

    def _extract_feedback(self, row) -> Dict[str, str]:
        """提取反馈信息"""
        feedback = {}

        # 调试信息
        # print(f"提取反馈，列名: {list(row.index)}")

        # 物管处反馈字段映射
        property_feedback_map = {
            '优秀案例： 请您列举该供应商在服务过程中，令您印象深刻的优点或特别优秀的具体事例（请尽量具体描述事件、时间和影响）。': 'positive_case',
            '您对于供应商优秀事项的描述：': 'positive_description',
            '问题案例： 请您列举该供应商在服务过程中，您认为需要改进的方面或遇到的具体问题（请尽量具体描述事件、时间和影响）。': 'negative_case',
            '您对于供应商问题案例的描述：': 'negative_description',
            '改进建议 您对该供应商的服务有哪些具体的改进建议？或者对本次评估体系有什么意见？': 'suggestions'
        }

        # 职能部门反馈字段映射
        functional_feedback_map = {
            '优秀案例： 请您列举该供应商在与本部门协作过程中，令您印象深刻的优点或特别优秀的具体事例（请尽量具体描述事件、时间和影响）。': 'positive_case',
            '您的描述：': 'positive_description',  # 这可能是优秀案例的描述
            '问题案例： 请您列举该供应商在与本部门协作过程中，您认为需要改进的方面或遇到的具体问题（请尽量具体描述事件、时间和影响）。': 'negative_case',
            '改进建议： 您对该供应商的服务或有哪些具体的改进建议？': 'suggestions'
        }

        # 尝试两种映射
        for col_name in row.index:
            # 尝试物管处映射
            if col_name in property_feedback_map:
                key = property_feedback_map[col_name]
                if pd.notna(row[col_name]) and str(row[col_name]).strip():
                    feedback[key] = str(row[col_name]).strip()

            # 尝试职能部门映射
            elif col_name in functional_feedback_map:
                key = functional_feedback_map[col_name]
                if pd.notna(row[col_name]) and str(row[col_name]).strip():
                    feedback[key] = str(row[col_name]).strip()

            # 处理"您的描述"字段（可能对应不同的内容）
            elif '您的描述' in col_name:
                if pd.notna(row[col_name]) and str(row[col_name]).strip():
                    # 根据上下文判断是正面还是负面描述
                    # 这里简单处理，如果已有positive_case但无positive_description，则认为是正面描述
                    if 'positive_case' in feedback and 'positive_description' not in feedback:
                        feedback['positive_description'] = str(row[col_name]).strip()
                    elif 'negative_case' in feedback and 'negative_description' not in feedback:
                        feedback['negative_description'] = str(row[col_name]).strip()
                    else:
                        # 默认作为正面描述
                        feedback['positive_description'] = str(row[col_name]).strip()

        # 调试信息
        # if feedback:
        #     print(f"提取到的反馈: {list(feedback.keys())}")

        return feedback

