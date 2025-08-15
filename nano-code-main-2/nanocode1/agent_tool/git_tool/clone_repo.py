import os
import asyncio
from pathlib import Path
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session


class CloneRepoTool(AgentToolDefine):
    name: str = "clone_repository"
    description: str = """Clone the latest version from Git repository with smart branch detection.
    Automatically tries main branch first, then master, then default branch."""
    
    parameters_schema: dict = {
        "type": "object",
        "properties": {
            "repo_url": {
                "type": "string",
                "description": "Git repository URL (HTTPS or SSH format)"
            },
            "target_dir": {
                "type": "string", 
                "description": "Target directory name (optional, auto-extracted from URL if not provided)"
            },
            "branch": {
                "type": "string",
                "description": "Specific branch to clone (optional, defaults to main/master detection)"
            }
        },
        "required": ["repo_url"]
    }


    @classmethod
    def init(cls, **kwargs) -> "CloneRepoTool":
        return cls(**kwargs)

    def _parse_clone_strategy(self, arguments: dict) -> dict:
        """解析克隆策略 - 只处理最新版本"""
        repo_url = arguments["repo_url"]
        
        # 确保target_dir只是目录名，不是完整路径
        target_dir = arguments.get("target_dir") or self._extract_repo_name(repo_url)
        if os.path.isabs(target_dir):
            # 如果传入了绝对路径，只取最后的目录名
            target_dir = os.path.basename(target_dir)
        
        strategy = {
            "repo_url": repo_url,
            "target_dir": target_dir,
            "branch": arguments.get("branch") or "auto"  # 用户指定分支或自动检测
        }
        
        return strategy

    def _extract_repo_name(self, repo_url: str) -> str:
        """从URL提取仓库名"""
        # https://github.com/user/repo.git -> repo
        # git@github.com:user/repo.git -> repo
        name = repo_url.split('/')[-1].replace('.git', '')
        return name if name else "cloned_repo"

    async def _execute(self, session: Session, arguments: dict) -> AgentToolReturn:
        strategy = self._parse_clone_strategy(arguments)
        # 克隆到专门的repos目录，避免与AI生成文件混合
        repos_dir = os.path.join(session.working_dir, "repos")
        os.makedirs(repos_dir, exist_ok=True)
        target_path = os.path.join(repos_dir, strategy["target_dir"])
        
        # 检查目标目录是否已存在
        if os.path.exists(target_path):
            return AgentToolReturn.error(
                self.name, 
                f"Directory '{strategy['target_dir']}' already exists"
            )
        
        try:
            # 创建父目录
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 根据策略执行克隆（只有两种情况：自动检测或用户指定分支）
            if strategy["branch"] == "auto":
                result = await self._clone_auto_branch(strategy, target_path, session)
            else:
                result = await self._clone_specific_branch(strategy, target_path, session)
                
            return result
            
        except Exception as e:
            return AgentToolReturn.error(self.name, f"克隆过程出错: {str(e)}")

    async def _clone_auto_branch(self, strategy: dict, target_path: str, session: Session) -> AgentToolReturn:
        """自动检测主分支并克隆"""
        
        # 按优先级尝试主分支
        main_branches = ["main", "master", "develop"]
        
        for branch in main_branches:
            # 确保在repos目录中执行git命令，避免路径问题
            repos_dir = os.path.dirname(target_path)
            target_dir_name = os.path.basename(target_path)
            
            git_cmd = [
                "git", "clone",
                "--depth", "1",
                "--single-branch", 
                "--branch", branch,
                strategy["repo_url"], 
                target_dir_name  # 在repos目录中使用相对路径
            ]
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *git_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=repos_dir  # 在repos目录中执行
                )
                
                _, stderr = await process.communicate()
                
                if process.returncode == 0:
                    return AgentToolReturn(
                        for_llm=f"Successfully cloned {strategy['repo_url']} (branch: {branch}) to {strategy['target_dir']}",
                        for_human=f"✅ 成功克隆仓库到 {strategy['target_dir']} 目录 (自动检测分支: {branch})"
                    )
                    
            except Exception:
                continue  # 尝试下一个分支
                
        # 所有分支都失败，最后尝试不指定分支的默认克隆
        return await self._fallback_clone(strategy, target_path, session)

    async def _clone_specific_branch(self, strategy: dict, target_path: str, session: Session) -> AgentToolReturn:
        """克隆用户指定的分支（最新版本）"""
        
        # 确保在repos目录中执行git命令，避免路径问题
        repos_dir = os.path.dirname(target_path)
        target_dir_name = os.path.basename(target_path)
        
        git_cmd = [
            "git", "clone",
            "--depth", "1",  # 浅克隆，只要最新版本
            "--single-branch",
            "--branch", strategy["branch"],
            strategy["repo_url"], 
            target_dir_name  # 在repos目录中使用相对路径
        ]
        
        process = await asyncio.create_subprocess_exec(
            *git_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=repos_dir  # 在repos目录中执行
        )
        
        _, stderr = await process.communicate()
        
        if process.returncode == 0:
            return AgentToolReturn(
                for_llm=f"Successfully cloned {strategy['repo_url']} (branch: {strategy['branch']}) to {strategy['target_dir']}",
                for_human=f"✅ 成功克隆仓库到 {strategy['target_dir']} 目录 (分支: {strategy['branch']})"
            )
        else:
            error_msg = stderr.decode('utf-8', errors='replace')
            return AgentToolReturn.error(
                self.name,
                f"无法克隆分支 '{strategy['branch']}': {error_msg}"
            )


    async def _fallback_clone(self, strategy: dict, target_path: str, session: Session) -> AgentToolReturn:
        """回退到默认克隆方式"""
        # 确保在repos目录中执行git命令，避免路径问题
        repos_dir = os.path.dirname(target_path)
        target_dir_name = os.path.basename(target_path)
        
        git_cmd = ["git", "clone", "--depth", "1", strategy["repo_url"], target_dir_name]
        
        process = await asyncio.create_subprocess_exec(
            *git_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=repos_dir  # 在repos目录中执行
        )
        
        _, stderr = await process.communicate()
        
        if process.returncode == 0:
            return AgentToolReturn(
                for_llm=f"Successfully cloned {strategy['repo_url']} (default branch) to {strategy['target_dir']}",
                for_human=f"✅ 成功克隆仓库到 {strategy['target_dir']} 目录 (默认分支)"
            )
        else:
            error_msg = stderr.decode('utf-8', errors='replace')
            return AgentToolReturn.error(self.name, f"克隆失败: {error_msg}")