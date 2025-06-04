"""供应商服务情况处理器"""
import pandas as pd
from typing import Dict
from database.db_manager import DatabaseManager

class ServiceInfoProcessor:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def import_service_info(self, excel_path: str):
        """导入供应商服务情况Excel"""
        print(f"\\n=== 导入供应商服务情况 ===")
        print(f"文件: {excel_path}")

        try:
            # 读取Excel文件
            df = pd.read_excel(excel_path)

            # 打印列名以调试
            print(f"Excel列名: {list(df.columns)}")

            # 统计信息
            success_count = 0
            failed_count = 0

            for idx, row in df.iterrows():
                try:
                    # 提取数据
                    supplier_name = str(row.get('外包公司名称', '')).strip()
                    project_count = int(row.get('项目数量', 0))
                    project_names = str(row.get('项目名称', '')).strip()

                    # 处理项目占比
                    project_ratio_str = str(row.get('项目占比', '0%'))
                    # 移除百分号并转换为小数
                    project_ratio = float(project_ratio_str.replace('%', '')) / 100

                    remarks = str(row.get('备注', '')).strip() if pd.notna(row.get('备注')) else ''

                    if not supplier_name:
                        print(f"  行{idx+2}: 跳过（供应商名称为空）")
                        continue

                    # 更新数据库
                    success = self.db_manager.update_supplier_service(
                        supplier_name=supplier_name,
                        project_count=project_count,
                        project_names=project_names,
                        project_ratio=project_ratio,
                        remarks=remarks
                    )

                    if success:
                        success_count += 1
                        print(f"  行{idx+2}: 成功导入 {supplier_name} - {project_count}个项目 ({project_ratio*100:.2f}%)")
                    else:
                        failed_count += 1
                        print(f"  行{idx+2}: 导入失败 {supplier_name}")

                except Exception as e:
                    failed_count += 1
                    print(f"  行{idx+2}: 处理失败 - {str(e)}")

            print(f"\\n导入完成: 成功 {success_count} 条，失败 {failed_count} 条")

        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
