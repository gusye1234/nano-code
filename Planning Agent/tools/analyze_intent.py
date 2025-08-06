"""
研究意图分析工具
使用LLM深度分析用户的研究意图和需求
"""

import json
from typing import Dict, Any, List
from .base import AgentToolDefine, AgentToolReturn


class AnalyzeResearchIntentTool(AgentToolDefine):
    """分析用户研究意图的工具"""

    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="analyze_research_intent",
            description="""深度分析用户的研究意图，提取核心研究问题、目标、研究类型和领域背景。
这个工具会智能解析用户的研究主题，识别隐含假设，并确定合适的研究方法。""",
            parameters_schema={
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "用户输入的研究主题或问题"
                    },
                    "additional_context": {
                        "type": "string", 
                        "description": "额外的上下文信息，如文件内容、特殊要求等"
                    },
                    "user_preferences": {
                        "type": "object",
                        "description": "用户偏好设置",
                        "properties": {
                            "depth": {
                                "type": "string",
                                "enum": ["basic", "comprehensive", "expert"],
                                "description": "研究深度要求"
                            },
                            "timeline": {
                                "type": "string", 
                                "description": "期望完成时间"
                            },
                            "focus_areas": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "重点关注的方向"
                            }
                        }
                    }
                },
                "required": ["topic"]
            }
        )

    async def _execute(self, arguments: Dict[str, Any]) -> AgentToolReturn:
        """执行意图分析"""
        topic = arguments["topic"]
        additional_context = arguments.get("additional_context", "")
        user_preferences = arguments.get("user_preferences", {})
        
        # 在实际应用中，这里会调用LLM来分析
        # 现在先用模拟的智能分析逻辑
        analysis_result = await self._analyze_with_llm(topic, additional_context, user_preferences)
        
        return AgentToolReturn.success(self.name, analysis_result)

    async def _analyze_with_llm(self, topic: str, context: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """使用LLM进行智能意图分析（模拟实现）"""
        
        # 模拟LLM分析结果
        # 在实际实现中，这里会构造prompt并调用LLM
        
        # 1. 提取核心问题
        core_question = self._extract_core_question(topic)
        
        # 2. 识别研究类型  
        research_type = self._identify_research_type(topic)
        
        # 3. 确定研究目标
        objectives = self._determine_objectives(topic, preferences)
        
        # 4. 识别技术领域
        domain_context = self._identify_domain(topic)
        
        # 5. 分析复杂度
        complexity_analysis = self._analyze_complexity(topic)
        
        # 6. 识别潜在挑战
        challenges = self._identify_challenges(topic, research_type)
        
        return {
            "core_question": core_question,
            "research_type": research_type,
            "objectives": objectives,
            "domain_context": domain_context,
            "complexity_analysis": complexity_analysis,
            "potential_challenges": challenges,
            "recommended_approach": self._recommend_approach(research_type, complexity_analysis),
            "success_criteria": self._define_success_criteria(objectives)
        }

    def _extract_core_question(self, topic: str) -> str:
        """提取核心研究问题"""
        topic_lower = topic.lower()
        
        if any(word in topic_lower for word in ["如何", "怎么", "how"]):
            return f"How to implement or achieve: {topic}"
        elif any(word in topic_lower for word in ["什么", "what", "介绍"]):
            return f"What is: {topic}"
        elif any(word in topic_lower for word in ["为什么", "why", "原理"]):
            return f"Why and how does: {topic}"
        elif any(word in topic_lower for word in ["比较", "对比", "vs"]):
            return f"Comparative analysis of: {topic}"
        else:
            return f"Comprehensive research on: {topic}"

    def _identify_research_type(self, topic: str) -> str:
        """识别研究类型"""
        topic_lower = topic.lower()
        
        keywords_mapping = {
            "experimental": ["实验", "测试", "验证", "评估", "性能", "效果", "experiment", "test", "evaluate"],
            "comparative": ["比较", "对比", "vs", "versus", "哪个更好", "优缺点", "compare"],
            "survey": ["综述", "调研", "总结", "回顾", "survey", "review", "overview"],
            "theoretical": ["理论", "原理", "机制", "理论分析", "theory", "principle", "mechanism"],
            "applied": ["应用", "实现", "开发", "实际应用", "practical", "implementation", "application"],
            "exploratory": ["探索", "发现", "了解", "研究", "explore", "discover", "investigate"]
        }
        
        for research_type, keywords in keywords_mapping.items():
            if any(keyword in topic_lower for keyword in keywords):
                return research_type
        
        return "exploratory"  # 默认探索性研究

    def _determine_objectives(self, topic: str, preferences: Dict[str, Any]) -> List[str]:
        """确定研究目标"""
        objectives = []
        topic_lower = topic.lower()
        depth = preferences.get("depth", "comprehensive")
        
        # 基础目标
        if "应用" in topic_lower or "application" in topic_lower:
            objectives.extend([
                "理解技术的实际应用场景和价值",
                "掌握具体的实现方法和最佳实践",
                "分析应用中的关键技术挑战"
            ])
        elif "比较" in topic_lower or "compare" in topic_lower:
            objectives.extend([
                "全面比较不同方法的优缺点", 
                "分析各方法的适用场景",
                "提供选择建议和实施指导"
            ])
        else:
            objectives.extend([
                f"深入理解{topic}的核心概念和原理",
                f"掌握{topic}的关键技术和方法",
                f"分析{topic}的发展趋势和未来方向"
            ])
        
        # 根据深度要求调整
        if depth == "expert":
            objectives.extend([
                "深入分析技术细节和实现原理",
                "评估不同方案的性能和可扩展性", 
                "探索前沿发展和创新机会"
            ])
        elif depth == "comprehensive":
            objectives.append("提供系统性的知识框架和实践指导")
        
        return objectives

    def _identify_domain(self, topic: str) -> Dict[str, Any]:
        """识别技术领域"""
        topic_lower = topic.lower()
        
        domain_keywords = {
            "artificial_intelligence": ["ai", "人工智能", "机器学习", "深度学习", "神经网络"],
            "machine_learning": ["机器学习", "ml", "算法", "模型训练", "模型"],
            "deep_learning": ["深度学习", "dl", "神经网络", "cnn", "rnn", "transformer"],
            "natural_language_processing": ["nlp", "自然语言处理", "文本处理", "语言模型"],
            "computer_vision": ["计算机视觉", "cv", "图像处理", "图像识别", "视觉"],
            "data_science": ["数据科学", "数据分析", "大数据", "数据挖掘"],
            "software_engineering": ["软件工程", "软件开发", "系统设计", "架构设计"],
            "web_development": ["web开发", "前端", "后端", "网站开发", "web应用"],
            "mobile_development": ["移动开发", "app开发", "android", "ios", "移动应用"]
        }
        
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in topic_lower for keyword in keywords):
                detected_domains.append(domain)
        
        return {
            "primary_domain": detected_domains[0] if detected_domains else "general_technology",
            "secondary_domains": detected_domains[1:3],  # 最多3个相关领域
            "interdisciplinary": len(detected_domains) > 1,
            "technical_level": "intermediate"  # 可以基于更复杂的逻辑确定
        }

    def _analyze_complexity(self, topic: str) -> Dict[str, Any]:
        """分析研究复杂度"""
        topic_lower = topic.lower()
        
        high_complexity_indicators = [
            "分布式", "大规模", "高性能", "实时", "深度学习", "神经网络", 
            "系统架构", "复杂", "高级", "distributed", "large-scale", "real-time"
        ]
        
        medium_complexity_indicators = [
            "机器学习", "数据分析", "web开发", "应用开发", "算法", 
            "machine learning", "data analysis", "algorithm"
        ]
        
        low_complexity_indicators = [
            "基础", "入门", "简单", "介绍", "概述", "basic", "introduction", "simple"
        ]
        
        if any(indicator in topic_lower for indicator in high_complexity_indicators):
            complexity_level = "high"
            estimated_time = "4-8周"
            required_expertise = "expert"
        elif any(indicator in topic_lower for indicator in medium_complexity_indicators):
            complexity_level = "medium" 
            estimated_time = "2-4周"
            required_expertise = "intermediate"
        elif any(indicator in topic_lower for indicator in low_complexity_indicators):
            complexity_level = "low"
            estimated_time = "1-2周"
            required_expertise = "beginner"
        else:
            complexity_level = "medium"
            estimated_time = "2-3周"
            required_expertise = "intermediate"
        
        return {
            "level": complexity_level,
            "estimated_time": estimated_time,
            "required_expertise": required_expertise,
            "key_challenges": self._identify_technical_challenges(topic_lower, complexity_level)
        }

    def _identify_technical_challenges(self, topic_lower: str, complexity: str) -> List[str]:
        """识别技术挑战"""
        challenges = []
        
        if "深度学习" in topic_lower or "deep learning" in topic_lower:
            challenges.extend([
                "模型选择和架构设计",
                "数据预处理和特征工程", 
                "超参数调优和训练优化",
                "模型评估和性能分析"
            ])
        
        if "大规模" in topic_lower or "large-scale" in topic_lower:
            challenges.extend([
                "系统可扩展性设计",
                "性能优化和资源管理",
                "分布式架构复杂性"
            ])
        
        if complexity == "high":
            challenges.extend([
                "技术栈整合复杂性",
                "系统稳定性保证",
                "技术文档和知识获取难度"
            ])
        
        return challenges

    def _identify_challenges(self, topic: str, research_type: str) -> List[str]:
        """识别潜在研究挑战"""
        challenges = []
        
        if research_type == "experimental":
            challenges.extend([
                "实验环境搭建和配置",
                "基准数据集获取和处理",
                "实验结果的可靠性验证"
            ])
        elif research_type == "comparative":
            challenges.extend([
                "公平比较标准的建立",
                "多种方法的统一评估框架",
                "结果解释和建议提供"
            ])
        elif research_type == "survey":
            challenges.extend([
                "大量文献的筛选和整理",
                "知识体系的结构化组织",
                "前沿发展的跟踪和分析"
            ])
        
        # 通用挑战
        challenges.extend([
            "高质量资料和数据源获取",
            "技术深度与易理解性的平衡",
            "理论知识与实践应用的结合"
        ])
        
        return challenges

    def _recommend_approach(self, research_type: str, complexity_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """推荐研究方法"""
        approach_mapping = {
            "experimental": {
                "methodology": "controlled_experiments",
                "phases": ["literature_review", "experiment_design", "implementation", "evaluation", "analysis"],
                "key_activities": ["baseline_setup", "controlled_testing", "performance_analysis"]
            },
            "comparative": {
                "methodology": "comparative_analysis", 
                "phases": ["method_identification", "unified_evaluation", "comparison", "recommendation"],
                "key_activities": ["criteria_definition", "fair_comparison", "pros_cons_analysis"]
            },
            "survey": {
                "methodology": "systematic_review",
                "phases": ["literature_search", "screening", "analysis", "synthesis", "writing"],
                "key_activities": ["source_identification", "content_analysis", "knowledge_synthesis"]
            },
            "applied": {
                "methodology": "development_research",
                "phases": ["requirement_analysis", "design", "implementation", "testing", "deployment"],
                "key_activities": ["prototype_development", "user_testing", "iterative_improvement"]
            }
        }
        
        base_approach = approach_mapping.get(research_type, approach_mapping["survey"])
        
        # 根据复杂度调整
        if complexity_analysis["level"] == "high":
            base_approach["additional_considerations"] = [
                "分阶段实施策略",
                "专家咨询和指导",
                "风险评估和缓解"
            ]
        
        return base_approach

    def _define_success_criteria(self, objectives: List[str]) -> List[str]:
        """定义成功标准"""
        criteria = []
        
        # 基于目标生成标准
        for obj in objectives:
            if "理解" in obj:
                criteria.append("能够清晰解释核心概念和原理")
            elif "掌握" in obj:
                criteria.append("能够独立实现相关技术方案")
            elif "分析" in obj:
                criteria.append("能够深入分析技术特点和应用场景")
            elif "比较" in obj:
                criteria.append("能够客观比较不同方案的优缺点")
        
        # 通用成功标准
        criteria.extend([
            "提供清晰完整的知识体系",
            "包含可操作的实践指导",
            "具备实际应用价值"
        ])
        
        return list(set(criteria))  # 去重