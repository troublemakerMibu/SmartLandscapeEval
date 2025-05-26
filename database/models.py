"""数据模型定义"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict

@dataclass
class Supplier:
    """供应商信息"""
    id: Optional[int] = None
    name: str = ""
    created_at: Optional[datetime] = None

@dataclass
class Evaluation:
    """评估记录"""
    id: Optional[int] = None
    supplier_id: int = 0
    evaluator_name: str = ""
    evaluator_dept: str = ""
    evaluator_phone: str = ""
    evaluation_type: str = ""  # 'property' 或 'functional'
    evaluation_date: Optional[datetime] = None
    scores: Dict[str, float] = None
    feedback: Dict[str, str] = None

@dataclass
class EvaluationDimension:
    """评估维度"""
    id: Optional[int] = None
    code: str = ""
    name: str = ""
    type: str = ""  # 'property' 或 'functional'
    weight: float = 0.0
