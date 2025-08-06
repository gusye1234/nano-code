"""
实验实施规划工具
为Code Agent生成详细的实验实施任务规范
"""

import json
from typing import Dict, Any, List
from .base import AgentToolDefine, AgentToolReturn


class PlanImplementationTool(AgentToolDefine):
    """规划实验实施任务的工具"""

    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="plan_implementation", 
            description="""为Code Agent规划详细的实验实施任务。
基于研究意图和搜索结果，生成包含实验配置、基线方法、评估框架等的完整实施计划。""",
            parameters_schema={
                "type": "object",
                "properties": {
                    "research_intent": {
                        "type": "object",
                        "description": "研究意图分析结果",
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
                    "search_results": {
                        "type": "object",
                        "description": "文献搜索的结果摘要",
                        "properties": {
                            "key_technologies": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "available_datasets": {
                                "type": "array", 
                                "items": {"type": "string"}
                            },
                            "baseline_methods": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "evaluation_metrics": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    },
                    "implementation_constraints": {
                        "type": "object",
                        "description": "实施约束条件",
                        "properties": {
                            "available_resources": {
                                "type": "object",
                                "description": "可用资源（计算、时间、数据等）"
                            },
                            "technical_requirements": {
                                "type": "object",
                                "description": "技术要求和限制"
                            },
                            "deliverable_format": {
                                "type": "string",
                                "description": "交付格式要求"
                            }
                        }
                    }
                },
                "required": ["research_intent"]
            }
        )

    async def _execute(self, arguments: Dict[str, Any]) -> AgentToolReturn:
        """执行实施规划"""
        research_intent = arguments["research_intent"]
        search_results = arguments.get("search_results", {})
        constraints = arguments.get("implementation_constraints", {})
        
        # 生成实施计划
        implementation_plan = await self._generate_implementation_plan(
            research_intent, search_results, constraints
        )
        
        return AgentToolReturn.success(self.name, implementation_plan)

    async def _generate_implementation_plan(
        self, 
        research_intent: Dict[str, Any], 
        search_results: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成详细的实施计划"""
        
        research_type = research_intent["research_type"]
        domain_context = research_intent["domain_context"]
        
        # 1. 确定实施策略
        implementation_strategy = self._determine_implementation_strategy(research_type, domain_context)
        
        # 2. 规划实验配置
        experiment_config = self._plan_experiment_configuration(research_intent, search_results)
        
        # 3. 设计基线方法
        baseline_design = self._design_baseline_methods(research_intent, search_results)
        
        # 4. 构建评估框架
        evaluation_framework = self._build_evaluation_framework(research_intent, search_results)
        
        # 5. 规划实施阶段
        implementation_phases = self._plan_implementation_phases(research_type, experiment_config)
        
        # 6. 定义交付规格
        deliverable_specs = self._define_deliverable_specifications(research_intent, constraints)
        
        # 7. 技术栈推荐
        tech_stack = self._recommend_tech_stack(domain_context, experiment_config)
        
        return {
            "implementation_strategy": implementation_strategy,
            "experiment_configuration": experiment_config,
            "baseline_methods": baseline_design,
            "evaluation_framework": evaluation_framework,
            "implementation_phases": implementation_phases,
            "deliverable_specifications": deliverable_specs,
            "recommended_tech_stack": tech_stack,
            "resource_requirements": self._estimate_resource_requirements(experiment_config),
            "risk_mitigation": self._identify_implementation_risks(research_intent, experiment_config)
        }

    def _determine_implementation_strategy(self, research_type: str, domain_context: Dict[str, Any]) -> Dict[str, Any]:
        """确定实施策略"""
        
        strategies = {
            "experimental": {
                "approach": "controlled_experimentation",
                "focus": "验证性实验和性能比较",
                "key_principles": [
                    "控制变量确保公平比较",
                    "多次实验确保结果可靠性",
                    "统计显著性分析"
                ]
            },
            "comparative": {
                "approach": "multi_method_comparison",
                "focus": "多种方法的全面对比",
                "key_principles": [
                    "统一实验环境和数据集",
                    "相同评估指标和标准",
                    "客观公正的结果分析"
                ]
            },
            "survey": {
                "approach": "implementation_showcase",
                "focus": "关键技术的实现展示",
                "key_principles": [
                    "代表性方法的实现",
                    "清晰的代码结构和文档",
                    "易于理解和复现"
                ]
            },
            "applied": {
                "approach": "practical_development",
                "focus": "实际应用系统开发",
                "key_principles": [
                    "用户需求导向设计",
                    "系统稳定性和可扩展性",
                    "实际应用价值验证"
                ]
            },
            "theoretical": {
                "approach": "concept_demonstration",
                "focus": "理论概念的代码验证",
                "key_principles": [
                    "算法正确性验证",
                    "理论性能分析",
                    "概念可视化展示"
                ]
            }
        }
        
        base_strategy = strategies.get(research_type, strategies["experimental"])
        
        # 根据领域特点调整策略
        domain = domain_context.get("primary_domain", "")
        if domain == "deep_learning":
            base_strategy["domain_specific_considerations"] = [
                "模型训练时间管理",
                "GPU资源优化利用",
                "超参数调优策略"
            ]
        elif domain == "web_development":
            base_strategy["domain_specific_considerations"] = [
                "跨浏览器兼容性测试",
                "响应式设计验证",
                "性能优化实施"
            ]
        
        return base_strategy

    def _plan_experiment_configuration(self, research_intent: Dict[str, Any], search_results: Dict[str, Any]) -> Dict[str, Any]:
        """规划实验配置"""
        
        domain = research_intent["domain_context"]["primary_domain"]
        complexity = research_intent.get("complexity_analysis", {}).get("level", "medium")
        
        # 基础实验配置
        config = {
            "environment": self._determine_experiment_environment(domain),
            "data_requirements": self._specify_data_requirements(research_intent, search_results),
            "compute_requirements": self._estimate_compute_needs(domain, complexity),
            "reproducibility": self._ensure_reproducibility_config()
        }
        
        # 领域特定配置
        if domain == "machine_learning" or domain == "deep_learning":
            config.update({
                "model_configurations": self._plan_ml_model_configs(research_intent, search_results),
                "training_settings": self._plan_training_configurations(complexity),
                "validation_strategy": self._design_validation_strategy()
            })
        elif domain == "web_development":
            config.update({
                "browser_testing": self._plan_browser_testing(),
                "performance_testing": self._plan_performance_testing(),
                "accessibility_testing": self._plan_accessibility_testing()
            })
        elif domain == "software_engineering":
            config.update({
                "architecture_design": self._plan_architecture_design(research_intent),
                "testing_strategy": self._plan_comprehensive_testing(),
                "deployment_config": self._plan_deployment_configuration()
            })
        
        return config

    def _determine_experiment_environment(self, domain: str) -> Dict[str, Any]:
        """确定实验环境"""
        
        environments = {
            "machine_learning": {
                "primary": "Python + Jupyter",
                "libraries": ["scikit-learn", "pandas", "numpy", "matplotlib"],
                "compute": "CPU sufficient, GPU recommended for large datasets"
            },
            "deep_learning": {
                "primary": "Python + PyTorch/TensorFlow",
                "libraries": ["pytorch/tensorflow", "transformers", "datasets", "wandb"],
                "compute": "GPU required, multi-GPU for large models"
            },
            "web_development": {
                "primary": "Node.js/React or Python/Django",
                "libraries": ["framework-specific", "testing-tools", "build-tools"],
                "compute": "Standard development environment"
            },
            "data_science": {
                "primary": "Python/R + Jupyter",
                "libraries": ["pandas", "numpy", "scipy", "seaborn"],
                "compute": "CPU sufficient, large memory for big data"
            }
        }
        
        return environments.get(domain, environments["machine_learning"])

    def _specify_data_requirements(self, research_intent: Dict[str, Any], search_results: Dict[str, Any]) -> Dict[str, Any]:
        """指定数据需求"""
        
        available_datasets = search_results.get("available_datasets", [])
        domain = research_intent["domain_context"]["primary_domain"]
        research_type = research_intent["research_type"]
        
        requirements = {
            "dataset_sources": available_datasets if available_datasets else self._suggest_default_datasets(domain),
            "data_preprocessing": self._plan_data_preprocessing(domain),
            "data_splits": self._plan_data_splits(research_type),
            "data_quality": self._specify_data_quality_requirements()
        }
        
        return requirements

    def _suggest_default_datasets(self, domain: str) -> List[str]:
        """推荐默认数据集"""
        
        dataset_suggestions = {
            "machine_learning": [
                "iris (分类入门)", 
                "boston housing (回归)",
                "titanic (特征工程)",
                "wine quality (多类分类)"
            ],
            "deep_learning": [
                "MNIST (手写数字)",
                "CIFAR-10 (图像分类)",
                "IMDB (情感分析)",
                "Penn Treebank (语言建模)"
            ],
            "natural_language_processing": [
                "GLUE benchmarks",
                "SQuAD (阅读理解)",
                "CoNLL-2003 (命名实体识别)",
                "WMT (机器翻译)"
            ],
            "computer_vision": [
                "ImageNet (图像分类)",
                "COCO (目标检测)",
                "CelebA (人脸属性)",
                "Places365 (场景识别)"
            ]
        }
        
        return dataset_suggestions.get(domain, ["custom dataset"])

    def _design_baseline_methods(self, research_intent: Dict[str, Any], search_results: Dict[str, Any]) -> Dict[str, Any]:
        """设计基线方法"""
        
        research_type = research_intent["research_type"]
        domain = research_intent["domain_context"]["primary_domain"] 
        available_baselines = search_results.get("baseline_methods", [])
        
        baseline_design = {
            "selection_criteria": self._define_baseline_selection_criteria(research_type),
            "recommended_baselines": available_baselines if available_baselines else self._suggest_default_baselines(domain),
            "implementation_priority": self._prioritize_baseline_implementation(research_type),
            "comparison_framework": self._design_comparison_framework()
        }
        
        return baseline_design

    def _define_baseline_selection_criteria(self, research_type: str) -> List[str]:
        """定义基线选择标准"""
        
        criteria_by_type = {
            "experimental": [
                "经典方法作为底线基准",
                "当前最优方法作为对比目标",
                "简单方法验证实验有效性"
            ],
            "comparative": [
                "覆盖主要技术路线",
                "包含新旧方法对比",
                "选择代表性实现"
            ],
            "survey": [
                "历史重要方法", 
                "当前主流方法",
                "新兴前沿方法"
            ],
            "applied": [
                "实际应用中常用方法",
                "性能可接受的轻量方法",
                "易于部署和维护的方法"
            ]
        }
        
        return criteria_by_type.get(research_type, criteria_by_type["experimental"])

    def _suggest_default_baselines(self, domain: str) -> List[Dict[str, Any]]:
        """推荐默认基线方法"""
        
        baselines = {
            "machine_learning": [
                {
                    "name": "Linear Regression/Logistic Regression",
                    "complexity": "low",
                    "implementation_effort": "minimal",
                    "use_case": "简单基准"
                },
                {
                    "name": "Random Forest",
                    "complexity": "medium", 
                    "implementation_effort": "low",
                    "use_case": "强基准"
                },
                {
                    "name": "SVM",
                    "complexity": "medium",
                    "implementation_effort": "low", 
                    "use_case": "经典方法"
                }
            ],
            "deep_learning": [
                {
                    "name": "Multi-Layer Perceptron",
                    "complexity": "low",
                    "implementation_effort": "low",
                    "use_case": "神经网络基准"
                },
                {
                    "name": "CNN (ResNet)",
                    "complexity": "medium",
                    "implementation_effort": "medium",
                    "use_case": "视觉任务标准"
                },
                {
                    "name": "Transformer",
                    "complexity": "high",
                    "implementation_effort": "medium",
                    "use_case": "当前最优"
                }
            ]
        }
        
        return baselines.get(domain, baselines["machine_learning"])

    def _build_evaluation_framework(self, research_intent: Dict[str, Any], search_results: Dict[str, Any]) -> Dict[str, Any]:
        """构建评估框架"""
        
        domain = research_intent["domain_context"]["primary_domain"]
        research_type = research_intent["research_type"]
        available_metrics = search_results.get("evaluation_metrics", [])
        
        framework = {
            "evaluation_metrics": available_metrics if available_metrics else self._suggest_default_metrics(domain),
            "evaluation_protocol": self._design_evaluation_protocol(research_type),
            "statistical_analysis": self._plan_statistical_analysis(research_type),
            "visualization": self._plan_result_visualization(domain),
            "reporting": self._plan_result_reporting(research_intent)
        }
        
        return framework

    def _suggest_default_metrics(self, domain: str) -> List[Dict[str, Any]]:
        """推荐默认评估指标"""
        
        metrics = {
            "machine_learning": [
                {"name": "Accuracy", "type": "classification", "priority": "high"},
                {"name": "Precision/Recall/F1", "type": "classification", "priority": "high"},
                {"name": "RMSE", "type": "regression", "priority": "high"},
                {"name": "ROC-AUC", "type": "classification", "priority": "medium"}
            ],
            "deep_learning": [
                {"name": "Loss Function Value", "type": "training", "priority": "high"},
                {"name": "Task-specific Accuracy", "type": "performance", "priority": "high"},
                {"name": "Training Time", "type": "efficiency", "priority": "medium"},
                {"name": "Model Size", "type": "efficiency", "priority": "medium"}
            ],
            "web_development": [
                {"name": "Page Load Time", "type": "performance", "priority": "high"},
                {"name": "Time to Interactive", "type": "performance", "priority": "high"},
                {"name": "Lighthouse Score", "type": "quality", "priority": "medium"},
                {"name": "Bundle Size", "type": "efficiency", "priority": "medium"}
            ]
        }
        
        return metrics.get(domain, metrics["machine_learning"])

    def _plan_implementation_phases(self, research_type: str, experiment_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """规划实施阶段"""
        
        base_phases = [
            {
                "phase": "环境准备",
                "objectives": [
                    "搭建开发和实验环境",
                    "准备数据集和依赖库",
                    "建立版本控制和文档框架"
                ],
                "deliverables": [
                    "可运行的开发环境",
                    "数据预处理管道",
                    "项目结构和README"
                ],
                "estimated_time": "1-2天"
            },
            {
                "phase": "基线实现",
                "objectives": [
                    "实现选定的基线方法",
                    "建立评估流程",
                    "验证实现正确性"
                ],
                "deliverables": [
                    "基线方法代码",
                    "评估脚本",
                    "初步结果报告"
                ],
                "estimated_time": "2-4天"
            },
            {
                "phase": "核心实验",
                "objectives": [
                    "实现主要实验方法",
                    "进行系统性实验",
                    "收集和分析结果"
                ],
                "deliverables": [
                    "完整实验代码",
                    "详细实验结果",
                    "性能分析报告"
                ],
                "estimated_time": "3-7天"
            },
            {
                "phase": "结果整理",
                "objectives": [
                    "生成可视化结果",
                    "撰写技术报告",
                    "准备展示材料"
                ],
                "deliverables": [
                    "结果图表和分析",
                    "完整技术文档",
                    "可复现的代码包"
                ],
                "estimated_time": "2-3天"
            }
        ]
        
        # 根据研究类型调整阶段
        if research_type == "comparative":
            base_phases.insert(2, {
                "phase": "多方法对比",
                "objectives": [
                    "并行实现多种方法",
                    "统一对比实验",
                    "深度结果分析"
                ],
                "deliverables": [
                    "所有方法的实现",
                    "对比实验结果",
                    "方法优劣分析"
                ],
                "estimated_time": "4-8天"
            })
        
        return base_phases

    def _define_deliverable_specifications(self, research_intent: Dict[str, Any], constraints: Dict[str, Any]) -> Dict[str, Any]:
        """定义交付规格"""
        
        deliverable_format = constraints.get("deliverable_format", "jupyter_notebook")
        research_type = research_intent["research_type"]
        
        specs = {
            "primary_deliverable": self._specify_primary_deliverable(deliverable_format, research_type),
            "code_organization": self._specify_code_organization(),
            "documentation": self._specify_documentation_requirements(),
            "reproducibility": self._specify_reproducibility_requirements(),
            "presentation": self._specify_presentation_requirements(research_type)
        }
        
        return specs

    def _specify_primary_deliverable(self, format_type: str, research_type: str) -> Dict[str, Any]:
        """指定主要交付物"""
        
        deliverables = {
            "jupyter_notebook": {
                "format": "Jupyter Notebook (.ipynb)",
                "structure": [
                    "研究背景和目标",
                    "数据探索和预处理",
                    "方法实现和实验",
                    "结果分析和可视化",
                    "结论和未来工作"
                ],
                "requirements": [
                    "代码清晰可读",
                    "Markdown文档详细",
                    "图表美观专业"
                ]
            },
            "python_package": {
                "format": "Python Package",
                "structure": [
                    "核心算法模块",
                    "数据处理模块",
                    "评估和可视化模块",
                    "命令行接口",
                    "完整测试套件"
                ],
                "requirements": [
                    "模块化设计",
                    "完整API文档",
                    "单元测试覆盖"
                ]
            }
        }
        
        base_deliverable = deliverables.get(format_type, deliverables["jupyter_notebook"])
        
        # 根据研究类型调整
        if research_type == "comparative":
            base_deliverable["additional_requirements"] = [
                "方法对比总结表",
                "性能对比图表",
                "选择建议指南"
            ]
        
        return base_deliverable

    def _recommend_tech_stack(self, domain_context: Dict[str, Any], experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """推荐技术栈"""
        
        domain = domain_context.get("primary_domain", "")
        
        tech_stacks = {
            "machine_learning": {
                "core_language": "Python",
                "primary_libraries": [
                    "scikit-learn (经典ML)",
                    "pandas (数据处理)",
                    "numpy (数值计算)",
                    "matplotlib/seaborn (可视化)"
                ],
                "development_tools": [
                    "Jupyter Notebook",
                    "VS Code",
                    "Git"
                ],
                "optional_tools": [
                    "MLflow (实验跟踪)",
                    "optuna (超参优化)"
                ]
            },
            "deep_learning": {
                "core_language": "Python",
                "primary_libraries": [
                    "PyTorch/TensorFlow (深度学习)",
                    "transformers (预训练模型)",
                    "datasets (数据加载)",
                    "wandb (实验跟踪)"
                ],
                "development_tools": [
                    "Jupyter Notebook",
                    "Google Colab (GPU)",
                    "Docker (环境)"
                ],
                "optional_tools": [
                    "Ray Tune (分布式训练)",
                    "TensorBoard (可视化)"
                ]
            }
        }
        
        return tech_stacks.get(domain, tech_stacks["machine_learning"])

    def _estimate_resource_requirements(self, experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """估算资源需求"""
        
        compute_req = experiment_config.get("compute_requirements", {})
        
        return {
            "compute_resources": {
                "cpu": "4-8 cores recommended",
                "memory": "8-16 GB RAM",
                "storage": "20-50 GB for datasets and results",
                "gpu": compute_req.get("compute", "").get("GPU", "Optional but recommended")
            },
            "time_estimation": {
                "development": "1-2 weeks",
                "experimentation": "3-7 days",
                "analysis_reporting": "2-3 days"
            },
            "skill_requirements": [
                "Python编程 (中级)",
                "机器学习基础 (中级)",
                "数据分析能力 (中级)",
                "实验设计思维 (初级)"
            ]
        }

    def _identify_implementation_risks(self, research_intent: Dict[str, Any], experiment_config: Dict[str, Any]) -> Dict[str, Any]:
        """识别实施风险"""
        
        complexity = research_intent.get("complexity_analysis", {}).get("level", "medium")
        domain = research_intent["domain_context"]["primary_domain"]
        
        risks = {
            "technical_risks": [
                {
                    "risk": "环境配置困难",
                    "probability": "medium",
                    "impact": "high",
                    "mitigation": "使用Docker或云平台"
                },
                {
                    "risk": "数据质量问题",
                    "probability": "medium",
                    "impact": "medium", 
                    "mitigation": "充分的数据探索和预处理"
                }
            ],
            "resource_risks": [
                {
                    "risk": "计算资源不足",
                    "probability": "low" if complexity == "low" else "medium",
                    "impact": "high",
                    "mitigation": "使用云GPU或简化实验规模"
                }
            ],
            "timeline_risks": [
                {
                    "risk": "实现复杂度超出预期",
                    "probability": "medium",
                    "impact": "medium",
                    "mitigation": "分阶段实施，优先核心功能"
                }
            ]
        }
        
        # 领域特定风险
        if domain == "deep_learning":
            risks["technical_risks"].append({
                "risk": "模型训练不收敛",
                "probability": "medium",
                "impact": "high", 
                "mitigation": "仔细调试超参数，使用预训练模型"
            })
        
        return risks

    # 辅助方法实现
    def _plan_data_preprocessing(self, domain: str) -> List[str]:
        return [
            "数据清洗和缺失值处理",
            "特征工程和标准化",
            "数据分割 (训练/验证/测试)",
            "数据可视化和探索性分析"
        ]

    def _plan_data_splits(self, research_type: str) -> Dict[str, Any]:
        if research_type == "experimental":
            return {
                "train": "70%",
                "validation": "15%", 
                "test": "15%",
                "strategy": "stratified_split"
            }
        return {
            "train": "80%",
            "test": "20%",
            "strategy": "random_split"
        }

    def _specify_data_quality_requirements(self) -> List[str]:
        return [
            "数据完整性检查",
            "异常值检测和处理",
            "数据分布分析",
            "标签质量验证"
        ]

    def _plan_ml_model_configs(self, research_intent: Dict[str, Any], search_results: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "model_selection": "基于搜索结果的主流模型",
            "hyperparameter_ranges": "合理的参数搜索空间",
            "cross_validation": "k-fold交叉验证"
        }

    def _plan_training_configurations(self, complexity: str) -> Dict[str, Any]:
        configs = {
            "low": {"epochs": 10, "batch_size": 32},
            "medium": {"epochs": 50, "batch_size": 64},
            "high": {"epochs": 100, "batch_size": 128}
        }
        return configs.get(complexity, configs["medium"])

    def _design_validation_strategy(self) -> Dict[str, Any]:
        return {
            "primary": "hold_out_validation",
            "secondary": "cross_validation",
            "metrics": "task_specific_metrics"
        }

    def _ensure_reproducibility_config(self) -> Dict[str, Any]:
        return {
            "seed_setting": "固定随机种子",
            "version_control": "记录所有依赖版本",
            "environment": "使用requirements.txt或environment.yml"
        }

    def _prioritize_baseline_implementation(self, research_type: str) -> List[str]:
        if research_type == "comparative":
            return ["所有基线同等重要", "并行开发", "统一评估"]
        return ["简单基线优先", "经典方法次之", "最优方法最后"]

    def _design_comparison_framework(self) -> Dict[str, Any]:
        return {
            "comparison_aspects": ["性能", "效率", "复杂度", "可解释性"],
            "statistical_tests": "显著性检验",
            "visualization": "对比图表"
        }

    def _design_evaluation_protocol(self, research_type: str) -> Dict[str, Any]:
        protocols = {
            "experimental": "严格的实验设计和重复验证",
            "comparative": "公平对比和统计检验",
            "survey": "全面展示和分析"
        }
        return {"protocol": protocols.get(research_type, protocols["experimental"])}

    def _plan_statistical_analysis(self, research_type: str) -> List[str]:
        if research_type == "comparative":
            return ["配对t检验", "方差分析", "效应大小分析"]
        return ["描述性统计", "置信区间", "显著性检验"]

    def _plan_result_visualization(self, domain: str) -> List[str]:
        return [
            "性能对比图表",
            "训练曲线可视化", 
            "混淆矩阵或误差分析",
            "特征重要性分析"
        ]

    def _plan_result_reporting(self, research_intent: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "report_structure": [
                "实验设置",
                "主要结果",
                "详细分析", 
                "结论建议"
            ],
            "formatting": "专业图表和表格"
        }

    def _specify_code_organization(self) -> Dict[str, Any]:
        return {
            "structure": [
                "data/ (数据文件)",
                "src/ (源代码)",
                "notebooks/ (实验笔记)",
                "results/ (结果文件)",
                "docs/ (文档)"
            ],
            "coding_standards": "PEP 8, 代码注释, 函数文档"
        }

    def _specify_documentation_requirements(self) -> List[str]:
        return [
            "完整的README文件",
            "API文档和使用示例",
            "实验结果说明",
            "复现步骤指南"
        ]

    def _specify_reproducibility_requirements(self) -> List[str]:
        return [
            "固定随机种子",
            "依赖版本锁定",
            "详细环境配置",
            "一键运行脚本"
        ]

    def _specify_presentation_requirements(self, research_type: str) -> Dict[str, Any]:
        return {
            "format": "技术报告 + 代码演示",
            "key_elements": [
                "问题定义和方法",
                "实验设置和结果",
                "深度分析和洞察",
                "代码质量和可复现性"
            ]
        }