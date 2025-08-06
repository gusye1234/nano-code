import os
import sys
import signal
import json
from pathlib import Path
from daytona_sdk import Daytona, DaytonaConfig
from daytona_sdk.common.process import SessionExecuteRequest
from daytona_sdk.common.daytona import CreateSandboxFromImageParams



class NanoCodeProxy:
    
    def __init__(self, max_iterations: int = 20):
        self.daytona_client = None
        self.sandbox = None
        self.running = True
        self.max_iterations = max_iterations  # 可配置的执行轮次
        
        signal.signal(signal.SIGINT, self._cleanup_and_exit)
        signal.signal(signal.SIGTERM, self._cleanup_and_exit)
    
    def setup_daytona(self):    #创建Daytona沙盒 设置API
        api_key = "dtn_6a9223aba4abbd47a0ed89e4c8ee8cae1d6237abe658246ca1f66c2a83d58179"
        api_url = "https://app.daytona.io/api"
        
        config = DaytonaConfig(api_key=api_key, api_url=api_url)
        self.daytona_client = Daytona(config)
        
        create_params = CreateSandboxFromImageParams(
            image="filletofish0405/nanodaytona:v1.0"
        )
        self.sandbox = self.daytona_client.create(create_params)
        
        if not self.sandbox:
            raise Exception("沙盒创建失败")

    def _get_api_config(self) -> tuple[str, str]:  #读取nano code所需要的API key
        """获取LLM API配置"""
        # 配置文件读取
        config_path = Path.home() / ".nano_code" / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                api_key = config.get('llm_api_key', '')
                base_url = config.get('llm_base_url', 'https://api.openai.com/v1')
                
                if api_key:
                    return api_key, base_url
            except Exception:
                pass
        
        # 从环境变量读取
        api_key = os.getenv('OPENAI_API_KEY', '')
        base_url = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')
        
        if not api_key:
            raise RuntimeError("未找到LLM API密钥配置")
        
        return api_key, base_url

    def upload_files(self, local_files: list):  #上传分析文件到Daytona
        print("📤 开始上传文件到upload目录...")
        uploaded_paths = []
        
        if not local_files:
            print("📁 无文件上传")
            return uploaded_paths
        
        # 批量上传文件并显示进度
        total_files = len(local_files)
        successful_uploads = 0
        
        for i, local_file in enumerate(local_files, 1):
            local_path = Path(local_file)
            if not local_path.exists():
                print(f"⚠️  本地文件不存在: {local_file}")
                continue
                
            remote_path = f"/workspace/upload/{local_path.name}"
            
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
    
    def download_results(self, session_id: str = None): #下载返回文件
        print("📥 开始下载结果文件...")
        
        # 创建本地下载目录
        download_dir = Path.home() / "Desktop" / "SandboxWork" / "download"
        download_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            downloaded_files = []
            
            if session_id:
                
                # 列出download目录下的结果文件
                list_cmd = "find /workspace/download -maxdepth 1 -type f \\( -name '*.csv' -o -name '*.txt' -o -name '*.json' -o -name '*.html' -o -name '*.md' -o -name '*.png' -o -name '*.jpg' -o -name '*.py' -o -name '*.pdf' -o -name '*.xlsx' \\) 2>/dev/null || true"
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
                                file_content = self.sandbox.fs.download_file(remote_path) #或许考虑更换下载函数
                                
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

    def _setup_secure_workspace(self, session_id: str): #细分目录
        print("🔒 设置工作区...")
        
        setup_commands = [
            # 创建四个目录
            "mkdir -p /workspace/system /workspace/upload /workspace/download /workspace/tmp",
            
            # 移动源代码到system目录
            "mv /workspace/nanocode1 /workspace/system/ 2>/dev/null || true",
            
            # 设置system目录为只读
            "chmod -R 555 /workspace/system/ 2>/dev/null || true",
            
        ]
        
        for cmd in setup_commands:
            req = SessionExecuteRequest(command=cmd)
            result = self.sandbox.process.execute_session_command(session_id, req)
            if result.exit_code != 0 and "No such file" not in str(result.output):
                print(f"⚠️  设置命令失败: {cmd}")
    
    def start_nano_code_batch(self, task_description: str, input_files: list = None):#启动nano code
        print(f"🚀 任务描述: {task_description}")
        
        # 1. 上传输入文件到input目录
        remote_files = []
        if input_files:
            remote_files = self.upload_files(input_files)
        
        # 2. 获取API配置
        api_key, base_url = self._get_api_config()
        
        # 3. 创建会话并设置安全工作区
        session_id = "nano-code-secure-session"
        try:
            self.sandbox.process.create_session(session_id)
            
            # 设置安全工作区
            self._setup_secure_workspace(session_id)
            
            tmp_files = []
            if remote_files:
                for upload_file in remote_files:
                    filename = upload_file.split('/')[-1]
                    tmp_file = f"/workspace/tmp/{filename}"
                    copy_cmd = f"cp '{upload_file}' '{tmp_file}'"
                    req = SessionExecuteRequest(command=copy_cmd)
                    result = self.sandbox.process.execute_session_command(session_id, req)
                    if result.exit_code == 0:
                        tmp_files.append(tmp_file)
                        print(f"✅ 复制文件: {filename}")
                    else:
                        print(f"⚠️  复制失败: {filename}")
            
            # 构建执行命令 (在tmp目录中运行AI)
            batch_cmd = f'cd /workspace/tmp && OPENAI_API_KEY="{api_key}" LLM_BASE_URL="{base_url}" PYTHONPATH="/workspace/system:$PYTHONPATH" python -m nanocode1 --task "{task_description}" --working-dir /workspace/tmp --max-iterations {self.max_iterations}'
            
            if tmp_files:
                # 使用tmp目录中的文件
                input_files_str = " ".join(tmp_files)
                batch_cmd += f' --files {input_files_str}'
            
            print(f"🔧执行命令: {batch_cmd}")
            
            # 执行任务（
            req = SessionExecuteRequest(command=batch_cmd)
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
            
            # 检查和收集输出文件 (传入输入文件名以便过滤)
            input_filenames = [f.split('/')[-1] for f in tmp_files] if tmp_files else []

            self._collect_output_files(session_id, input_filenames)
            
            # 下载结果文件
            downloaded_files = self.download_results(session_id)
            
            if downloaded_files:
                print(f"🎉 任务完成！共生成 {len(downloaded_files)} 个结果文件")
                print("📁 结果文件已下载到: ~/Desktop/SandboxWork/download/")
            else:
                print("🎉 任务完成！")
            
        except Exception as e:
            print(f"❌ 批处理执行失败: {e}")
            import traceback
            print(f"详细错误信息: {traceback.format_exc()}")
        finally:
            try:
                self.sandbox.process.delete_session(session_id)
                print("🧹 会话已清理")
            except:
                pass

    def _collect_output_files(self, session_id: str, input_filenames: list = None): #筛选download文件
        print("📦 收集输出文件...")
        
        # 只查找tmp目录根目录的文件，排除Python包和虚拟环境
        find_cmd = "find /workspace/tmp -maxdepth 1 -type f 2>/dev/null"
        req = SessionExecuteRequest(command=find_cmd)
        result = self.sandbox.process.execute_session_command(session_id, req)
        
        if result.output.strip():
            all_files = result.output.strip().split('\n')
            
            # 过滤掉输入文件和系统文件，只保留AI创建的输出文件
            input_filenames = input_filenames or []
            ai_generated_files = []
            
            # 需要排除的文件模式
            exclude_patterns = [
                '.pyc',           # Python字节码
                '__pycache__',    # Python缓存目录
                'venv',           # 虚拟环境
                '.git',           # Git文件
                '.DS_Store',      # macOS系统文件
                'pip-log.txt',    # pip日志
                'pip-delete-this-directory.txt',  # pip临时文件
            ]
            
            for file_path in all_files:
                file_path = file_path.strip()
                if file_path:
                    filename = file_path.split('/')[-1]
                    
                    # 排除输入文件
                    if filename in input_filenames:
                        continue
                    
                    # 排除系统和包管理文件
                    should_exclude = False
                    for pattern in exclude_patterns:
                        if pattern in filename or pattern in file_path:
                            should_exclude = True
                            break
                    
                    if not should_exclude:
                        ai_generated_files.append(file_path)
            
            if ai_generated_files:
                print(f"🔍 发现 {len(ai_generated_files)} 个AI生成的文件")
                
                # 移动AI生成的文件到download目录
                moved_count = 0
                for file_path in ai_generated_files:
                    filename = file_path.split('/')[-1]
                    download_path = f"/workspace/download/{filename}"
                    
                    # 移动文件
                    move_cmd = f"mv '{file_path}' '{download_path}'"
                    req = SessionExecuteRequest(command=move_cmd)
                    move_result = self.sandbox.process.execute_session_command(session_id, req)
                    
                    if move_result.exit_code == 0:
                        print(f"✅ 收集AI生成文件: {filename}")
                        moved_count += 1
                    else:
                        print(f"⚠️  收集失败: {filename}")
                
                if moved_count > 0:
                    print(f"📁 成功收集 {moved_count} 个AI输出文件到 /workspace/download/")
                else:
                    print("⚠️  未能收集到任何输出文件")
            else:
                print("📁 未发现AI新创建的文件")
        else:
            print("📁 tmp目录中未发现文件")
    
    def _cleanup_and_exit(self, signum, frame):  #结束任务删除沙盒
        print(f"\n接收到信号 {signum}，清理资源...")
        
        if self.sandbox and self.daytona_client:
            try:
                self.daytona_client.delete(self.sandbox)
                print("沙盒已清理")
            except:
                pass
        
        sys.exit(0)
    


def main():
    try:
        proxy = NanoCodeProxy(max_iterations=20)  
        proxy.setup_daytona()
        print(f"✅ 沙盒创建成功: {proxy.sandbox.id}")
        
        # 检查命令行参数
        if len(sys.argv) < 2:
            # 显示使用帮助
            print("=" * 60)
            print("🚀 nano-code 可以正常使用，输入格式有误")
            print("")
            print("💡 使用方法:")
            print("   python3 daytona_proxy.py \"任务描述\" [本地文件...]")
            print("")
            print("📖 示例:")
            print("   python3 daytona_proxy.py \"分析CSV数据\"")
            print("   python3 daytona_proxy.py \"分析这个数据文件\" data.csv")
            print("   python3 daytona_proxy.py \"检查代码质量\" script.py")
            print("   python3 daytona_proxy.py \"处理多个文件\" file1.csv file2.json")
            print("")
            print("🔄 文件处理流程:")
            print("   1. 本地文件自动上传到沙盒")
            print("   2. 在沙盒中执行任务处理")
            print("   3. 结果文件自动下载到 ~/Desktop/SandboxWork/download/")
            print("=" * 60)
            sys.exit(0)
        


        task_description = sys.argv[1]
        input_files = sys.argv[2:] if len(sys.argv) > 2 else None
        
        print("=" * 60)
        print("🎯 nano-code ")
        print(f"📋 任务: {task_description}")
        if input_files:
            print(f"📁 输入文件: {input_files}")
        else:
            print("📁 无输入文件")
        print("=" * 60)
        
        proxy.start_nano_code_batch(task_description, input_files)
                
    except KeyboardInterrupt:
        print("\n👋 程序被中断")
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
