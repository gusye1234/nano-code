"""
文献搜索规划工具
为Search Agent生成详细的文献搜索任务规范
"""

import json
from typing import Dict, Any, List
from .base import AgentToolDefine, AgentToolReturn


class PlanLiteratureSearchTool(AgentToolDefine):
    """规划文献搜索任务的工具"""

    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="plan_literature_search",
            description="""为Search Agent规划详细的文献搜索策略和任务。
基于研究意图分析结果，生成包含搜索关键词、数据源、质量标准等的完整搜索计划。""",
            parameters_schema={
                "type": "object",
                "properties": {
                    "research_intent": {
                        "type": "object",
                        "description": "从analyze_research_intent工具获得的研究意图分析结果",
                        "properties": {
                            "core_question": {"type": "string"},
                            "research_type": {"type": "string"},
                            "objectives": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "domain_context": {"type": "object"},
                            "complexity_analysis": {"type": "object"}
                        },
                        "required": ["core_question", "research_type", "domain_context"]
                    },
                    "search_constraints": {
                        "type": "object",
                        "description": "搜索约束条件",
                        "properties": {
                            "time_range": {
                                "type": "string",
                                "description": "时间范围，如'recent_5_years', 'all_time'"
                            },
                            "language_preference": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "语言偏好，如['chinese', 'english']"
                            },
                            "source_types": {
                                "type": "array", 
                                "items": {"type": "string"},
                                "description": "资源类型，如['academic_papers', 'blog_posts', 'documentation']"
                            }
                        }
                    }
                },
                "required": ["research_intent"]
            }
        )

    async def _execute(self, arguments: Dict[str, Any]) -> AgentToolReturn:
        """执行搜索规划"""
        research_intent = arguments["research_intent"]
        search_constraints = arguments.get("search_constraints", {})
        
        # 生成搜索计划
        search_plan = await self._generate_search_plan(research_intent, search_constraints)
        
        return AgentToolReturn.success(self.name, search_plan)

    async def _generate_search_plan(self, research_intent: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """生成详细的搜索计划"""
        
        # 1. 生成搜索关键词策略
        keyword_strategy = self._generate_keyword_strategy(research_intent)
        
        # 2. 确定数据源和平台
        data_sources = self._determine_data_sources(research_intent, constraints)
        
        # 3. 设置搜索质量标准
        quality_criteria = self._define_quality_criteria(research_intent, constraints)
        
        # 4. 制定搜索阶段计划
        search_phases = self._plan_search_phases(research_intent)
        
        # 5. 预期输出规格
        expected_outputs = self._define_expected_outputs(research_intent)
        
        return {
            "search_strategy": {
                "approach": self._determine_search_approach(research_intent["research_type"]),
                "keyword_strategy": keyword_strategy,
                "data_sources": data_sources,
                "search_phases": search_phases
            },
            "quality_criteria": quality_criteria,
            "expected_outputs": expected_outputs,
            "success_metrics": self._define_search_success_metrics(research_intent),
            "estimated_effort": self._estimate_search_effort(research_intent, constraints)
        }

    def _generate_keyword_strategy(self, research_intent: Dict[str, Any]) -> Dict[str, Any]:
        """生成关键词搜索策略"""
        core_question = research_intent["core_question"]
        domain_context = research_intent["domain_context"]
        research_type = research_intent["research_type"]
        
        # 从核心问题提取主要概念
        primary_keywords = self._extract_primary_keywords(core_question, domain_context)
        
        # 根据研究类型生成特定关键词
        type_specific_keywords = self._generate_type_specific_keywords(research_type)
        
        # 生成相关和扩展关键词
        related_keywords = self._generate_related_keywords(primary_keywords, domain_context)
        
        # 构建搜索查询组合
        query_combinations = self._build_query_combinations(primary_keywords, related_keywords)
        
        return {
            "primary_keywords": primary_keywords,
            "type_specific_keywords": type_specific_keywords,
            "related_keywords": related_keywords,
            "query_combinations": query_combinations,
            "search_operators": self._recommend_search_operators(research_type)
        }

    def _extract_primary_keywords(self, core_question: str, domain_context: Dict[str, Any]) -> List[str]:
        """提取主要关键词"""
        keywords = []
        
        # 从领域上下文提取
        primary_domain = domain_context.get("primary_domain", "")
        
        domain_keywords = {
            "artificial_intelligence": ["artificial intelligence", "AI", "人工智能"],
            "machine_learning": ["machine learning", "ML", "机器学习", "算法", "模型"],
            "deep_learning": ["deep learning", "neural network", "深度学习", "神经网络"],
            "natural_language_processing": ["NLP", "natural language processing", "自然语言处理", "文本处理"],
            "computer_vision": ["computer vision", "image processing", "计算机视觉", "图像处理"],
            "data_science": ["data science", "data analysis", "数据科学", "数据分析"],
            "software_engineering": ["software engineering", "software development", "软件工程", "软件开发"]
        }
        
        if primary_domain in domain_keywords:
            keywords.extend(domain_keywords[primary_domain])
        
        # 从核心问题中提取关键术语
        question_lower = core_question.lower()
        
        # 技术关键词提取
        tech_terms = [
            "algorithm", "model", "framework", "system", "method", "approach",
            "算法", "模型", "框架", "系统", "方法", "技术"
        ]
        
        for term in tech_terms:
            if term in question_lower:
                keywords.append(term)
        
        return list(set(keywords))

    def _generate_type_specific_keywords(self, research_type: str) -> List[str]:
        """根据研究类型生成特定关键词"""
        type_keywords = {
            "experimental": [
                "experiment", "empirical", "evaluation", "performance", "benchmark",
                "实验", "评估", "性能", "基准", "测试"
            ],
            "comparative": [
                "comparison", "comparative", "versus", "evaluation", "analysis",
                "比较", "对比", "分析", "评价"
            ],
            "survey": [
                "survey", "review", "overview", "systematic review", "literature review",
                "综述", "回顾", "总结", "文献综述"
            ],
            "theoretical": [
                "theory", "theoretical", "principle", "foundation", "mathematical",
                "理论", "原理", "数学", "基础"
            ],
            "applied": [
                "application", "practical", "implementation", "real-world", "case study",
                "应用", "实际", "实现", "案例", "实践"
            ]
        }
        
        return type_keywords.get(research_type, [])

    def _generate_related_keywords(self, primary_keywords: List[str], domain_context: Dict[str, Any]) -> List[str]:
        """生成相关和扩展关键词"""
        related = []
        
        # 基于主要关键词生成相关词
        for keyword in primary_keywords:
            if "learning" in keyword.lower():
                related.extend(["training", "optimization", "model", "algorithm"])
            elif "neural" in keyword.lower():
                related.extend(["network", "layer", "activation", "backpropagation"])
            elif "vision" in keyword.lower():
                related.extend(["image", "detection", "recognition", "segmentation"])
        
        # 添加技术栈相关词
        if domain_context.get("primary_domain") == "deep_learning":
            related.extend(["pytorch", "tensorflow", "CNN", "RNN", "transformer"])
        
        return list(set(related))

    def _build_query_combinations(self, primary: List[str], related: List[str]) -> List[str]:
        """构建搜索查询组合"""
        combinations = []
        
        # 单一主要关键词查询
        combinations.extend(primary[:5])  # 取前5个主要关键词
        
        # 主要关键词 + 相关词组合
        for p in primary[:3]:
            for r in related[:3]:
                combinations.append(f"{p} {r}")
                combinations.append(f'"{p}" AND "{r}"')
        
        # 多主要关键词组合
        if len(primary) >= 2:
            combinations.append(f'"{primary[0]}" AND "{primary[1]}"')
        
        return combinations

    def _recommend_search_operators(self, research_type: str) -> Dict[str, Any]:
        """推荐搜索操作符"""
        operators = {
            "boolean_operators": ["AND", "OR", "NOT"],
            "phrase_search": '使用引号进行精确短语搜索',
            "wildcard": "使用*进行通配符搜索",
            "field_search": "使用title:, author:, abstract: 等字段搜索"
        }
        
        if research_type == "comparative":
            operators["specific_tips"] = [
                '使用"A vs B", "A compared to B"格式',
                '搜索"comparison", "comparative study"'
            ]
        elif research_type == "survey":
            operators["specific_tips"] = [
                '使用"survey", "review", "state of the art"',
                '按时间倒序排列获取最新综述'
            ]
        
        return operators

    def _determine_data_sources(self, research_intent: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """确定数据源和搜索平台"""
        domain = research_intent["domain_context"]["primary_domain"]
        source_types = constraints.get("source_types", ["academic_papers", "documentation"])
        
        sources = {
            "academic_databases": [],
            "general_sources": [],
            "domain_specific": [],
            "priority_order": []
        }
        
        # 学术数据库
        if "academic_papers" in source_types:
            sources["academic_databases"] = [
                "Google Scholar",
                "IEEE Xplore", 
                "ACM Digital Library",
                "arXiv",
                "DBLP"
            ]
        
        # 通用信息源
        if "documentation" in source_types:
            sources["general_sources"] = [
                "官方文档和API文档",
                "GitHub项目和README",
                "技术博客和教程",
                "Stack Overflow"
            ]
        
        # 领域特定源
        domain_sources = {
            "machine_learning": ["Papers With Code", "Towards Data Science", "ML Conference Papers"],
            "deep_learning": ["Distill", "OpenAI Blog", "DeepMind Publications"],
            "software_engineering": ["ACM Software Engineering", "IEEE Software", "Medium Engineering"],
            "web_development": ["MDN Web Docs", "W3C Specifications", "Developer Blogs"]
        }
        
        if domain in domain_sources:
            sources["domain_specific"] = domain_sources[domain]
        
        # 设置优先级
        if research_intent["research_type"] == "survey":
            sources["priority_order"] = ["academic_databases", "domain_specific", "general_sources"]
        else:
            sources["priority_order"] = ["general_sources", "academic_databases", "domain_specific"]
        
        return sources

    def _define_quality_criteria(self, research_intent: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """定义搜索结果质量标准"""
        criteria = {
            "relevance": {
                "high_priority": [
                    "标题或摘要直接相关",
                    "包含主要关键词",
                    "符合研究类型"
                ],
                "medium_priority": [
                    "相关技术领域",
                    "类似应用场景"
                ]
            },
            "quality": {
                "academic_sources": [
                    "同行评议论文",
                    "会议论文 (A类/B类会议)",
                    "期刊文章 (影响因子>2)"
                ],
                "non_academic_sources": [
                    "官方文档和规范",
                    "知名技术博客", 
                    "开源项目文档",
                    "技术公司博客"
                ]
            },
            "recency": self._get_recency_requirements(research_intent, constraints),
            "language": constraints.get("language_preference", ["chinese", "english"]),
            "exclusion_criteria": [
                "广告和营销内容",
                "无技术深度的概述",
                "过时的技术信息 (>5年)",
                "无可靠来源的观点"
            ]
        }
        
        return criteria

    def _get_recency_requirements(self, research_intent: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """获取时效性要求"""
        time_range = constraints.get("time_range", "recent_3_years")
        research_type = research_intent["research_type"]
        domain = research_intent["domain_context"]["primary_domain"]
        
        # 快速发展的领域需要更新的资料
        fast_evolving_domains = ["deep_learning", "artificial_intelligence", "web_development"]
        
        if domain in fast_evolving_domains:
            preferred_range = "recent_2_years"
            acceptable_range = "recent_5_years"
        else:
            preferred_range = "recent_3_years" 
            acceptable_range = "recent_10_years"
        
        if research_type == "survey":
            # 综述需要涵盖更长时间范围
            acceptable_range = "all_time"
        
        return {
            "preferred": preferred_range,
            "acceptable": acceptable_range,
            "time_distribution": "70% recent, 30% classic papers" if research_type == "survey" else "90% recent"
        }

    def _plan_search_phases(self, research_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """制定搜索阶段计划"""
        research_type = research_intent["research_type"]
        
        base_phases = [
            {
                "phase": "初步搜索",
                "objective": "获取概览信息和主要资源",
                "activities": [
                    "使用主要关键词进行宽泛搜索",
                    "识别权威资源和综述论文",
                    "建立初步的知识框架"
                ],
                "expected_results": "20-30个高质量核心资源"
            },
            {
                "phase": "深度搜索", 
                "objective": "获取详细技术信息",
                "activities": [
                    "使用扩展关键词进行精确搜索",
                    "追踪引用和被引用文献",
                    "搜索特定技术实现细节"
                ],
                "expected_results": "50-80个详细资源"
            },
            {
                "phase": "补充搜索",
                "objective": "填补知识空白",
                "activities": [
                    "针对发现的空白进行targeted搜索",
                    "寻找实际应用案例和代码示例",
                    "获取最新发展动态"
                ],
                "expected_results": "20-30个补充资源"
            }
        ]
        
        # 根据研究类型调整
        if research_type == "comparative":
            base_phases.insert(1, {
                "phase": "对比方法搜索",
                "objective": "收集需要比较的不同方法",
                "activities": [
                    "识别主要的竞争方法/技术",
                    "为每种方法收集详细资料",
                    "寻找现有的比较研究"
                ],
                "expected_results": "每种方法10-15个资源"
            })
        
        return base_phases

    def _define_expected_outputs(self, research_intent: Dict[str, Any]) -> Dict[str, Any]:
        """定义预期输出规格"""
        research_type = research_intent["research_type"]
        complexity = research_intent.get("complexity_analysis", {}).get("level", "medium")
        
        base_outputs = {
            "resource_summary": {
                "total_sources": self._estimate_total_sources(complexity),
                "source_breakdown": {
                    "academic_papers": "40-50%",
                    "documentation": "20-30%", 
                    "tutorials_blogs": "20-30%",
                    "code_examples": "10-20%"
                }
            },
            "content_organization": {
                "categories": self._define_content_categories(research_intent),
                "format": "结构化摘要 + 原始链接 + 重要性评级"
            },
            "deliverables": [
                "资源清单(按重要性排序)",
                "关键概念提取",
                "技术路线图",
                "推荐学习路径"
            ]
        }
        
        # 根据研究类型定制输出
        type_specific_outputs = {
            "comparative": {
                "additional_deliverables": [
                    "各方法对比表",
                    "优缺点分析矩阵",
                    "应用场景推荐"
                ]
            },
            "survey": {
                "additional_deliverables": [
                    "发展时间线",
                    "技术分类体系",
                    "未来发展趋势分析"
                ]
            },
            "experimental": {
                "additional_deliverables": [
                    "实验设计参考",
                    "数据集和工具推荐",
                    "性能评估标准"
                ]
            }
        }
        
        if research_type in type_specific_outputs:
            base_outputs.update(type_specific_outputs[research_type])
        
        return base_outputs

    def _estimate_total_sources(self, complexity: str) -> str:
        """估计总资源数量"""
        estimates = {
            "low": "30-50个资源",
            "medium": "50-80个资源", 
            "high": "80-120个资源"
        }
        return estimates.get(complexity, "50-80个资源")

    def _define_content_categories(self, research_intent: Dict[str, Any]) -> List[str]:
        """定义内容分类"""
        base_categories = [
            "核心概念和原理",
            "技术实现方法",
            "应用案例和实践",
            "工具和框架",
            "相关资源和数据"
        ]
        
        research_type = research_intent["research_type"]
        
        if research_type == "comparative":
            base_categories.extend([
                "方法A详细信息",
                "方法B详细信息", 
                "对比分析结果"
            ])
        elif research_type == "survey":
            base_categories.extend([
                "历史发展脉络",
                "当前研究热点",
                "未来发展趋势"
            ])
        
        return base_categories

    def _determine_search_approach(self, research_type: str) -> str:
        """确定搜索方法"""
        approaches = {
            "experimental": "focused_technical_search",
            "comparative": "multi_perspective_search", 
            "survey": "comprehensive_systematic_search",
            "theoretical": "academic_literature_search",
            "applied": "practical_implementation_search"
        }
        return approaches.get(research_type, "general_systematic_search")

    def _define_search_success_metrics(self, research_intent: Dict[str, Any]) -> Dict[str, Any]:
        """定义搜索成功指标"""
        return {
            "coverage_metrics": [
                "核心概念覆盖完整性 (>90%)",
                "主要方法/技术覆盖度 (>80%)",
                "应用场景覆盖广度 (>70%)"
            ],
            "quality_metrics": [
                "高质量资源比例 (>60%)",
                "最新资源比例 (>50%)",
                "权威来源比例 (>40%)"
            ],
            "utility_metrics": [
                "可操作性资源比例 (>30%)",
                "代码示例覆盖度 (>20%)",
                "实际案例数量 (>10个)"
            ]
        }

    def _estimate_search_effort(self, research_intent: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """估算搜索工作量"""
        complexity = research_intent.get("complexity_analysis", {}).get("level", "medium")
        research_type = research_intent["research_type"]
        
        base_effort = {
            "low": {"time": "1-2天", "iterations": 2},
            "medium": {"time": "2-4天", "iterations": 3},
            "high": {"time": "3-7天", "iterations": 4}
        }
        
        effort = base_effort[complexity].copy()
        
        # 根据研究类型调整
        if research_type == "survey":
            effort["time"] = effort["time"].replace("天", "天 (综述类需要更多时间)")
            effort["iterations"] += 1
        elif research_type == "comparative":
            effort["parallel_searches"] = "需要并行搜索多个方法"
        
        effort["resource_processing_time"] = "搜索时间的50-70%用于筛选和整理"
        
        return effort