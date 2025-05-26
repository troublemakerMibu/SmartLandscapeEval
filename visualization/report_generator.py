"""报告生成器"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
from datetime import datetime
from typing import Dict, List, Tuple

class ReportGenerator:
    def __init__(self):
        # 注册中文字体
        try:
            pdfmetrics.registerFont(TTFont('SimHei', 'simhei.ttf'))
        except:
            print("警告：未找到中文字体文件，报告可能无法正确显示中文")

        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='ChineseTitle',
            fontName='SimHei',
            fontSize=24,
            alignment=1,  # 居中
            spaceAfter=30
        ))
        self.styles.add(ParagraphStyle(
            name='ChineseHeading',
            fontName='SimHei',
            fontSize=16,
            spaceAfter=12
        ))
        self.styles.add(ParagraphStyle(
            name='ChineseNormal',
            fontName='SimHei',
            fontSize=12,
            spaceAfter = 6
        ))

    def generate_supplier_report(self, supplier_name: str, analysis_data: Dict,
                                 output_path: str):
        """生成供应商评估报告"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # 标题页
        story.append(Paragraph(f"{supplier_name}<br/>供应商评估报告", self.styles['ChineseTitle']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"生成日期：{datetime.now().strftime('%Y年%m月%d日')}",
                               self.styles['ChineseNormal']))
        story.append(PageBreak())

        # 1. 综合评分
        story.append(Paragraph("一、综合评分", self.styles['ChineseHeading']))
        score_data = [
            ['评估类型', '得分', '权重', '加权得分'],
            ['物管处评估', f"{analysis_data['property_score']:.2f}", '60%',
             f"{analysis_data['property_score'] * 0.6:.2f}"],
            ['职能部门评估', f"{analysis_data['functional_score']:.2f}", '40%',
             f"{analysis_data['functional_score'] * 0.4:.2f}"],
            ['综合得分', '', '', f"{analysis_data['total_score']:.2f}"],
            ['评级', '', '', analysis_data['level']],
            ['排名', '', '', f"第{analysis_data['rank']}名"]
        ]

        score_table = Table(score_data, colWidths=[2 * inch, 1.5 * inch, 1 * inch, 1.5 * inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('SPAN', (0, 3), (2, 3)),
            ('SPAN', (0, 4), (2, 4)),
            ('SPAN', (0, 5), (2, 5)),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 0.3 * inch))

        # 2. 维度分析
        story.append(Paragraph("二、维度分析", self.styles['ChineseHeading']))

        # 物管处维度
        story.append(Paragraph("2.1 物管处评估维度", self.styles['ChineseNormal']))
        property_dim_data = [['维度', '得分', '满分', '得分率']]
        for dim, score in analysis_data['dimension_scores']['property'].items():
            dim_name = self._get_dimension_name('property', dim)
            score_rate = (score / 5) * 100
            property_dim_data.append([dim_name, f"{score:.2f}", '5.00', f"{score_rate:.1f}%"])

        property_table = Table(property_dim_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 1.5 * inch])
        property_table.setStyle(self._get_table_style())
        story.append(property_table)
        story.append(Spacer(1, 0.2 * inch))

        # 职能部门维度
        story.append(Paragraph("2.2 职能部门评估维度", self.styles['ChineseNormal']))
        functional_dim_data = [['维度', '得分', '满分', '得分率']]
        for dim, score in analysis_data['dimension_scores']['functional'].items():
            dim_name = self._get_dimension_name('functional', dim)
            score_rate = (score / 5) * 100
            functional_dim_data.append([dim_name, f"{score:.2f}", '5.00', f"{score_rate:.1f}%"])

        functional_table = Table(functional_dim_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 1.5 * inch])
        functional_table.setStyle(self._get_table_style())
        story.append(functional_table)
        story.append(PageBreak())

        # 3. 可视化分析
        story.append(Paragraph("三、可视化分析", self.styles['ChineseHeading']))

        # 雷达图
        if os.path.exists(analysis_data['radar_chart_path']):
            story.append(Paragraph("3.1 维度雷达图", self.styles['ChineseNormal']))
            img = Image(analysis_data['radar_chart_path'], width=6 * inch, height=3 * inch)
            story.append(img)
            story.append(Spacer(1, 0.2 * inch))

        # 词云图
        if os.path.exists(analysis_data['wordcloud_path']):
            story.append(Paragraph("3.2 反馈词云分析", self.styles['ChineseNormal']))
            img = Image(analysis_data['wordcloud_path'], width=6 * inch, height=3 * inch)
            story.append(img)
            story.append(PageBreak())

        # 4. 反馈汇总
        story.append(Paragraph("四、反馈汇总", self.styles['ChineseHeading']))

        # 优秀案例
        story.append(Paragraph("4.1 优秀案例", self.styles['ChineseNormal']))
        if analysis_data['positive_feedbacks']:
            for i, feedback in enumerate(analysis_data['positive_feedbacks'][:5], 1):
                story.append(Paragraph(f"{i}. {feedback}", self.styles['ChineseNormal']))
        else:
            story.append(Paragraph("暂无优秀案例反馈", self.styles['ChineseNormal']))
        story.append(Spacer(1, 0.2 * inch))

        # 问题与建议
        story.append(Paragraph("4.2 问题与改进建议", self.styles['ChineseNormal']))
        if analysis_data['negative_feedbacks']:
            for i, feedback in enumerate(analysis_data['negative_feedbacks'][:5], 1):
                story.append(Paragraph(f"{i}. {feedback}", self.styles['ChineseNormal']))
        else:
            story.append(Paragraph("暂无问题反馈", self.styles['ChineseNormal']))

        # 生成PDF
        doc.build(story)

    def generate_summary_report(self, rankings: List[Tuple[str, float, int]],
                                output_path: str):
        """生成汇总排名报告"""
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []

        # 标题
        story.append(Paragraph("供应商评估汇总报告", self.styles['ChineseTitle']))
        story.append(Spacer(1, 0.2 * inch))
        story.append(Paragraph(f"生成日期：{datetime.now().strftime('%Y年%m月%d日')}",
                               self.styles['ChineseNormal']))
        story.append(Spacer(1, 0.5 * inch))

        # 排名表
        story.append(Paragraph("供应商综合排名", self.styles['ChineseHeading']))

        ranking_data = [['排名', '供应商名称', '综合得分', '评级']]
        for supplier, score, rank in rankings:
            level = self._get_score_level(score)
            ranking_data.append([str(rank), supplier, f"{score:.2f}", level])

        ranking_table = Table(ranking_data, colWidths=[1 * inch, 3 * inch, 1.5 * inch, 1.5 * inch])
        ranking_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            # 前三名高亮
            ('BACKGROUND', (0, 1), (-1, 1), colors.gold if len(rankings) > 0 else colors.beige),
            ('BACKGROUND', (0, 2), (-1, 2), colors.silver if len(rankings) > 1 else colors.beige),
            ('BACKGROUND', (0, 3), (-1, 3), colors.brown if len(rankings) > 2 else colors.beige),
        ]))
        story.append(ranking_table)

        # 生成PDF
        doc.build(story)

    def _get_dimension_name(self, eval_type: str, dim: str) -> str:
        """获取维度名称"""
        dimension_names = {
            'property': {
                'dim1': '绿化专业知识与技能',
                'dim2': '人员管理与现场协作',
                'dim3': '服务质量与养护效果',
                'dim4': '客户满意度与市场反馈',
                'dim5': '成本效益与定价透明',
                'dim6': '安全环保与作业规范',
                'dim7': '规模实力与应急响应',
                'dim8': '合规管理与合同履约'
            },
            'functional': {
                'dim1': '绿化专业知识与实践经验',
                'dim2': '人员管理与现场协作',
                'dim3': '服务质量与养护标准',
                'dim4': '客户评价与市场声誉',
                'dim5': '成本效益与定价模式',
                'dim6': '现场作业安全与环保',
                'dim7': '规模与灵活性',
                'dim8': '合规性与法律事项'
            }
        }
        return dimension_names.get(eval_type, {}).get(dim, dim)

    def _get_table_style(self):
        """获取表格样式"""
        return TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])

    def _get_score_level(self, score: float) -> str:
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
