import json
import uuid
from typing import List, Tuple

from ..models.dissertation_plan import DissertationPlan, AgentCommunication
from ..core.session import Session
from ..utils.logger import AIConsoleLogger
from ..llm import llm_complete


def read_plan(input_path: str) -> DissertationPlan:
    """从JSON文件中读取研究计划"""
    return DissertationPlan.from_file(input_path)

def extract_tasks(plan: DissertationPlan) -> List[str]:
    """
    提取需要判断的任务候选项
    
    """
    tasks: List[str] = []

    # 1) 代码仓库分析关注点
    try:
        for focus in plan.experimental_requirements.code_repository_review.analysis_focus:
            if focus and isinstance(focus, str):
                tasks.append(f"分析关注点: {focus}")
    except:
        pass

    # 2) 复现任务的目标和方法
    try:
        for task in plan.experimental_requirements.reproduction_tasks:
            tasks.append(f"阶段[{task.phase}] 目标: {task.target} | 方法: {task.methodology}")
    except:
        pass

    # 3) 批判性评估
    try:
        ce = plan.experimental_requirements.critical_evaluation
        if ce.failure_case_study:
            tasks.append(f"失败案例: {ce.failure_case_study}")
        for direction in ce.improvement_directions or []:
            if direction and isinstance(direction, str):
                tasks.append(f"改进方向: {direction}")  

    except:
        pass

    return tasks

def build_simple_prompt(task: str, plan: DissertationPlan) -> Tuple[str, list[dict]]:
    """
    根据task构建prompt
    """
    
    # 提取计划中的可用资源信息
    available_resources = []
    
    if hasattr(plan.experimental_requirements, 'code_repository_review'):
        repo = plan.experimental_requirements.code_repository_review
        available_resources.append(f"代码仓库: {repo.url}")
        available_resources.append(f"仓库描述: {repo.description}")
    
    
    resources_text = "\n".join(available_resources) if available_resources else "无特定代码仓库"
    
    system_prompt = f"""你是一个严格的决策器，判断给定任务是否需要额外的外部资料搜索。

            【内部可获得的资料范围】
            - 研究计划JSON文件中提供的所有信息
            - 指定的代码仓库URL（等同于我们能完整获取和分析源码）
            - 通过代码仓库分析可以直接得到的内容：
            * 代码架构和结构分析
            * 工作流程和机制理解  
            * 现有算法实现细节
            * 代码质量和性能分析
            * 模块化程度和集成点识别
            - 本地已克隆的代码副本和生成的分析文档
            - 历史分析结果和报告

            【外部资料定义】
            仅指无法从上述内部资料获得的内容，需要额外搜索的资料：
            - 学术文献和研究论文
            - 行业对比数据和benchmark
            - 其他项目的实现方案对比
            - 最新的技术趋势和标准
            - 领域专家经验和最佳实践

            【当前研究计划的可用资源】
            {resources_text}

            【判断规则】
            - 如果任务可以通过分析指定代码仓库、已有信息和内部资料完成 → NO_NEED
            - 如果任务明确需要外部文献、对比数据、行业调研等外部资料 → NEED: <简洁描述>

            【输出格式要求】
            严格按照以下格式输出，保持简洁：
            - NO_NEED
            - NEED: <最多20个字的简洁中文描述，例如"需要Agent对比研究的学术论文"或"需要编码基准测试数据">

            【重要】：搜索请求必须简洁明了，避免冗长描述、技术细节或具体要求清单。
            """

    user_content = f"【待评估任务】\n{task}\n\n请严格按照上述标准判断该任务是否需要外部资料搜索。"
    
    return system_prompt, [{"role": "user", "content": user_content}]

def parse_result(llm_output: str) -> Tuple[bool, str]:
    """解析LLM判断结果"""
    if not llm_output:
        return False, ""
    
    text = llm_output.strip().upper()
    first_line = text.splitlines()[0].strip()
    
    if first_line.startswith("NO_NEED"):
        return False, ""
    elif first_line.startswith("NEED"):
        # 提取NEED后的内容
        parts = first_line.split(":", 1)
        if len(parts) == 2:
            return True, parts[1].strip()[:400]
        else:
            return True, first_line[4:].strip()[:400]
    
    return False, ""

async def judge_task(session: Session, task: str, plan: DissertationPlan) -> Tuple[bool, str]:
    """使用LLM判断单个任务是否需要外部资料"""
    system_prompt, messages = build_simple_prompt(task, plan)
    
    try:
        resp = await llm_complete(
            session=session,
            model=session.working_env.llm_main_model,
            messages=messages,
            system_prompt=system_prompt,
        )
        content = resp.choices[0].message.content if resp and resp.choices else ""
        return parse_result(content)
    except Exception:
        return False, ""

def create_search_requests(tasks: List[str], judgements: List[Tuple[bool, str]]) -> List[AgentCommunication]:
    """根据判断结果创建搜索请求"""
    requests = []
    
    for task, (need_search, search_desc) in zip(tasks, judgements):
        if need_search:
            request_text = search_desc if search_desc else f"请为以下任务提供外部资料：{task}"
            requests.append(
                AgentCommunication(
                    id=str(uuid.uuid4()),
                    request=request_text,
                    response=""
                )
            )
    
    return requests

def save_result(plan: DissertationPlan, search_requests: List[AgentCommunication], output_path: str):
    """保存结果到文件"""
    data = plan.model_dump()
    data["agent_communicate"] = [req.model_dump() for req in search_requests]
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

async def run_decision(input_path: str, output_path: str, working_dir: str) -> None:
    """运行决策判断的主流程"""
    # 初始化
    logger = AIConsoleLogger()
    session = Session(working_dir=working_dir, logger=logger)
    
    # 读取计划
    plan = read_plan(input_path)
    
    # 检查是否为第一次分析
    if plan.is_first_time:
        save_result(plan, [], output_path)
        return
    
    # 提取任务并判断
    tasks = extract_tasks(plan)
    
    judgements = []
    for i, task in enumerate(tasks, 1):
        need_search, search_desc = await judge_task(session, task, plan)
        judgements.append((need_search, search_desc))
    
    # 创建搜索请求并保存
    search_requests = create_search_requests(tasks, judgements)
    save_result(plan, search_requests, output_path)
