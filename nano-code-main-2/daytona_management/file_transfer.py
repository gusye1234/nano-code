from pathlib import Path
from typing import List, Optional
from daytona_sdk.common.process import SessionExecuteRequest
from openai import uploads
from .config import PathConfig
import re


class FileTransfer:
    """文件传输操作管理"""
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
    
    def upload_files(self, local_files: List[str]) -> List[str]:
        """
        上传本地文件到upload目录
        Args:
            local_files (List[str]): 本地文件路径列表
        Returns:
            List[str]: 上传后的远程文件路径列表
        """
        print("📤 开始上传文件到upload目录...")
        uploaded_paths = []
        
        if not local_files:
            print("📁 无文件上传")
            return uploaded_paths
        
        # 批量上传文件
        total_files = len(local_files)
        successful_uploads = 0
        
        for i, local_file in enumerate(local_files, 1):
            local_path = Path(local_file)
            if not local_path.exists():
                print(f"⚠️  本地文件不存在: {local_file}")
                continue
                
            remote_path = f"{PathConfig.TMP_DIR}/{local_path.name}"
            
            try:
                with open(local_path, 'rb') as f:
                    file_content = f.read()
                
                self.sandbox.fs.upload_file(file_content, remote_path)
                uploaded_paths.append(remote_path)
                successful_uploads += 1
                print(f"✅ 上传成功 ({i}/{total_files}): {local_file} → {remote_path}")
                
            except Exception as e:
                print(f"❌ 上传失败 ({i}/{total_files}): {local_file} - {e}")
        
        if successful_uploads > 0:
            print(f"📁 上传完成：{successful_uploads}/{total_files} 个文件成功")
        
        return uploaded_paths

    def process_json_file_and_upload(self, json_file_path: str) -> str:
        """
        处理JSON文件上传并返回远程路径, 这里是特殊的上传因为这个文件是任务上传
        Args:
            json_file_path (str): JSON文件路径
        Returns:
            str: 上传后的远程文件路径
        """
        local_path = Path(json_file_path)
        
        if not local_path.exists():
            raise FileNotFoundError(f"JSON文件不存在: {json_file_path}")
        
        if not local_path.suffix.lower() == '.json':
            raise ValueError(f"输入文件必须是JSON格式: {json_file_path}")
        
        # 上传JSON文件到远程
        remote_path = f"{PathConfig.TMP_DIR}/{local_path.name}"
        
        try:
            with open(local_path, 'rb') as f:
                file_content = f.read()
            
            self.sandbox.fs.upload_file(file_content, remote_path)
            print(f"✅ 上传JSON文件: {json_file_path} → {remote_path}")
            return remote_path
            
        except Exception as e:
            raise Exception(f"上传JSON文件失败: {json_file_path} - {e}")
    
    def download_results(self, session_id: str) -> List[str]:
        """
        下载结果文件到本地
        Args:
            session_id (str): 会话ID
        Returns:
            List[str]: 下载后的本地文件路径列表
        """
        print("📥 开始下载结果文件...")
        
        # 创建本地下载目录
        download_dir = PathConfig.LOCAL_DOWNLOAD_DIR
        download_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            downloaded_files = []
            
            if session_id:
                # 列出download目录下的结果文件
                list_cmd = f"find {PathConfig.DOWNLOAD_DIR} -maxdepth 1 -type f \\( -name '*.csv' -o -name '*.txt' -o -name '*.json' -o -name '*.html' -o -name '*.md' -o -name '*.png' -o -name '*.jpg' -o -name '*.py' -o -name '*.pdf' -o -name '*.xlsx' \\) 2>/dev/null || true"
                req = SessionExecuteRequest(command=list_cmd)
                result = self.sandbox.process.execute_session_command(session_id, req)
                
                if result.output.strip():
                    file_paths = result.output.strip().split('\n')
                    print(f"🎯 在download目录找到 {len(file_paths)} 个结果文件")
                    
                    for remote_path in file_paths:
                        remote_path = remote_path.strip()
                        if remote_path and remote_path != "":
                            try:
                                # 下载文件
                                file_content = self.sandbox.fs.download_file(remote_path)
                                
                                # 保存到本地
                                local_filename = Path(remote_path).name
                                local_path = download_dir / local_filename
                                
                                with open(local_path, 'wb') as f:
                                    f.write(file_content)
                                
                                downloaded_files.append(str(local_path))
                                print(f"✅ 下载成功: {remote_path} → {local_path}")
                                
                            except Exception as e:
                                print(f"⚠️  下载失败 {remote_path}: {e}")
                else:
                    print("📁 download目录中没有找到结果文件")
                
            if downloaded_files:
                print(f"📁 共下载 {len(downloaded_files)} 个结果文件到: {download_dir}")
                return downloaded_files
            else:
                print("📁 未找到可下载的结果文件")
                return []
                
        except Exception as e:
            print(f"❌ 下载过程出错: {e}")
            return []
    
    def collect_output_files(self, session_id: str, input_filenames: Optional[List[str]] = None, copy: bool = True):
        """
        收集AI生成的输出文件到download目录
        Args:
            session_id (str): 会话ID
            input_filenames (Optional[List[str]]): 输入文件名列表，用于排除
            copy (bool): True为复制模式（保留原文件），False为移动模式
        """
        operation_name = "复制" if copy else "移动"
        print(f"📦 收集输出文件({operation_name}模式)...")
        
        find_cmd = f"find {PathConfig.TMP_DIR} -type f -not -path '*/.*' -not -path '*/__pycache__/*' -not -path '*/venv/*' 2>/dev/null"
        req = SessionExecuteRequest(command=find_cmd)
        result = self.sandbox.process.execute_session_command(session_id, req)
        
        if result.output.strip():
            all_files = result.output.strip().split('\n')
            
            input_filenames = input_filenames or []
            ai_generated_files = []
            
            for file_path in all_files:
                file_path = file_path.strip()
                if file_path:
                    filename = file_path.split('/')[-1]
                    
                    # 跳过输入文件
                    if filename in input_filenames:
                        continue
                    
                    # 排除克隆的Git仓库目录
                    if 'repos/' in file_path or '/repos/' in file_path:
                        continue

                    # 保留 SimpleContext 上下文：不要移动 agent_context_*.json
                    if filename.startswith('agent_context_') and filename.endswith('.json'):
                        continue
                    
                    # 更强的Git仓库检测：只保留明确的AI输出文件
                    # 如果文件在一个看起来像Git仓库的目录中（有常见的仓库文件），跳过它
                    path_parts = file_path.split('/')
                    
                    # 检查是否在同一个目录级别有常见的Git仓库文件
                    file_dir = '/'.join(path_parts[:-1])  # 文件所在目录
                    common_repo_files = ['README.md', 'LICENSE', 'setup.py', 'pyproject.toml', 'package.json', '.gitignore']
                    
                    # 简单策略：如果文件名是常见的源码文件类型，且不是明确的分析输出，跳过
                    if (filename.endswith(('.py', '.js', '.ts', '.java', '.go', '.rs', '.cpp', '.c', '.h')) 
                        and not filename.startswith('architecture_analysis_') 
                        and not filename.startswith('analysis_')
                        and not filename.startswith('project_structure')
                        and not filename.startswith('application_flow')):
                        continue
                    
                    # 保留matplotlib生成的PNG文件
                    if filename.endswith('.png') and (
                        filename.startswith('project_structure') or 
                        filename.startswith('application_flow') or 
                        'analysis' in filename):
                        # 这些是AI生成的可视化文件，保留
                        pass
                    
                    # 排除常见的仓库配置文件
                    if filename in ['README.md', 'LICENSE', 'setup.py', 'pyproject.toml', 'package.json', '.gitignore', 'Cargo.toml', 'go.mod']:
                        continue
                    
                    # 检查是否应该排除
                    should_exclude = False
                    for pattern in PathConfig.EXCLUDE_PATTERNS:
                        if pattern in filename or pattern in file_path:
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        ai_generated_files.append(file_path)
            
            if ai_generated_files:
                print(f"🔍 发现 {len(ai_generated_files)} 个生成文件")
                
                processed_count = 0
                for file_path in ai_generated_files:
                    filename = file_path.split('/')[-1]
                    download_path = f"{PathConfig.DOWNLOAD_DIR}/{filename}"
                    
                    # 根据copy参数选择操作命令
                    if copy:
                        op_cmd = f"cp -f '{file_path}' '{download_path}'"
                        action_verb = "复制"
                    else:
                        op_cmd = f"mv '{file_path}' '{download_path}'"
                        action_verb = "移动"
                    
                    req = SessionExecuteRequest(command=op_cmd)
                    op_result = self.sandbox.process.execute_session_command(session_id, req)
                    
                    if op_result.exit_code == 0:
                        print(f"✅ {action_verb}生成文件: {filename}")
                        processed_count += 1
                    else:
                        print(f"⚠️  {action_verb}失败: {filename}")
                
                if processed_count > 0:
                    print(f"📁 成功{operation_name} {processed_count} 个输出文件到 {PathConfig.DOWNLOAD_DIR}")
                else:
                    print(f"⚠️  未能{operation_name}任何输出文件")
            else:
                print("📁 未发现新创建的文件")
        else:
            print("📁 tmp目录中未发现文件")
    
