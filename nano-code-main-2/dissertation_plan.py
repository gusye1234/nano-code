from pydantic import BaseModel
from typing import List, Dict, Any
import json
from json_repair import repair_json


# 定义Pydantic模型
class CodeRepositoryReview(BaseModel):
    url: str
    description: str
    analysis_focus: List[str]


class ReproductionTask(BaseModel):
    phase: str
    target: str
    methodology: str


class CriticalEvaluation(BaseModel):
    failure_case_study: str
    improvement_directions: List[str]


class ExperimentalRequirements(BaseModel):
    code_repository_review: CodeRepositoryReview
    reproduction_tasks: List[ReproductionTask]
    critical_evaluation: CriticalEvaluation


class UrlInfo(BaseModel):
    url: str
    description: str


class DissertationPlan(BaseModel):
    dissertation_title: str
    literature_topic: List[str]
    experimental_requirements: ExperimentalRequirements
    urls: List[UrlInfo]


# 原始JSON字符串
json_str = '''{
  "dissertation_title": "From Coding Agent to the General Agent: Research into Real-world Coding Agents and Advanced Agent Algorithms",
  "literature_topic": [
    "Coding Agents in Real-world Applications",
    "Generalization of Intelligent Agents",
    "Agent Architecture Analysis",
    "Advanced Agent Algorithms",
    "Optimization of Agent Systems"
  ],
  "experimental_requirements": {
    "code_repository_review": {
      "url": "https://github.com/gusye1234/nano-code",
      "description": "This GitHub repository, nano-code, contains the source code for a coding agent system. It is essential for reviewing the current code structure, understanding the working principles of the agent, and forming the base for conducting optimization experiments.",
      "analysis_focus": [
        "Code architecture (structure, modularity, workflow)",
        "Agent's mechanism of operation",
        "Existing algorithms and implementation details",
        "Points of integration for proposed optimizations"
      ]
    },
    "reproduction_tasks": [
      {
        "phase": "Initial Review and Documentation",
        "target": "Understand and document the agent's workflow and architecture",
        "methodology": "Analyze the code base and associated documentation; produce a code architecture analysis diagram"
      },
      {
        "phase": "Agent Algorithm Research and Comparative Study",
        "target": "Determine strengths and weaknesses of current agent algorithms",
        "methodology": "Survey literature and compare with nano-code's approach; analyze and report on agent architectures"
      },
      {
        "phase": "Proposal and Implementation of Optimizations",
        "target": "Suggest and test optimization directions for nano-code",
        "methodology": "Design and implement optimizations, evaluate performance impacts, document results"
      }
    ],
    "critical_evaluation": {
      "failure_case_study": "Document any limitations or failure cases in the current agent’s architecture and workflow, such as scalability issues, response accuracy, or performance bottlenecks.",
      "improvement_directions": [
        "Enhancement of agent's decision-making algorithms",
        "Refactoring code for scalability and maintainability",
        "Integration of state-of-the-art agent architectures",
        "Performance optimization under real-world coding tasks"
      ]
    }
  },
  "urls": [
    {
      "url": "https://github.com/gusye1234/nano-code",
      "description": "The official code repository for nano-code, which needs to be reviewed for its architecture, functioning, and potential areas for improvement."
    }
  ]
}'''

# 修复JSON并解析到Pydantic模型
try:
    # 修复可能的JSON格式问题
    repaired_json = repair_json(json_str)
    # 解析为字典
    data = json.loads(repaired_json)
    # 转换为Pydantic模型对象
    dissertation_plan = DissertationPlan(**data)

    # 验证数据加载成功
    print("Successfully loaded data into Pydantic model:")
    print(f"Dissertation Title: {dissertation_plan.dissertation_title}")
    print(f"Number of literature topics: {len(dissertation_plan.literature_topic)}")
    print(f"Code repository URL: {dissertation_plan.experimental_requirements.code_repository_review.url}")
    print(dissertation_plan.model_dump())

except Exception as e:
    print(f"Error processing JSON: {str(e)}")
