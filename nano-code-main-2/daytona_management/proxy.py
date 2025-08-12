import sys
import signal
from pathlib import Path
from .config import DaytonaConfig
from .sandbox_manager import SandboxManager
from .workspace_manager import WorkspaceManager
from .file_transfer import FileTransfer
from .task_executor import TaskExecutor


class NanoCodeProxy:
    """nano-code代理主控制器 (统一接口)"""
    
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
        """创建并设置Daytona沙盒"""
        print("📦 创建Daytona沙盒...")
        
        # 创建沙盒管理器并初始化沙盒
        self.sandbox_manager = SandboxManager(self.config)
        self.sandbox = self.sandbox_manager.create_sandbox()
        
        # 设置环境
        self.sandbox_manager.setup_environment()
        
        # 初始化其他管理器
        self.workspace_manager = WorkspaceManager(self.sandbox)
        self.file_transfer = FileTransfer(self.sandbox)
        self.task_executor = TaskExecutor(self.sandbox)
        
        print(f"✅ 沙盒创建成功: {self.sandbox.id}")
    
    def start_nano_code_unified(self, user_input: str):
        """统一任务执行 - Agent自动分析用户输入"""
        print(f"🚀 开始执行任务")
        print(f"🧠 Agent将自动分析用户输入并选择合适的工具")
        
        session_id = "nano-code-unified-session"
        try:
            # 创建工作会话
            self.workspace_manager.create_session(session_id)
            
            # 设置工作区
            self.workspace_manager.setup_secure_workspace(session_id)
            
            # 统一执行 - 让Agent自己分析用户输入
            result = self.task_executor.execute_unified_task(session_id, user_input)
            
            # 收集并下载结果
            self.file_transfer.collect_output_files(session_id, input_filenames=[])
            downloaded_files = self.file_transfer.download_results(session_id)
            
            # 显示结果
            if downloaded_files:
                print(f"🎉 任务完成！共生成 {len(downloaded_files)} 个文件")
                print("📁 结果文件已下载到: ~/Desktop/SandboxWork/download/")
            else:
                print("🎉 任务完成！")
                
        except Exception as e:
            print(f"❌ 任务执行失败: {e}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
        finally:
            self.workspace_manager.delete_session(session_id)
    
    def _cleanup_and_exit(self, signum, _):
        """清理资源并退出"""
        print(f"\n接收到信号 {signum}，清理资源...")
        
        if self.sandbox_manager:
            self.sandbox_manager.destroy_sandbox()
        
        sys.exit(0)