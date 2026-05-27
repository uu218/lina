from pydantic import BaseModel, Field
from typing import List


class CorePoint(BaseModel):
    point_id: str = Field(..., description="采分点唯一标识，如 P1, P2")
    description: str = Field(..., description="采分点的核心得分含义、关键词或核心表述")
    weight_score: float = Field(..., description="该采分点所占的分值")


class EvaluationDimension(BaseModel):
    dimension_name: str = Field(..., description="评分维度，如：归纳概括能力、对策针对性、语言表达")
    total_score: float = Field(..., description="该维度的满分值")
    core_points: List[CorePoint] = Field(..., description="该维度下的具体采分点列表")


class UnifiedRubric(BaseModel):
    title: str = Field(..., description="申论题目名称/要求摘要")
    max_total_score: float = Field(..., description="试卷总分")
    dimensions: List[EvaluationDimension] = Field(..., description="多维度评分大纲")


class PointMatchResult(BaseModel):
    point_id: str = Field(..., description="对应阶段1的采分点ID")
    is_matched: bool = Field(..., description="用户文章是否命中该点")
    score_awarded: float = Field(..., description="该点实际得分")
    evidence: str = Field(..., description="从用户文章中摘录的原句，未命中留空")
    reason: str = Field(..., description="判定逻辑说明")


class DimensionGrade(BaseModel):
    dimension_name: str = Field(..., description="评分维度名称")
    score: float = Field(..., description="维度实际总得分")
    match_details: List[PointMatchResult] = Field(..., description="逐一比对结果")
    comments: str = Field(..., description="评语")


class FinalReport(BaseModel):
    total_score: float = Field(..., description="用户文章最终总得分")
    dimension_grades: List[DimensionGrade] = Field(..., description="各维度得分详情")
    summary_feedback: str = Field(..., description="全局宏观总评")
    upgrade_suggestions: List[str] = Field(..., description="修改建议")
