import asyncio
import os
from typing import Dict, Any, List


class PythonExecutor:

    @staticmethod
    async def run_code(code: str, working_dir: str) -> Dict[str, Any]:
        """执行Python代码字符串"""
        return await PythonExecutor._execute_subprocess(
            ['python3', '-c', code], 
            working_dir
        )
    
    @staticmethod  
    async def run_file(file_path: str, working_dir: str) -> Dict[str, Any]:
        """执行Python文件"""
        # 确保使用绝对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(working_dir, file_path)
        
        return await PythonExecutor._execute_subprocess(
            ['python3', file_path], 
            working_dir
        )
        
    @staticmethod
    async def install_packages(packages: List[str], working_dir: str) -> Dict[str, Any]:
        """安装Python包"""
        cmd = ['pip3', 'install'] + packages
        return await PythonExecutor._execute_subprocess(cmd, working_dir)
        
    @staticmethod
    async def check_package(package: str, working_dir: str) -> bool:
        """检查包是否已安装"""
        result = await PythonExecutor._execute_subprocess(
            ['python3', '-c', f'import {package}'], 
            working_dir
        )
        return result["returncode"] == 0
    
    @staticmethod
    async def _execute_subprocess(cmd: List[str], working_dir: str) -> Dict[str, Any]:
        """
        统一的子进程执行方法
        
        返回标准格式的结果字典，便于上层工具统一处理
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
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
                "stdout": "",
                "stderr": f"Exception: {str(e)}",
                "returncode": -1
            }