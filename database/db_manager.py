"""数据库管理"""
import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime
from .models import Supplier, Evaluation, EvaluationDimension

class DatabaseManager:
    def __init__(self, db_path: str = 'supplier_evaluation.db'):
        self.db_path = db_path
        # 设置SQLite的日期时间解析
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
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

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

            conn.commit()

    def insert_supplier(self, name: str) -> int:
        """插入供应商，返回ID"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO suppliers (name) VALUES (?)",
                (name,)
            )
            cursor.execute("SELECT id FROM suppliers WHERE name = ?", (name,))
            result = cursor.fetchone()
            return result['id'] if result else None

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

    def get_supplier_evaluations(self, supplier_name: str) -> List[Dict]:
        """获取供应商的所有评估记录"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.*, s.name as supplier_name
                FROM evaluations e
                JOIN suppliers s ON e.supplier_id = s.id
                WHERE s.name = ?
            ''', (supplier_name,))

            results = []
            for row in cursor.fetchall():
                record = dict(row)
                record['scores'] = json.loads(record['scores']) if record['scores'] else {}
                record['feedback'] = json.loads(record['feedback']) if record['feedback'] else {}
                results.append(record)

            return results

    def get_all_suppliers(self) -> List[str]:
        """获取所有供应商名称"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM suppliers")
            return [row['name'] for row in cursor.fetchall()]
