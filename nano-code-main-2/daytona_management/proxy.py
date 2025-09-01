import sys
import signal
import json
from pathlib import Path
from .config import DaytonaConfig
from .sandbox_manager import SandboxManager
from .workspace_manager import WorkspaceManager
from .file_transfer import FileTransfer
from .task_executor import TaskExecutor


class NanoCodeProxy:

    def __init__(self):
        self.config = DaytonaConfig()
        self.sandbox_manager = None
        self.workspace_manager = None
        self.file_transfer = None
        self.task_executor = None
        self.sandbox = None
        self.running = True
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._cleanup_and_exit)
        signal.signal(signal.SIGTERM, self._cleanup_and_exit)
    
    def setup_daytona(self):
        print("📦 创建Daytona沙盒...")
        
        self.sandbox_manager = SandboxManager(self.config)
        self.sandbox = self.sandbox_manager.create_sandbox()
        
        # 设置环境
        self.sandbox_manager.setup_environment()
        self.workspace_manager = WorkspaceManager(self.sandbox)
        self.file_transfer = FileTransfer(self.sandbox)
        self.task_executor = TaskExecutor(self.sandbox)
    
    def _infer_stage_from_plan(self, json_file_path: str) -> str:
        """
        阶段推断（忽略 is_first_time），按以下优先级：
        1) experimental_requirements.code_repository_review 存在 -> CodeRepositoryReview
        2) experimental_requirements.reproduction_tasks 非空数组 -> ReproductionTask
        3) experimental_requirements.critical_evaluation 存在 -> CriticalEvaluation
        4) 默认 -> CodeRepositoryReview
        """
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                plan_data = json.load(f)

            exp_req = plan_data.get('experimental_requirements', {}) or {}

            # 1) 优先：如果包含代码仓库分析配置
            if exp_req.get('code_repository_review'):
                return "CodeRepositoryReview"

            # 2) 其次：若存在复现实验任务
            rt = exp_req.get('reproduction_tasks')
            if isinstance(rt, list) and len(rt) > 0:
                return "ReproductionTask"

            # 3) 再次：若存在批判性评估内容
            if exp_req.get('critical_evaluation'):
                return "CriticalEvaluation"

            # 4) 默认回退
            return "CodeRepositoryReview"

        except Exception as e:
            print(f"⚠️  解析JSON失败，默认阶段: {e}")
            return "CodeRepositoryReview"
    
    def start_nano_code_json(self, json_file_path: str):
        """执行JSON任务文件"""
        print(f"🚀 开始执行JSON任务")
        
        # 从JSON文件推断阶段名作为会话基础名称
        base_stage = self._infer_stage_from_plan(json_file_path)
        print(f"🎯 推断任务阶段: {base_stage}")
        
        try:
            # 使用幂等创建会话，自动处理重名冲突
            session_id = self.workspace_manager.ensure_session(base_stage)
            print(f"📋 使用会话: {session_id}")
            
            self.workspace_manager.setup_secure_workspace(session_id)
            
            # 上传JSON文件
            json_remote_path = self.file_transfer.process_json_file_and_upload(json_file_path)
            
            # 执行任务
            self.task_executor.execute_json_task(session_id, json_remote_path)
            
            print("📦 收集输出文件...")

            # JSON文件名用于排除，使用复制模式保留原文件
            json_filename = Path(json_file_path).name
            self.file_transfer.collect_output_files(session_id, [json_filename], copy=True)
            downloaded_files = self.file_transfer.download_results(session_id)
            
            # 检查是否生成了预期的分析报告
            report_found = any('architecture_analysis' in f or 'analysis' in f.lower() or 'agent_output' in f.lower()
                             for f in downloaded_files) if downloaded_files else False

            if downloaded_files:
                print(f"🎉 任务完成！共生成 {len(downloaded_files)} 个文件")
                print("📁 结果文件已下载到: ~/Desktop/SandboxWork/download/")
                if report_found:
                    print("✅ 发现输出报告文件")
                else:
                    print("⚠️  未找到预期的输出报告文件")
            else:
                print("⚠️  任务完成，但未生成任何输出文件")
                print("💡 可能原因: AI未执行文件创建指令")
                
        except Exception as e:
            print(f"❌ 任务执行失败: {e}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
        #finally:
            #self.workspace_manager.delete_session(session_id)
    
    def _cleanup_and_exit(self, signum, _):
        """清理资源并退出"""
        print(f"\n接收到信号 {signum}，清理资源...")
        
        if self.sandbox_manager:
            self.sandbox_manager.destroy_sandbox()
        
        sys.exit(0)