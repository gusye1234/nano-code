from daytona_sdk.common.process import SessionExecuteRequest
from .config import LLMConfig, PathConfig


class TaskExecutor:
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
        self.llm_config = LLMConfig()
    
    def execute_unified_task(self, session_id: str, user_input: str) -> dict:
        print(f"🚀 开始执行统一任务")
        print(f"📝 用户输入: {user_input}")
        
        unified_cmd = self._build_unified_command(user_input)
        
        # 执行任务
        result = self._execute_command(session_id, unified_cmd)
        
        # # 读取调用工具创建的文件列表
        # created_files = self._read_created_files_log(session_id)
        
        return {
            "success": result.exit_code == 0,
            "output": result.output,
            "exit_code": result.exit_code,
            # "created_files": created_files  # 已禁用基于日志的文件追踪
        }
    
    def _build_unified_command(self, user_input: str) -> str:
        return (
            f'cd {PathConfig.TMP_DIR} && '
            f'OPENAI_API_KEY="{self.llm_config.api_key}" '
            f'LLM_BASE_URL="{self.llm_config.base_url}" '
            f'PYTHONPATH="{PathConfig.SYSTEM_DIR}:$PYTHONPATH" '
            f'python -m nanocode1 --user-input "{user_input}" --working-dir {PathConfig.TMP_DIR}'
        )
    
    def _execute_command(self, session_id: str, command: str):
        print(f"🔧 执行命令: {command}")
        
        req = SessionExecuteRequest(command=command)
        result = self.sandbox.process.execute_session_command(session_id, req)
        
        print("📊 任务执行结果:")
        if result.output:
            print(result.output)
        else:
            print("无输出内容")
        
        if result.exit_code != 0:
            print(f"⚠️  任务执行失败，退出码: {result.exit_code}")
        else:
            print("✅ 任务执行成功")
        
        return result
    
    # def _read_created_files_log(self, session_id: str) -> list:
    #     # # 读取调用工具创建的文件列表
    #     created_files_log = f"{PathConfig.TMP_DIR}/created_files.log"
    #     
    #     try:
    #         # 检查日志文件是否存在
    #         check_cmd = f"test -f '{created_files_log}' && cat '{created_files_log}' || echo ''"
    #         req = SessionExecuteRequest(command=check_cmd)
    #         result = self.sandbox.process.execute_session_command(session_id, req)
    #         
    #         if result.output.strip():
    #             created_files = [line.strip() for line in result.output.strip().split('\n') if line.strip()]
    #             print(f"📋 读取到 {len(created_files)} 个AI创建的文件")
    #             return created_files
    #         else:
    #             print("📋 未发现AI创建文件日志")
    #             return []
    #             
    #     except Exception as e:
    #         print(f"⚠️  读取创建文件日志失败: {e}")
    #         return []