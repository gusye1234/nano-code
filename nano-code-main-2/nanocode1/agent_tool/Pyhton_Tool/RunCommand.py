import asyncio
import tempfile
import os
from ...constants import MAX_FOR_LLM_TOOL_RETURN_TOKENS
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session


class RunCommandTool(AgentToolDefine):    
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="run_command",
            description="""Execute Python code. Simple tool for running Python scripts and code.

Examples:
- {"code": "print('hello world')"}
- {"file": "script.py"}
- {"code": "import os; print(os.getcwd())", "timeout": 10}
""",
            parameters_schema={
                "properties": {
                    "code": {
                        "description": "Python code to execute",
                        "type": "string",
                    },
                    "file": {
                        "description": "Python file to run",
                        "type": "string",
                    },
                    
                },
                "one_of": [
                    {"required": ["code"]},
                    {"required": ["file"]}
                ],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        code = arguments.get("code")
        file_path = arguments.get("file") 
        
        if not code and not file_path:
            return AgentToolReturn.error(self.name, "Either 'code' or 'file' required")
        
        if code and file_path:
            return AgentToolReturn.error(self.name, "Cannot specify both 'code' and 'file'")
        
        try:
            if code:
                # execute code (str) - 在虚拟环境中运行
                result = await self._run_python_code(code, session.working_dir)
                return self._format_result("code execution", result, code, session.working_dir)
            else:
                # execute code (file) - 在虚拟环境中运行
                full_path = os.path.join(session.working_dir, file_path)
                if not os.path.exists(full_path):
                    return AgentToolReturn.error(self.name, f"File '{file_path}' not found")
                
                # read code file for debug analysis
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        file_code = f.read()
                except Exception:
                    file_code = None
                
                result = await self._run_python_file(file_path, session.working_dir)
                return self._format_result(file_path, result, file_code, session.working_dir)
                
        except Exception as e:
            return AgentToolReturn.error(self.name, f"Execution failed: {str(e)}")
    
    
    def _format_result(self, source: str, result: dict, code: str = None, working_dir: str = None) -> AgentToolReturn:
        stdout = result.get('stdout', '').strip()
        stderr = result.get('stderr', '').strip()
        returncode = result.get('returncode', -1)
        
        output_parts = []
        if stdout:
            output_parts.append(stdout)
        if stderr:
            output_parts.append(f"error: {stderr}")
        
        output = "\n".join(output_parts) if output_parts else "(no output)"
        
        if len(output) > MAX_FOR_LLM_TOOL_RETURN_TOKENS:
            output = output[:MAX_FOR_LLM_TOOL_RETURN_TOKENS] + "...[truncated]"
        
        status = "SUCCESS" if returncode == 0 else "ERROR"
        
        # 添加虚拟环境信息
        env_info = ""
        if working_dir:
            venv_dir = os.path.join(working_dir, 'venv')
            env_info = f"\nVirtual environment: {venv_dir}"
        
        # when error occurs use debug tool
        llm_content = f"Python {source} executed.{env_info}\nReturn code: {returncode}\nOutput:\n{output}"
        
        if returncode != 0 and stderr and code:
            llm_content += f"\n\n=== AUTO DEBUG ANALYSIS ===\n"
            llm_content += "The following Python code produced an error:\n\n"
            llm_content += "=== CODE ===\n"
            # code with line number
            code_lines = code.split('\n')
            for i, line in enumerate(code_lines, 1):
                llm_content += f"{i:3d}: {line}\n"
            llm_content += f"\n=== ERROR OUTPUT ===\n{stderr}\n"
            llm_content += "\nPlease analyze the error and provide fix suggestions."
        
        return AgentToolReturn(
            for_llm=llm_content,
            for_human=f"Python execution {status.lower()} (exit code: {returncode})"
        )
    
    def _venv_exists(self, venv_dir: str) -> bool:
        """检查虚拟环境是否存在"""
        venv_python = os.path.join(venv_dir, 'bin', 'python')
        venv_pip = os.path.join(venv_dir, 'bin', 'pip')
        return os.path.exists(venv_python) and os.path.exists(venv_pip)
    
    async def _ensure_venv(self, working_dir: str) -> str:
        """确保虚拟环境存在，返回Python可执行文件路径"""
        venv_dir = os.path.join(working_dir, 'venv')
        venv_python = os.path.join(venv_dir, 'bin', 'python')
        
        if not self._venv_exists(venv_dir):
            # 创建虚拟环境
            process = await asyncio.create_subprocess_exec(
                'python3', '-m', 'venv', venv_dir,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='replace') if stderr else stdout.decode('utf-8', errors='replace')
                raise RuntimeError(f"Failed to create virtual environment: {error_msg}")
        
        return venv_python
    
    async def _run_python_code(self, code: str, working_dir: str) -> dict:
        """在虚拟环境中运行Python代码"""
        try:
            python_exec = await self._ensure_venv(working_dir)
            
            process = await asyncio.create_subprocess_exec(
                python_exec, '-c', code,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace') if stdout else "",
                "stderr": stderr.decode('utf-8', errors='replace') if stderr else "",
                "returncode": process.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception while running Python code: {str(e)}",
                "returncode": -1
            }
    
    async def _run_python_file(self, file_path: str, working_dir: str) -> dict:
        """在虚拟环境中运行Python文件"""
        try:
            python_exec = await self._ensure_venv(working_dir)
            
            # 确保文件路径是绝对路径
            if not os.path.isabs(file_path):
                file_path = os.path.join(working_dir, file_path)
            
            process = await asyncio.create_subprocess_exec(
                python_exec, file_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode('utf-8', errors='replace') if stdout else "",
                "stderr": stderr.decode('utf-8', errors='replace') if stderr else "",
                "returncode": process.returncode
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Exception while running Python file: {str(e)}",
                "returncode": -1
            }