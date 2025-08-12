import os
import asyncio
from pathlib import Path
from ..base import AgentToolDefine, AgentToolReturn
from ...core.session import Session
from ...prompts import GIT_ANALYSIS_MESSAGE, GIT_ANALYSIS_IMPORTANT


class AnalyzeRepoTool(AgentToolDefine):
    name: str = "analyze_repository_structure"
    description: str = "Analyze the structure, file types, code statistics, and key information of a Git repository"
    parameters_schema: dict = {
        "type": "object",
        "properties": {
            "repo_path": {
                "type": "string",
                "description": "The local path of the repository to analyze"
            },
            "max_files": {
                "type": "integer",
                "description": "Maximum number of files to analyze, to avoid overload with large repositories",
                "default": 100
            }
        },
        "required": ["repo_path"]
    }
    

    @classmethod 
    def init(cls, **kwargs) -> "AnalyzeRepoTool":
        return cls(**kwargs)

    async def _execute(self, session: Session, arguments: dict) -> AgentToolReturn:
        repo_path = arguments["repo_path"]

        max_files = arguments.get("max_files", 100)
        
        # 确保路径是绝对路径
        if not os.path.isabs(repo_path):
            repo_path = os.path.join(session.working_dir, repo_path)
        
        repo_dir = Path(repo_path)
        
        try:
            # 检查路径是否存在且是Git仓库
            if not repo_dir.exists():
                return AgentToolReturn(
                    for_llm=f"Repository path does not exist: {repo_path}",
                    for_human=f"❌ The repository path does not exist: {repo_path}"
                )
            
            git_dir = repo_dir / ".git"
            if not git_dir.exists():
                return AgentToolReturn(
                    for_llm=f"Path is not a Git repository: {repo_path}",
                    for_human=f"❌ The path is not a Git repository: {repo_path}"
                )
            
            analysis_result = await self.normal_analysis(repo_path, max_files)
            
            formatted_output = self._format_analysis_output(analysis_result)

            key_files = analysis_result.get('key_files', [])
            llm_prompt = GIT_ANALYSIS_MESSAGE.format(
                repo_path=repo_path,
                total_files=analysis_result.get('total_files', 0),
                file_types_count=len(analysis_result.get('file_types', {})),
                key_files=', '.join(key_files)
            )

            if key_files:
                llm_prompt += GIT_ANALYSIS_IMPORTANT.format(
                    key_files_list=', '.join(key_files[:5])
                )
            
            return AgentToolReturn(
                for_llm=llm_prompt,
                for_human=formatted_output
            )
            
        except Exception as e:
            return AgentToolReturn(
                for_llm=f"Error analyzing repository {repo_path}: {str(e)}",
                for_human=f"❌ An error occurred while analyzing the repository: {str(e)}"
            )

    async def normal_analysis(self, repo_path: str, max_files: int) -> dict:
        """执行基础仓库分析"""
        analysis = {
            "repo_path": repo_path,
            "git_info": {},
            "directory_structure": {},
            "file_types": {},
            "total_files": 0,
            "total_lines": 0,
            "key_files": []
        }
        
        # Git信息
        git_info_cmd = f"cd {repo_path} && git remote -v && echo '---' && git branch -a && echo '---' && git log --oneline -10"
        try:
            process = await asyncio.create_subprocess_shell(
                git_info_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            if stdout:
                analysis["git_info"] = stdout.decode('utf-8')
        except:
            analysis["git_info"] = "Failed to get Git information"
        
        # 文件统计
        repo_dir = Path(repo_path)
        file_count = 0
        
        for file_path in repo_dir.rglob("*"):
            if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts[len(repo_dir.parts):]):
                if file_count >= max_files:
                    break
                    
                file_count += 1
                analysis["total_files"] += 1
                
                # 文件扩展名统计
                suffix = file_path.suffix.lower()
                if suffix:
                    analysis["file_types"][suffix] = analysis["file_types"].get(suffix, 0) + 1
                
                # 关键文件识别
                filename = file_path.name.lower()
                if filename in ["readme.md", "package.json", "requirements.txt", "dockerfile", "makefile", "setup.py", "cargo.toml", "pom.xml", "build.gradle"]:
                    analysis["key_files"].append(str(file_path.relative_to(repo_dir)))
        
        
        # 深度代码分析 - 统计各文件类型的代码行数
        analysis["code_analysis"] = {}
        common_extensions = [".py", ".js", ".ts", ".java", ".go", ".cpp", ".c", ".rs", ".php", ".rb"]
        
        for ext in common_extensions:
            if ext in analysis["file_types"]:  # 只分析仓库中存在的文件类型
                lines_cmd = f"find {repo_path} -name '*{ext}' -type f -exec wc -l {{}} + 2>/dev/null | tail -1"
                try:
                    process = await asyncio.create_subprocess_shell(
                        lines_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, _ = await process.communicate()
                    if stdout:
                        lines_info = stdout.decode('utf-8').strip()
                        if lines_info and lines_info.split():
                            lines_count = lines_info.split()[0]
                            if lines_count.isdigit():
                                analysis["code_analysis"][ext] = {
                                    "total_lines": int(lines_count),
                                    "file_count": analysis["file_types"][ext]
                                }
                                analysis["total_lines"] += int(lines_count)
                except:
                    continue
        
        return analysis

    def _format_analysis_output(self, analysis: dict) -> str:
        """格式化分析输出"""
        output = f"""📊 Repository Analysis Report

📁 Repository Path: {analysis['repo_path']}
📈 Analysis Type: Complete Deep Analysis

🔍 Statistics:
- Total Files: {analysis['total_files']}
- Total Code Lines: {analysis['total_lines']:,}
- File Types: {len(analysis['file_types'])} types

📋 File Type Distribution:"""
        
        # 文件类型统计
        for ext, count in sorted(analysis['file_types'].items(), key=lambda x: x[1], reverse=True)[:10]:
            output += f"\n  {ext}: {count} files"   
        
        # Git信息
        if analysis.get('git_info'):
            output += f"\n\n🔗 Git Information:\n{analysis['git_info']}"
        
        # 关键文件
        if analysis.get('key_files'):
            output += f"\n\n📄 Key Files:"
            for key_file in analysis['key_files'][:10]:
                output += f"\n  - {key_file}"
        
        # 代码统计分析
        if analysis.get('code_analysis'):
            output += f"\n\n💻 Code Analysis:"
            for ext, info in sorted(analysis['code_analysis'].items(), key=lambda x: x[1]['total_lines'], reverse=True):
                output += f"\n  {ext}: {info['total_lines']:,} lines in {info['file_count']} files"
        
        return output