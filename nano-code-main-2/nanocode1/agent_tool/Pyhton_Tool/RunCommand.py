import os
from ...constants import MAX_FOR_LLM_TOOL_RETURN_TOKENS
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session
from .python_executor import PythonExecutor


class RunCommandTool(AgentToolDefine):
    """
    Python代码执行工具
    
    功能：执行Python代码字符串或文件，在Daytona隔离环境中直接使用系统Python
    提供详细的执行结果和错误分析
    """
    
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="run_command",
            description="""Execute Python code. Simple tool for running Python scripts and code.

Examples:
- {"code": "print('hello world')"}
- {"file": "script.py"}
- {"code": "import os; print(os.getcwd())"}
""",
            parameters_schema={
                "properties": {
                    "code": {
                        "description": "Python code to execute (use this OR file, not both)",
                        "type": "string",
                    },
                    "file": {
                        "description": "Python file to run (use this OR code, not both)",
                        "type": "string",
                    },
                },
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        code = arguments.get("code")
        file_path = arguments.get("file") 
        
        # 参数验证
        if not code and not file_path:
            return AgentToolReturn.error(self.name, "Either 'code' or 'file' required")
        
        if code and file_path:
            return AgentToolReturn.error(self.name, "Cannot specify both 'code' and 'file'")
        
        try:
            if code:
                # 执行代码字符串
                result = await PythonExecutor.run_code(code, session.working_dir)
                return self._format_result("code execution", result, code, session.working_dir)
            else:
                # 执行Python文件
                result, file_code = await self._execute_file(file_path, session)
                return self._format_result(file_path, result, file_code, session.working_dir)
                
        except Exception as e:
            return AgentToolReturn.error(self.name, f"Execution failed: {str(e)}")
    
    async def _execute_file(self, file_path: str, session: Session) -> tuple:
        """执行Python文件并读取文件内容用于调试"""
        # 检查文件是否存在
        full_path = os.path.join(session.working_dir, file_path)
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File '{file_path}' not found")
        
        # 读取文件内容用于调试分析
        file_code = None
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                file_code = f.read()
        except Exception:
            pass  # 文件读取失败不影响执行
        
        # 执行文件
        result = await PythonExecutor.run_file(file_path, session.working_dir)
        return result, file_code
    
    def _format_result(self, source: str, result: dict, code: str = None, working_dir: str = None) -> AgentToolReturn:
        """格式化执行结果，提供详细的输出和错误分析"""
        stdout = result.get('stdout', '').strip()
        stderr = result.get('stderr', '').strip()
        returncode = result.get('returncode', -1)
        
        # 组合输出内容
        output_parts = []
        if stdout:
            output_parts.append(stdout)
        if stderr:
            output_parts.append(f"Error: {stderr}")
        
        output = "\n".join(output_parts) if output_parts else "(no output)"
        
        # 截断过长的输出
        if len(output) > MAX_FOR_LLM_TOOL_RETURN_TOKENS:
            output = output[:MAX_FOR_LLM_TOOL_RETURN_TOKENS] + "...[truncated]"
        
        status = "SUCCESS" if returncode == 0 else "ERROR"
        env_info = f"Environment: Daytona container at {working_dir}" if working_dir else ""
        
        # 构建LLM内容
        llm_content = f"Python {source} executed.{(' ' + env_info) if env_info else ''}\nReturn code: {returncode}\nOutput:\n{output}"
        
        # 如果执行失败且有代码，提供调试分析
        if returncode != 0 and stderr and code:
            llm_content += self._generate_debug_analysis(code, stderr)
        
        return AgentToolReturn(
            for_llm=llm_content,
            for_human=f"Python execution {status.lower()} (exit code: {returncode})"
        )
    
    def _generate_debug_analysis(self, code: str, stderr: str) -> str:
        """生成代码调试分析"""
        debug_content = f"\n\n=== AUTO DEBUG ANALYSIS ===\n"
        debug_content += "The following Python code produced an error:\n\n"
        debug_content += "=== CODE ===\n"
        
        # 添加行号的代码显示
        code_lines = code.split('\n')
        for i, line in enumerate(code_lines, 1):
            debug_content += f"{i:3d}: {line}\n"
        
        debug_content += f"\n=== ERROR OUTPUT ===\n{stderr}\n"
        debug_content += "\nPlease analyze the error and provide fix suggestions."
        
        return debug_content