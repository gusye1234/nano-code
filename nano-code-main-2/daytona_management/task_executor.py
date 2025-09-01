from daytona_sdk.common.process import SessionExecuteRequest
from .config import LLMConfig, PathConfig


class TaskExecutor:
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
        self.llm_config = LLMConfig()
    
    def execute_json_task(self, session_id: str, json_remote_path: str) -> dict:
        """
        执行JSON任务文件
        Args:
            session_id (str): 会话ID
            json_remote_path (str): JSON文件的远程路径
        Returns:
            dict: 执行结果，包含成功标志、输出和退出码
        """
        print(f"📝 JSON文件路径: {json_remote_path}")
        
        json_cmd = self._build_json_command(json_remote_path)
        
        # 执行任务
        result = self._execute_command(session_id, json_cmd)
        
        return {
            "success": result.exit_code == 0,
            "output": result.output,
            "exit_code": result.exit_code,
        }
    
    
    def _build_json_command(self, json_remote_path: str) -> str:
        """构建JSON任务执行命令"""
        return (
            f'cd {PathConfig.TMP_DIR} && '
            f'OPENAI_API_KEY="{self.llm_config.api_key}" '
            f'LLM_BASE_URL="{self.llm_config.base_url}" '
            f'PYTHONPATH="{PathConfig.SYSTEM_DIR}:$PYTHONPATH" '
            f'python -m nanocode1 "{json_remote_path}" --working-dir {PathConfig.TMP_DIR}'
        )
    
    def _execute_command(self, session_id: str, command: str):
        """执行命令"""
        
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
