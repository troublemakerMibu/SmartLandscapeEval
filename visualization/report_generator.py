"""报告生成器"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_JUSTIFY
import os
from datetime import datetime
from typing import Dict, List, Tuple
from LLMconfig import call_LLM
from utils.config import Config

class ReportGenerator:
    def __init__(self):
        # 注册中文字体
        try:
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            self.chinese_font = 'STSong-Light'
            print("已注册中文字体STSong-Light")

        except:
            try:
                if os.path.exists('simhei.ttf'):
                    pdfmetrics.registerFont(TTFont('SimHei', 'simhei.ttf'))
                    self.chinese_font = 'SimHei'
                else:
                    print("警告：未找到中文字体文件，将使用默认字体")
                    self.chinese_font = 'Helvetica'
            except:
                self.chinese_font = 'Helvetica'

        self.styles = getSampleStyleSheet()
        self.styles.add(ParagraphStyle(
            name='ChineseTitle',
            fontName=self.chinese_font,
            fontSize=22,
            alignment = 1,  # 居中
            spaceAfter = 30,
            wordWrap='CJK'
        ))
        self.styles.add(ParagraphStyle(
            name='ChineseHeading',
            fontName=self.chinese_font,
            fontSize=18,
            spaceAfter=24,
            wordWrap='CJK'
        ))
        self.styles.add(ParagraphStyle(
            name='ChineseNormal',
            fontName=self.chinese_font,
            fontSize=12,
            spaceAfter=16,
            wordWrap='CJK'
        ))

        # 添加大模型评价专用样式
        self.styles.add(ParagraphStyle(
            name='LLMFeedback',
            fontName=self.chinese_font,  # 宋体
            fontSize=12,  # 字号12
            leading=18,  # 行距（12 * 1.5 = 18）
            firstLineIndent=24,  # 首行缩进2个字符（12号字体，2个字符约24点）
            alignment=TA_JUSTIFY,  # 两端对齐
            spaceAfter=12,
            spaceBefore=0,
            leftIndent=0,
            rightIndent=0,
            wordWrap='CJK'  # 中文自动换行
        ))

    def generate_supplier_report(self, supplier_name: str, analysis_data: Dict,
                                 output_path: str):
        """生成供应商评估报告"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []

            # 标题页
            story.append(Paragraph(f"{supplier_name}<br/>", self.styles['ChineseTitle']))
            story.append(Paragraph("供应商评估报告", self.styles['ChineseTitle']))
            story.append(Spacer(1, 0.2 * inch))

            # 显示服务地区
            service_area = analysis_data.get('service_area', '未知')
            story.append(Paragraph(f"服务地区：{service_area}", self.styles['ChineseNormal']))
            story.append(Paragraph(f"生成日期：{datetime.now().strftime('%Y年%m月%d日')}",
                                   self.styles['ChineseNormal']))
            story.append(PageBreak())

            # 1. 综合评分
            story.append(Paragraph("一、综合评分", self.styles['ChineseHeading']))

            # 创建评分表格

            score_data = [
                ['评估类型', '得分', '权重', '加权得分'],
                ['物管处评估', f"{analysis_data.get('property_score', 0):.2f}", '40%',
                 f"{analysis_data.get('property_score', 0) * 0.4:.2f}"],
                ['职能部门评估', f"{analysis_data.get('functional_score', 0):.2f}", '60%',
                 f"{analysis_data.get('functional_score', 0) * 0.6:.2f}"],
                ['综合得分', '', '', f"{analysis_data.get('total_score', 0):.2f}"],
                ['评级', '', '', analysis_data.get('level', '未知')],
                ['服务地区', '', '', service_area],
                ['地区内排名', '', '', f"第{analysis_data.get('area_rank', 'N/A')}名"],
                ['总排名', '', '', f"第{analysis_data.get('rank', 'N/A')}名"]
            ]

            score_table = Table(score_data, colWidths=[2 * inch, 1.5 * inch, 1 * inch, 1.5 * inch])
            score_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 12),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('SPAN', (0, 3), (2, 3)),
                ('SPAN', (0, 4), (2, 4)),
                ('SPAN', (0, 5), (2, 5)),
                ('SPAN', (0, 6), (2, 6)),
                ('SPAN', (0, 7), (2, 7)),
            ]))
            story.append(score_table)
            story.append(Spacer(1, 0.3 * inch))

            # 2. 维度分析
            story.append(Paragraph("二、维度分析", self.styles['ChineseHeading']))

            # 物管处维度
            if 'property' in analysis_data['dimension_scores'] and analysis_data['dimension_scores']['property']:
                story.append(Paragraph("2.1 物管处评估维度", self.styles['ChineseNormal']))

                # 提取样本调整信息
                sample_adjustment = analysis_data['dimension_scores']['property'].get('_sample_adjustment', {})
                if sample_adjustment:
                    adjustment_text = (f"样本量: {sample_adjustment.get('sample_size', 0)}, \n"+
                                       f"可靠性: {sample_adjustment.get('reliability_score', 1.0):.2f}, \n"+
                                       f"调整系数: {sample_adjustment.get('factor', 1.0):.2f}")
                    story.append(Paragraph(f"({adjustment_text})", self.styles['ChineseNormal']))
                    story.append(Spacer(1, 0.1 * inch))

                property_dim_data = [['维度', '得分', '满分', '得分率']]

                # 只处理维度分数，跳过元数据
                for dim, score in analysis_data['dimension_scores']['property'].items():
                    # 跳过元数据（以下划线开头的键）
                    if dim.startswith('_'):
                        continue

                    # 确保score是数值而不是字典
                    if isinstance(score, (int, float)):
                        dim_name = self._get_dimension_name('property', dim)
                        score_rate = (score / 5) * 100
                        property_dim_data.append([dim_name, f"{score:.2f}", '5.00', f"{score_rate:.1f}%"])

                property_table = Table(property_dim_data, colWidths=[2.5 * inch, 1.5 * inch, 1 * inch, 1.5 * inch])
                property_table.setStyle(self._get_table_style())
                story.append(property_table)
                story.append(Spacer(1, 0.2 * inch))

            # 职能部门维度
            if 'functional' in analysis_data['dimension_scores'] and analysis_data['dimension_scores']['functional']:
                story.append(Paragraph("2.2 职能部门评估维度", self.styles['ChineseNormal']))

                # 提取样本调整信息
                sample_adjustment = analysis_data['dimension_scores']['functional'].get('_sample_adjustment', {})
                if sample_adjustment:
                    adjustment_text = (f"样本量: {sample_adjustment.get('sample_size', 0)}, \n"+
                                       f"可靠性: {sample_adjustment.get('reliability_score', 1.0):.2f}, \n"+
                                       f"调整系数: {sample_adjustment.get('factor', 1.0):.2f}")
                    story.append(Paragraph(f"({adjustment_text})", self.styles['ChineseNormal']))
                    story.append(Spacer(1, 0.1 * inch))

                functional_dim_data = [['维度', '得分', '满分', '得分率']]

                # 只处理维度分数，跳过元数据
                for dim, score in analysis_data['dimension_scores']['functional'].items():
                    # 跳过元数据
                    if dim.startswith('_'):
                        continue

                    # 确保score是数值而不是字典
                    if isinstance(score, (int, float)):
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
            if 'radar_chart_path' in analysis_data and os.path.exists(analysis_data['radar_chart_path']):
                story.append(Paragraph("3.1 维度雷达图", self.styles['ChineseNormal']))
                try:
                    img = Image(analysis_data['radar_chart_path'], width=6 * inch, height=3 * inch)
                    story.append(img)
                    story.append(Spacer(1, 0.2 * inch))
                except:
                    story.append(Paragraph("雷达图加载失败", self.styles['ChineseNormal']))

            # 词云图
            if 'wordcloud_path' in analysis_data and os.path.exists(analysis_data['wordcloud_path']):
                story.append(Paragraph("3.2 反馈词云分析", self.styles['ChineseNormal']))
                try:
                    img = Image(analysis_data['wordcloud_path'], width=6 * inch, height=3 * inch)
                    story.append(img)
                except:
                    story.append(Paragraph("词云图加载失败", self.styles['ChineseNormal']))

            story.append(PageBreak())

            # 4. 反馈汇总
            story.append(Paragraph("四、反馈汇总", self.styles['ChineseHeading']))

            # 优秀案例
            story.append(Paragraph("4.1 优秀案例", self.styles['ChineseNormal']))
            if analysis_data.get('positive_feedbacks'):
                for i, feedback in enumerate(analysis_data['positive_feedbacks'][:5], 1):
                    story.append(Paragraph(f"{i}. {feedback}", self.styles['ChineseNormal']))
            else:
                story.append(Paragraph("暂无优秀案例反馈", self.styles['ChineseNormal']))
            story.append(Spacer(1, 0.2 * inch))

            # 问题与建议
            story.append(Paragraph("4.2 问题与改进建议", self.styles['ChineseNormal']))
            if analysis_data.get('negative_feedbacks'):
                for i, feedback in enumerate(analysis_data['negative_feedbacks'][:5], 1):
                    story.append(Paragraph(f"{i}. {feedback}", self.styles['ChineseNormal']))
            else:
                story.append(Paragraph("暂无问题反馈", self.styles['ChineseNormal']))

            story.append(Spacer(1, 0.3 * inch))
            if Config.ENABLE_LLM:
                # 调用大模型生成最终评价（使用特定格式）
                feedback = self._generate_feedback(analysis_data)
                story.append(Paragraph("4.3 综合评价", self.styles['ChineseHeading']))

                # 将反馈文本按段落分割，每段都应用格式
                paragraphs = feedback.split('\n\n') if '\n\n' in feedback else feedback.split('\n')
                for para in paragraphs:
                    if para.strip():  # 忽略空段落
                        # 使用专门的LLM反馈样式
                        story.append(Paragraph(para.strip(), self.styles['LLMFeedback']))

                print('综合评价生成成功')
            else:
                print('跳过LLM生成综合评价')

            # 生成PDF
            doc.build(story)

        except Exception as e:
            print(f"生成供应商报告时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self._generate_matplotlib_report(supplier_name, analysis_data, output_path)

    def generate_summary_report_by_area(self, rankings_by_area: Dict[str, List[Tuple[str, float, int]]],
                                        total_rankings: List[Tuple[str, float, int]],
                                        output_path: str,
                                        db_manager=None):
        """生成按地区分类的汇总排名报告"""
        try:
            doc = SimpleDocTemplate(output_path, pagesize=A4)
            story = []

            # 标题
            story.append(Paragraph("供应商评估汇总报告", self.styles['ChineseTitle']))
            story.append(Spacer(1, 0.2 * inch))
            story.append(Paragraph(f"生成日期：{datetime.now().strftime('%Y年%m月%d日')}",
                                   self.styles['ChineseNormal']))
            story.append(Spacer(1, 0.5 * inch))

            # 获取供应商服务信息
            service_info_dict = {}
            if db_manager:
                all_services = db_manager.get_all_supplier_services()
                for service in all_services:
                    if service['name']:
                        service_info_dict[service['name']] = service

            # 总体排名（保持原有表格，因为只显示项目数）
            story.append(Paragraph("一、供应商综合排名（所有地区）", self.styles['ChineseHeading']))

            ranking_data = [['排名', '供应商名称', '服务地区', '项目数', '综合得分', '评级']]

            for supplier_info, score, rank in total_rankings:
                if isinstance(supplier_info, tuple):
                    supplier_name, service_area = supplier_info
                else:
                    supplier_name = supplier_info
                    service_area = '未知'

                level = self._get_score_level(score)

                # 获取项目数量
                project_count = 0
                if supplier_name in service_info_dict:
                    project_count = service_info_dict[supplier_name].get('project_count', 0)

                ranking_data.append([
                    str(rank),
                    supplier_name,
                    service_area,
                    str(project_count),
                    f"{score:.2f}",
                    level
                ])

            ranking_table = Table(ranking_data,
                                  colWidths=[0.6 * inch, 2.3 * inch, 0.8 * inch, 0.8 * inch, 1 * inch, 0.8 * inch])

            # 设置表格样式
            table_style = [
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]

            # 前三名高亮
            if len(total_rankings) > 0:
                table_style.append(('BACKGROUND', (0, 1), (-1, 1), colors.gold))
            if len(total_rankings) > 1:
                table_style.append(('BACKGROUND', (0, 2), (-1, 2), colors.silver))
            if len(total_rankings) > 2:
                table_style.append(('BACKGROUND', (0, 3), (-1, 3), colors.brown))

            ranking_table.setStyle(TableStyle(table_style))
            story.append(ranking_table)
            story.append(PageBreak())

            # 添加详细服务信息页（修改这部分以支持自动换行）
            story.append(Paragraph("二、供应商服务项目详情", self.styles['ChineseHeading']))

            # 创建一个专门用于表格单元格的样式（较小的字体和行距）
            cell_style = ParagraphStyle(
                'TableCell',
                parent=self.styles['ChineseNormal'],
                fontName=self.chinese_font,
                fontSize=10,
                leading=12,  # 行距
                alignment=0,  # 左对齐
                wordWrap='CJK'
            )

            # 按排名顺序显示每个供应商的详细项目信息
            for supplier_info, score, rank in total_rankings[:10]:  # 只显示前10名的详细信息
                if isinstance(supplier_info, tuple):
                    supplier_name, _ = supplier_info
                else:
                    supplier_name = supplier_info

                if supplier_name in service_info_dict:
                    service = service_info_dict[supplier_name]

                    story.append(Paragraph(f"<b>{rank}. {supplier_name}</b>", self.styles['ChineseNormal']))

                    # 处理项目名称，将其包装在Paragraph中以支持自动换行
                    project_names = service.get('project_names', '')
                    # 将项目名称转换为Paragraph对象
                    project_names_para = Paragraph(project_names, cell_style)

                    # 创建详细信息表
                    detail_data = [
                        ['项目数量', str(service.get('project_count', 0))],
                        ['项目占比', f"{service.get('project_ratio', 0) * 100:.2f}%"],
                        ['服务项目', project_names_para]  # 使用Paragraph对象
                    ]

                    if service.get('remarks'):
                        remarks_para = Paragraph(service.get('remarks', ''), cell_style)
                        detail_data.append(['备注', remarks_para])

                    # 设置表格列宽，给项目名称更多空间
                    detail_table = Table(detail_data, colWidths=[1.2 * inch, 5.3 * inch])

                    detail_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # 第一列右对齐
                        ('ALIGN', (1, 0), (1, -1), 'LEFT'),  # 第二列左对齐
                        ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 6),
                        ('LEFTPADDING', (0, 0), (-1, -1), 8),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ]))

                    story.append(detail_table)
                    story.append(Spacer(1, 0.3 * inch))

            # 添加项目分布统计
            story.append(PageBreak())
            story.append(Paragraph("三、项目分布统计", self.styles['ChineseHeading']))

            # 创建项目分布统计表
            total_projects = sum(service_info_dict.get(name, {}).get('project_count', 0)
                                 for (name, _), _, _ in total_rankings
                                 if isinstance(name, tuple) or name in service_info_dict)

            if total_projects > 0:
                distribution_data = [['供应商名称', '项目数量', '占比', '累计占比']]
                cumulative_ratio = 0

                for supplier_info, score, rank in total_rankings:
                    if isinstance(supplier_info, tuple):
                        supplier_name, _ = supplier_info
                    else:
                        supplier_name = supplier_info

                    if supplier_name in service_info_dict:
                        project_count = service_info_dict[supplier_name].get('project_count', 0)
                        if project_count > 0:
                            ratio = service_info_dict[supplier_name].get('project_ratio', 0)
                            cumulative_ratio += ratio

                            # 使用Paragraph包装供应商名称
                            supplier_name_para = Paragraph(supplier_name, cell_style)

                            distribution_data.append([
                                supplier_name_para,
                                str(project_count),
                                f"{ratio * 100:.2f}%",
                                f"{cumulative_ratio * 100:.2f}%"
                            ])

                distribution_table = Table(distribution_data,
                                           colWidths=[3 * inch, 1.2 * inch, 1.2 * inch, 1.2 * inch])

                distribution_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (0, 0), 'CENTER'),
                    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                story.append(distribution_table)

            story.append(PageBreak())

            # 分地区排名（保持原有逻辑）
            area_index = 4  # 从四开始编号
            for area, rankings in rankings_by_area.items():
                story.append(Paragraph(f"{area_index}、{area}供应商排名",
                                       self.styles['ChineseHeading']))
                area_index += 1

                area_data = [['地区排名', '供应商名称', '项目数', '综合得分', '评级', '总排名']]

                for supplier_info, score, area_rank in rankings:
                    if isinstance(supplier_info, tuple):
                        supplier_name, _ = supplier_info
                    else:
                        supplier_name = supplier_info

                    level = self._get_score_level(score)

                    # 找到总排名
                    total_rank = next((rank for (name, _), _, rank in total_rankings
                                       if
                                       (isinstance(name, tuple) and name[0] == supplier_name) or name == supplier_name),
                                      'N/A')

                    # 获取项目数量
                    project_count = 0
                    if supplier_name in service_info_dict:
                        project_count = service_info_dict[supplier_name].get('project_count', 0)

                    area_data.append([
                        str(area_rank),
                        supplier_name,
                        str(project_count),
                        f"{score:.2f}",
                        level,
                        f"第{total_rank}名"
                    ])

                area_table = Table(area_data,
                                   colWidths=[0.8 * inch, 2.2 * inch, 0.8 * inch, 1 * inch, 0.8 * inch, 0.8 * inch])

                area_style = [
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]

                # 地区前三名高亮
                if len(rankings) > 0:
                    area_style.append(('BACKGROUND', (0, 1), (-1, 1), colors.gold))
                if len(rankings) > 1:
                    area_style.append(('BACKGROUND', (0, 2), (-1, 2), colors.silver))
                if len(rankings) > 2:
                    area_style.append(('BACKGROUND', (0, 3), (-1, 3), colors.brown))

                area_table.setStyle(TableStyle(area_style))
                story.append(area_table)
                story.append(Spacer(1, 0.5 * inch))

            # 生成PDF
            doc.build(story)
            print(f"成功生成汇总报告: {output_path}")

        except Exception as e:
            print(f"生成汇总报告时出错: {str(e)}")
            import traceback
            traceback.print_exc()
            self._generate_matplotlib_summary_by_area(rankings_by_area, total_rankings, output_path)


    def generate_summary_report(self, rankings: List[Tuple[str, float, int]],
                                output_path: str):
        """生成汇总排名报告（兼容旧接口）"""
        # 转换为新格式
        rankings_with_area = []
        for supplier, score, rank in rankings:
            rankings_with_area.append(((supplier, '未知'), score, rank))

        self.generate_summary_report_by_area({}, rankings_with_area, output_path)

    def _generate_matplotlib_report(self, supplier_name: str, analysis_data: Dict,
                                    output_path: str):
        """使用matplotlib生成报告（备选方案）"""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages

        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        output_path = output_path.replace('.pdf', '_matplotlib.pdf')

        with PdfPages(output_path) as pdf:
            # 第1页：封面
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.5, 0.8, supplier_name, ha='center', fontsize=24, weight='bold')
            fig.text(0.5, 0.7, '供应商评估报告', ha='center', fontsize=20)

            service_area = analysis_data.get('service_area', '未知')
            fig.text(0.5, 0.65, f'服务地区：{service_area}', ha='center', fontsize=16)
            fig.text(0.5, 0.6, f'生成日期：{datetime.now().strftime("%Y年%m月%d日")}',
                     ha='center', fontsize=14)

            score_text = f"""
        综合评分：{analysis_data['total_score']:.2f} 分
        评级：{analysis_data['level']}
        服务地区：{service_area}
        地区内排名：第 {analysis_data.get('area_rank', 'N/A')} 名
        总排名：第 {analysis_data.get('rank', 'N/A')} 名

        物管处评分：{analysis_data['property_score']:.2f} 分（权重60%）
        职能部门评分：{analysis_data['functional_score']:.2f} 分（权重40%）
                    """
            fig.text(0.5, 0.3, score_text, ha='center', fontsize=16,
                     bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray"))

            plt.axis('off')
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()

            print(f"使用matplotlib生成报告: {output_path}")

    def _generate_matplotlib_summary_by_area(self, rankings_by_area: Dict[str, List[Tuple[str, float, int]]],
                                             total_rankings: List[Tuple[str, float, int]], output_path: str):
        """使用matplotlib生成分地区汇总报告（备选方案）"""
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_pdf import PdfPages

        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False

        output_path = output_path.replace('.pdf', '_matplotlib.pdf')

        with PdfPages(output_path) as pdf:
            # 第1页：总体排名
            fig = plt.figure(figsize=(8.27, 11.69))

            fig.text(0.5, 0.9, '供应商评估汇总报告',
                     ha='center', fontsize=24, weight='bold')
            fig.text(0.5, 0.85, f'生成日期：{datetime.now().strftime("%Y年%m月%d日")}',
                     ha='center', fontsize=14)

            # 创建总排名表格
            ax = fig.add_subplot(111)
            ax.axis('tight')
            ax.axis('off')

            headers = ['排名', '供应商名称', '服务地区', '综合得分', '评级']
            table_data = []

            for supplier_info, score, rank in total_rankings[:10]:  # 只显示前10名
                supplier_name, service_area = supplier_info
                level = self._get_score_level(score)
                table_data.append([str(rank), supplier_name, service_area, f'{score:.2f}', level])

            table = ax.table(cellText=table_data,
                             colLabels=headers,
                             cellLoc='center',
                             loc='center',
                             colWidths=[0.1, 0.4, 0.15, 0.15, 0.15])

            table.auto_set_font_size(False)
            table.set_fontsize(11)
            table.scale(1.2, 1.5)

            pdf.savefig(fig, bbox_inches='tight')
            plt.close()

            # 分地区页面
            for area, rankings in rankings_by_area.items():
                fig = plt.figure(figsize=(8.27, 11.69))

                fig.text(0.5, 0.9, f'{area}供应商排名',
                         ha='center', fontsize=20, weight='bold')

                ax = fig.add_subplot(111)
                ax.axis('tight')
                ax.axis('off')

                headers = ['地区排名', '供应商名称', '综合得分', '评级']
                table_data = []

                for supplier_info, score, area_rank in rankings:
                    supplier_name, _ = supplier_info
                    level = self._get_score_level(score)
                    table_data.append([str(area_rank), supplier_name, f'{score:.2f}', level])

                table = ax.table(cellText=table_data,
                                 colLabels=headers,
                                 cellLoc='center',
                                 loc='center',
                                 colWidths=[0.15, 0.5, 0.15, 0.15])

                table.auto_set_font_size(False)
                table.set_fontsize(12)
                table.scale(1.2, 1.5)

                pdf.savefig(fig, bbox_inches='tight')
                plt.close()

            print(f"使用matplotlib生成汇总报告: {output_path}")

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
            ('FONTNAME', (0, 0), (-1, -1), self.chinese_font),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ])

    def _get_score_level(self, score: float) -> str:
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

    # 调用大模型生成最终评价
    def _generate_feedback(self, analysis_data: Dict):
        print('正在调用大模型生成评价...')
        return call_LLM(analysis_data)