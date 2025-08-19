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
        
        return {
            "success": result.exit_code == 0,
            "output": result.output,
            "exit_code": result.exit_code,
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
