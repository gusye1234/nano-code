import asyncio
import subprocess
import os
from ...constants import MAX_FOR_LLM_TOOL_RETURN_TOKENS
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session


class ManageDependenciesTool(AgentToolDefine):
    
    @classmethod
    def init(cls, **kwargs):
        return cls(
            name="manage_dependencies",
            description="""Automatically check and install Python dependencies.
Checks if packages are installed, and installs them if missing.

Examples:
- {"packages": ["numpy", "pandas"]}
- {"packages": ["requests"]}
""",
            parameters_schema={
                "properties": {
                    "packages": {
                        "description": "List of package names to check and install if missing",
                        "type": "array",
                        "items": {"type": "string"},
                    },
                },
                "required": ["packages"],
                "type": "object",
            },
        )

    async def _execute(self, session: Session, arguments) -> AgentToolReturn:
        packages = arguments["packages"]
        
        session.log(f"Checking and installing packages in virtual environment: {packages}")
        
        try:
            missing_packages = []
            installed_packages = []
            
            # 确保虚拟环境存在
            await self._ensure_venv(session.working_dir)
            
            # 检查每个包是否已安装
            for package in packages:
                if await self._is_package_installed(package, session.working_dir):
                    installed_packages.append(package)
                else:
                    missing_packages.append(package)
            
            # 如果有缺失的包，进行安装
            if missing_packages:
                install_result = await self._install_packages(missing_packages, session.working_dir)
                if not install_result["success"]:
                    return AgentToolReturn(
                        for_llm=f"Failed to install missing packages: {missing_packages}\nError: {install_result['error']}",
                        for_human=f"Failed to install packages: {', '.join(missing_packages)}"
                    )
                
                # 重新检查安装结果
                newly_installed = []
                still_missing = []
                for package in missing_packages:
                    if await self._is_package_installed(package, session.working_dir):
                        newly_installed.append(package)
                    else:
                        still_missing.append(package)
                
                if still_missing:
                    return AgentToolReturn(
                        for_llm=f"Partially successful. Installed: {newly_installed}. Failed: {still_missing}",
                        for_human=f"Some packages failed to install: {', '.join(still_missing)}"
                    )
            
            # 构建返回消息
            messages = []
            if installed_packages:
                messages.append(f"Already installed: {', '.join(installed_packages)}")
            if missing_packages:
                messages.append(f"Newly installed: {', '.join(missing_packages)}")
            
            venv_dir = os.path.join(session.working_dir, 'venv')
            venv_info = f"Virtual environment: {venv_dir}"
            
            return AgentToolReturn(
                for_llm=f"Package management completed:\n" + "\n".join(messages) + f"\n{venv_info}",
                for_human=f"Checked {len(packages)} packages. " + 
                         f"Already installed: {len(installed_packages)}, "
                         f"Newly installed: {len(missing_packages)}"
            )
            
        except Exception as e:
            return AgentToolReturn.error(
                self.name,
                f"Failed to manage dependencies: {str(e)}"
            )
    
    def _venv_exists(self, venv_dir: str) -> bool:
        """检查虚拟环境是否存在"""
        venv_python = os.path.join(venv_dir, 'bin', 'python')
        venv_pip = os.path.join(venv_dir, 'bin', 'pip')
        return os.path.exists(venv_python) and os.path.exists(venv_pip)
    
    async def _ensure_venv(self, working_dir: str) -> bool:
        """确保虚拟环境存在"""
        venv_dir = os.path.join(working_dir, 'venv')
        
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
        
        return True
    
    async def _is_package_installed(self, package: str, working_dir: str) -> bool:
        """检查包是否在虚拟环境中已安装"""
        try:
            venv_dir = os.path.join(working_dir, 'venv')
            if not self._venv_exists(venv_dir):
                return False
            
            venv_python = os.path.join(venv_dir, 'bin', 'python')
            
            # 在虚拟环境中测试导入
            process = await asyncio.create_subprocess_exec(
                venv_python, '-c', f'import {package}',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            await process.communicate()
            return process.returncode == 0
            
        except Exception:
            return False
    
    async def _install_packages(self, packages: list, working_dir: str) -> dict:
        """在虚拟环境中安装包"""
        try:
            venv_dir = os.path.join(working_dir, 'venv')
            if not self._venv_exists(venv_dir):
                await self._ensure_venv(working_dir)
            
            venv_pip = os.path.join(venv_dir, 'bin', 'pip')
            
            # 安装包
            cmd = [venv_pip, 'install'] + packages
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=working_dir
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                return {
                    "success": True, 
                    "message": f"Successfully installed: {', '.join(packages)}"
                }
            else:
                error_msg = stderr.decode('utf-8', errors='replace') if stderr else stdout.decode('utf-8', errors='replace')
                return {"success": False, "error": f"Failed to install packages: {error_msg}"}
                
        except Exception as e:
            return {"success": False, "error": f"Exception while installing packages: {str(e)}"}