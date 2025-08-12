from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session
from .python_executor import PythonExecutor


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
        
        session.log(f"Managing Python packages: {packages}")
        
        try:
            # 检查包的安装状态
            installed_packages, missing_packages = await self._check_packages_status(
                packages, session.working_dir
            )
            
            # 安装缺失的包
            install_results = []
            if missing_packages:
                install_result = await PythonExecutor.install_packages(
                    missing_packages, session.working_dir
                )
                
                if not install_result["success"]:
                    return AgentToolReturn(
                        for_llm=f"Failed to install packages: {missing_packages}\nError: {install_result['stderr']}",
                        for_human=f"Failed to install: {', '.join(missing_packages)}"
                    )
                
                # 验证安装结果
                newly_installed, still_missing = await self._verify_installation(
                    missing_packages, session.working_dir
                )
                
                if still_missing:
                    return AgentToolReturn(
                        for_llm=f"Partial success. Installed: {newly_installed}. Failed: {still_missing}",
                        for_human=f"Some packages failed: {', '.join(still_missing)}"
                    )
                
                install_results = newly_installed
            
            # 生成成功报告
            return self._generate_success_report(
                installed_packages, install_results, session.working_dir
            )
            
        except Exception as e:
            return AgentToolReturn.error(
                self.name,
                f"Failed to manage dependencies: {str(e)}"
            )
    
    async def _check_packages_status(self, packages: list, working_dir: str) -> tuple:
        """检查包的安装状态，返回(已安装, 缺失)的包列表"""
        installed = []
        missing = []
        
        for package in packages:
            if await PythonExecutor.check_package(package, working_dir):
                installed.append(package)
            else:
                missing.append(package)
        
        return installed, missing
    
    async def _verify_installation(self, packages: list, working_dir: str) -> tuple:
        """验证安装结果，返回(成功安装, 仍然缺失)的包列表"""
        newly_installed = []
        still_missing = []
        
        for package in packages:
            if await PythonExecutor.check_package(package, working_dir):
                newly_installed.append(package)
            else:
                still_missing.append(package)
        
        return newly_installed, still_missing
    
    def _generate_success_report(self, installed: list, newly_installed: list, working_dir: str) -> AgentToolReturn:
        """生成成功报告"""
        messages = []
        if installed:
            messages.append(f"Already installed: {', '.join(installed)}")
        if newly_installed:
            messages.append(f"Newly installed: {', '.join(newly_installed)}")
        
        total_packages = len(installed) + len(newly_installed)
        env_info = f"Environment: Daytona container at {working_dir}"
        
        llm_content = "Package management completed:\n" + "\n".join(messages) + f"\n{env_info}"
        
        return AgentToolReturn(
            for_llm=llm_content,
            for_human=f"Managed {total_packages} packages successfully. "
                     f"Already installed: {len(installed)}, Newly installed: {len(newly_installed)}"
        )