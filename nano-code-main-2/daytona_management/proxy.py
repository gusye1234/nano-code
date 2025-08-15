import sys
import signal
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
    
    def start_nano_code_unified(self, user_input: str):
        print(f"🚀 开始执行任务")
        
        session_id = "nano-code-unified-session"
        try:
            self.workspace_manager.create_session(session_id)
            
            self.workspace_manager.setup_secure_workspace(session_id)
            
            modified_input, uploaded_files = self.file_transfer.process_input_and_upload_files(user_input)
            if uploaded_files:
                print(f"📤 自动处理了 {len(uploaded_files)} 个文件")
            
            self.task_executor.execute_unified_task(session_id, modified_input)
            
            print("📦 收集输出文件...")

            input_filenames = [Path(f).name for f in uploaded_files] if uploaded_files else []
            self.file_transfer.collect_output_files(session_id, input_filenames)
            downloaded_files = self.file_transfer.download_results(session_id)
            
            # 检查是否生成了预期的分析报告
            report_found = any('architecture_analysis' in f or 'analysis' in f.lower() 
                             for f in downloaded_files) if downloaded_files else False

            if downloaded_files:
                print(f"🎉 任务完成！共生成 {len(downloaded_files)} 个文件")
                print("📁 结果文件已下载到: ~/Desktop/SandboxWork/download/")
                if report_found:
                    print("✅ 发现分析报告文件")
                else:
                    print("⚠️  未找到预期的分析报告文件")
            else:
                print("⚠️  任务完成，但未生成任何输出文件")
                print("💡 可能原因: AI未执行文件创建指令")
                
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