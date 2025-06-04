"""数据库管理"""
import sqlite3
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from .models import Supplier, Evaluation, EvaluationDimension, SupplierService

class DatabaseManager:
    def __init__(self, db_path: str = 'supplier_evaluation.db'):
        self.db_path = db_path
        self.init_database()

    def _get_connection(self):
        """获取数据库连接并设置日期时间处理"""
        conn = sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        conn.row_factory = sqlite3.Row
        return conn

    def init_database(self):
        """初始化数据库表"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 供应商表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    service_area TEXT DEFAULT '市内',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 检查是否需要添加service_area列（兼容旧数据库）
            cursor.execute("PRAGMA table_info(suppliers)")
            columns = [column[1] for column in cursor.fetchall()]
            if 'service_area' not in columns:
                cursor.execute("ALTER TABLE suppliers ADD COLUMN service_area TEXT DEFAULT '市内'")

            # 评估维度表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evaluation_dimensions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('property', 'functional')),
                    weight REAL NOT NULL DEFAULT 1.0
                )
            ''')

            # 评估记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS evaluations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    evaluator_name TEXT NOT NULL,
                    evaluator_dept TEXT,
                    evaluator_phone TEXT,
                    evaluation_type TEXT NOT NULL CHECK(evaluation_type IN ('property', 'functional')),
                    evaluation_date TEXT,
                    scores TEXT NOT NULL,
                    feedback TEXT,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
                )
            ''')

            # 新增：供应商服务情况表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS supplier_services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    project_count INTEGER DEFAULT 0,
                    project_names TEXT,
                    project_ratio REAL DEFAULT 0.0,
                    remarks TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers (id)
                )
            ''')

            conn.commit()

    def update_supplier_service(self, supplier_name: str, project_count: int,
                               project_names: str, project_ratio: float, remarks: str = "") -> bool:
        """更新供应商服务情况"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 获取供应商ID
            cursor.execute("SELECT id FROM suppliers WHERE name = ?", (supplier_name,))
            result = cursor.fetchone()

            if not result:
                print(f"警告: 未找到供应商 {supplier_name}")
                return False

            supplier_id = result['id']

            # 检查是否已有记录
            cursor.execute("SELECT id FROM supplier_services WHERE supplier_id = ?", (supplier_id,))
            existing = cursor.fetchone()

            if existing:
                # 更新现有记录
                cursor.execute('''
                    UPDATE supplier_services
                    SET project_count = ?, project_names = ?, project_ratio = ?,
                        remarks = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE supplier_id = ?
                ''', (project_count, project_names, project_ratio, remarks, supplier_id))
            else:
                # 插入新记录
                cursor.execute('''
                    INSERT INTO supplier_services
                    (supplier_id, project_count, project_names, project_ratio, remarks)
                    VALUES (?, ?, ?, ?, ?)
                ''', (supplier_id, project_count, project_names, project_ratio, remarks))

            conn.commit()
            return True

    def get_supplier_service_info(self, supplier_name: str) -> Optional[Dict]:
        """获取供应商服务情况"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT ss.*
                FROM supplier_services ss
                JOIN suppliers s ON ss.supplier_id = s.id
                WHERE s.name = ?
            ''', (supplier_name,))

            result = cursor.fetchone()
            if result:
                return dict(result)
            return None

    def get_all_supplier_services(self) -> List[Dict]:
        """获取所有供应商服务情况"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute('''
                SELECT s.name, s.service_area, ss.*
                FROM suppliers s
                LEFT JOIN supplier_services ss ON s.id = ss.supplier_id
                ORDER BY s.name
            ''')

            results = []
            for row in cursor.fetchall():
                results.append(dict(row))

            return results

    def get_all_suppliers(self) -> List[Tuple[str, str]]:
        """获取所有供应商名称和服务地区"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, service_area FROM suppliers")
            return [(row['name'], row['service_area']) for row in cursor.fetchall()]

    def get_suppliers_by_area(self, service_area: str) -> List[str]:
        """根据服务地区获取供应商"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM suppliers WHERE service_area = ?", (service_area,))
            return [row['name'] for row in cursor.fetchall()]
    def get_supplier_evaluations(self, supplier_name: str) -> List[Dict]:
        """获取供应商的所有评估记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 先查询供应商ID
            cursor.execute("SELECT id, service_area FROM suppliers WHERE name = ?", (supplier_name,))
            supplier_row = cursor.fetchone()

            if not supplier_row:
                print(f"警告: 未找到供应商 {supplier_name}")
                return []

            supplier_id = supplier_row['id']
            service_area = supplier_row['service_area']

            # 查询所有评估记录
            cursor.execute('''
                SELECT e.*, s.name as supplier_name, s.service_area
                FROM evaluations e
                JOIN suppliers s ON e.supplier_id = s.id
                WHERE s.id = ?
            ''', (supplier_id,))

            results = []
            rows = cursor.fetchall()

            print(f"\n从数据库获取供应商 {supplier_name} 的评估记录:")
            print(f"  供应商ID: {supplier_id}")
            print(f"  找到 {len(rows)} 条评估记录")

            for i, row in enumerate(rows):
                record = dict(row)

                # 解析JSON字段
                try:
                    record['scores'] = json.loads(record['scores']) if record['scores'] else {}
                    record['feedback'] = json.loads(record['feedback']) if record['feedback'] else {}
                except json.JSONDecodeError as e:
                    print(f"  警告: 解析第{i + 1}条记录的JSON数据失败: {e}")
                    record['scores'] = {}
                    record['feedback'] = {}

                # 调试输出
                print(f"  记录{i + 1}: 类型={record.get('evaluation_type')}, "
                      f"评估人={record.get('evaluator_name')}, "
                      f"部门={record.get('evaluator_dept')}, "
                      f"评分项数={len(record.get('scores', {}))}")

                results.append(record)

            return results

    def insert_supplier(self, name: str, service_area: str = '市内') -> int:
        """插入供应商，返回ID（如果已存在则返回现有ID）"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 先查询是否已存在
            cursor.execute("SELECT id FROM suppliers WHERE name = ?", (name,))
            result = cursor.fetchone()

            if result:
                # 供应商已存在，更新服务地区（如果需要）并返回现有ID
                supplier_id = result['id']
                cursor.execute(
                    "UPDATE suppliers SET service_area = ? WHERE id = ?",
                    (service_area, supplier_id)
                )
                print(f"  供应商已存在: {name} (ID: {supplier_id})")
                return supplier_id
            else:
                # 供应商不存在，插入新记录
                cursor.execute(
                    "INSERT INTO suppliers (name, service_area) VALUES (?, ?)",
                    (name, service_area)
                )
                supplier_id = cursor.lastrowid
                print(f"  新增供应商: {name} (ID: {supplier_id})")
                return supplier_id

    def update_supplier_service_area(self, supplier_name: str, service_area: str):
        """更新供应商服务地区"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE suppliers SET service_area = ? WHERE name = ?",
                (service_area, supplier_name)
            )
            conn.commit()
    def insert_evaluation(self, evaluation: Evaluation) -> int:
        """插入评估记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # 处理日期时间
            eval_date = evaluation.evaluation_date
            if isinstance(eval_date, datetime):
                eval_date_str = eval_date.strftime('%Y-%m-%d %H:%M:%S')
            else:
                eval_date_str = str(eval_date) if eval_date else datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            cursor.execute('''
                INSERT INTO evaluations
                (supplier_id, evaluator_name, evaluator_dept, evaluator_phone,
                 evaluation_type, evaluation_date, scores, feedback)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                evaluation.supplier_id,
                evaluation.evaluator_name,
                evaluation.evaluator_dept,
                evaluation.evaluator_phone,
                evaluation.evaluation_type,
                eval_date_str,
                json.dumps(evaluation.scores, ensure_ascii=False) if evaluation.scores else '{}',
                json.dumps(evaluation.feedback, ensure_ascii=False) if evaluation.feedback else '{}'
            ))
            return cursor.lastrowid


