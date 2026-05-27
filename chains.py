"""
核心逻辑层：双阶段 Prompt 处理链
基于 LangChain LCEL 与 PydanticOutputParser 实现 (完美适配 DeepSeek)
"""

import os
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

from models import UnifiedRubric, FinalReport

# 加载 .env 文件中的环境变量
load_dotenv() 

# ============================================================
# Prompt 模板
# ============================================================

# 注意：我们在 Prompt 中挖了一个 {format_instructions} 的坑，用来注入 JSON 格式要求
STAGE1_SYSTEM_PROMPT = """【系统角色】国家公务员考试阅卷组组长。
【任务描述】对比【申论题目】、【给定材料】及【多家机构答案】。抽丝剥茧，合并同义表述，提炼一份客观、严谨的【统一采分点大纲】。
【规则】
1. 合并同义表述为核心采分点。
2. 科学拆解分值，总和须等于总分。
3. 严格遵守下方给定的 JSON 格式输出。

{format_instructions}"""

STAGE1_USER_PROMPT = """1. 题目：{question_text}
2. 材料：{material_text}
3. 机构答案：{agency_answers}"""

STAGE2_SYSTEM_PROMPT = """【系统角色】资深阅卷专家，绝不放过套话。
【任务描述】根据【统一采分点大纲】，逐句扫描【用户文章】寻找实质性表述。
【规则】
1. 实质大于形式，仅堆砌假大空套话不给分。
2. 必须在 `evidence` 摘录原句，找不到视作未命中。
3. 缺失点必须在 `reason` 中说明。
4. 严格遵守下方给定的 JSON 格式输出。

{format_instructions}"""

STAGE2_USER_PROMPT = """1. 统一采分点大纲：{unified_rubric_json}
2. 用户文章：{user_essay}"""


# ============================================================
# 模型工厂
# ============================================================

def create_model(
    model_name: str = "deepseek-chat",
    temperature: float = 0.0,
    max_tokens: int = 8192,
    **kwargs
):
    """
    创建 LLM 实例，专为 DeepSeek 配置。
    """
    api_key = kwargs.pop("api_key", os.getenv("DEEPSEEK_API_KEY"))
    base_url = kwargs.pop("base_url", os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"))
    
    if not api_key:
        raise ValueError("❌ 未找到 DEEPSEEK_API_KEY，请确保在 .env 文件中进行了配置！")

    return ChatOpenAI(
        model=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        base_url=base_url,
        api_key=api_key,
        # 移除了容易引起 400 报错的强制模型参数，回归最纯净的对话模式
        **kwargs
    )


# ============================================================
# 阶段 1 链：标准提炼
# ============================================================

def build_stage1_chain(model=None):
    llm = model or create_model()
    # 1. 初始化 Pydantic 解析器
    parser = PydanticOutputParser(pydantic_object=UnifiedRubric)
    
    # 2. 将解析规则注入到 Prompt 中
    prompt = ChatPromptTemplate.from_messages([
        ("system", STAGE1_SYSTEM_PROMPT),
        ("user", STAGE1_USER_PROMPT),
    ]).partial(format_instructions=parser.get_format_instructions())

    # 3. 串联：Prompt -> LLM -> Parser 解析回 Pydantic 对象
    return prompt | llm | parser


# ============================================================
# 阶段 2 链：深度对标批改
# ============================================================

def build_stage2_chain(model=None):
    llm = model or create_model()
    parser = PydanticOutputParser(pydantic_object=FinalReport)

    prompt = ChatPromptTemplate.from_messages([
        ("system", STAGE2_SYSTEM_PROMPT),
        ("user", STAGE2_USER_PROMPT),
    ]).partial(format_instructions=parser.get_format_instructions())

    return prompt | llm | parser


# ============================================================
# 完整流水线
# ============================================================

class EssayGraderPipeline:
    def __init__(self, model=None):
        self.model = model or create_model()
        self.stage1_chain = build_stage1_chain(self.model)
        self.stage2_chain = build_stage2_chain(self.model)

    def run_stage1(
        self,
        question_text: str,
        material_text: str,
        agency_answers: str
    ) -> UnifiedRubric:
        return self.stage1_chain.invoke({
            "question_text": question_text,
            "material_text": material_text,
            "agency_answers": agency_answers,
        })

    def run_stage2(
        self,
        unified_rubric: UnifiedRubric,
        user_essay: str
    ) -> FinalReport:
        rubric_json = unified_rubric.model_dump_json(indent=2, ensure_ascii=False)
        return self.stage2_chain.invoke({
            "unified_rubric_json": rubric_json,
            "user_essay": user_essay,
        })

    def run(
        self,
        question_text: str,
        material_text: str,
        agency_answers: str,
        user_essay: str
    ) -> FinalReport:
        rubric = self.run_stage1(question_text, material_text, agency_answers)
        return self.run_stage2(rubric, user_essay)