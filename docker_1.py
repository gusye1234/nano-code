import asyncio
import os
import sys
import signal
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any


class AutoSandboxManager:

    def __init__(self):
        """初始化自动沙盒管理器"""
        # 容器配置
        self.container_name = "nano-code-sandbox-container"
        self.input_dir = "/workspace/input" 
        self.output_dir = "/workspace/output"
        self.workspace_dir = "/workspace"
        self.temp_dir = "/workspace/temp"
        
        # 本地工作目录配置
        self.base_dir = Path.home() / "Desktop" / "SandboxWork"
        self.upload_dir = self.base_dir / "upload"
        self.download_dir = self.base_dir / "download"
        

        self.supported_extensions = {
            '.py',      # Python源码
            '.txt',     # 文本文件
            '.csv',     # CSV数据文件
            '.json',    # JSON数据文件
            '.yaml',    # YAML配置文件
            '.yml',     # YAML配置文件
            '.toml',    # TOML配置文件
            '.ini',     # INI配置文件
            '.conf',    # 配置文件
            '.cfg',     # 配置文件
            '.log',     # 日志文件
            '.md',      # Markdown文档
        }
        
        # 初始化工作环境
        self.setup_directories()
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self.cleanup_handler)
        signal.signal(signal.SIGTERM, self.cleanup_handler)
        
    
    def setup_directories(self) -> None:

        # 创建基础目录
        self.base_dir.mkdir(exist_ok=True)
        self.upload_dir.mkdir(exist_ok=True) 
        self.download_dir.mkdir(exist_ok=True)
        
        print()
        print("=" * 50)
        print("=" * 50)

        
        print(f"📁 工作目录已准备: {self.base_dir}")
        print(f"📤 上传目录: {self.upload_dir}")
        print(f"📥 下载目录: {self.download_dir}")
        
        # 检查待处理文件
        upload_files = [f for f in self.upload_dir.glob('*') if f.is_file()]
        if upload_files:
            print(f"📋 发现 {len(upload_files)} 个待分析文件")
    
    async def check_container_ready(self) -> bool:
        
        try:
            status = await self.get_container_status()
            
            if status.get('error'):
                print("⚠️  沙盒容器不存在，正在创建...")
                return await self._create_new_container()
            elif not status.get('running'):
                print("⚠️  沙盒容器已停止，正在启动...")
                return await self._start_existing_container()
            else:
                print("✅ 沙盒容器运行正常")
                await self._ensure_container_directories()
                return True
                
        except Exception as e:
            print(f"❌ 容器状态检查失败: {e}")
            return False
    
    async def _create_new_container(self) -> bool:

        try:
            print("🐳 创建新的沙盒容器...")
            
            # 删除可能存在的同名容器
            try:
                await self._run_command([
                    "docker", "rm", "-f", self.container_name
                ], "删除旧容器")
            except:
                pass
            
            # 创建新容器
            await self._run_command([
                "docker", "run", "-d", 
                "--name", self.container_name,
                "--entrypoint", "/bin/bash", 
                "filletofish0405/nano-code-sandbox:multiarch",
                "-c", "while true; do sleep 30; done"
            ], "创建新容器")
            
            await asyncio.sleep(2)
            await self._ensure_container_directories()
            
            print("✅ 新沙盒容器创建成功")
            return True
            
        except Exception as e:
            print(f"❌ 创建容器失败: {e}")
            return False
    
    async def _start_existing_container(self) -> bool:

        try:
            await self._run_command([
                "docker", "start", self.container_name
            ], "启动容器")
            
            await asyncio.sleep(2)
            await self._ensure_container_directories()
            
            print("✅ 沙盒容器启动成功")
            return True
            
        except Exception as e:
            print(f"❌ 启动容器失败: {e}")
            return False
    
    async def _ensure_container_directories(self) -> None:

        try:
            # 创建工作目录结构
            await self._run_command([
                "docker", "exec", "-u", "root", self.container_name,
                "mkdir", "-p", 
                self.input_dir, self.output_dir, self.temp_dir
            ], "创建工作目录结构")
            
            # 设置权限
            await self._run_command([
                "docker", "exec", "-u", "root", self.container_name,
                "chown", "-R", "sandboxuser:sandboxuser", "/workspace"
            ], "设置目录权限")
            
        except Exception as e:
            print(f"⚠️  目录结构检查失败: {e}")
    
    async def upload_files(self) -> List[str]:
        """自动上传 upload 目录中的所有文件到沙盒"""
        upload_files = [f for f in self.upload_dir.glob('*') if f.is_file()]
        
        if not upload_files:
            print("📤 upload目录为空，跳过文件上传")
            return []
        
        print(f"📤 发现 {len(upload_files)} 个文件，开始上传...")
        
        # 清空沙盒输入目录
        try:
            await self._run_command([
                "docker", "exec", self.container_name, "rm", "-rf", f"{self.input_dir}/*"
            ], "清空输入目录")
        except Exception as e:
            print(f"⚠️  清理沙盒目录失败: {e}")
        
        uploaded_files = []
        failed_files = []
        
        for file_path in upload_files:
            try:
                # 文件验证
                if not self._is_supported_file(file_path):
                    print(f"  ⚠️  跳过不支持的文件类型: {file_path.name}")
                    failed_files.append(file_path.name)
                    continue
                
                # 大小检查
                file_size = file_path.stat().st_size
                if file_size > 100 * 1024 * 1024:  # 100MB
                    print(f"  ❌ 文件过大 (>{file_size/1024/1024:.1f}MB): {file_path.name}")
                    failed_files.append(file_path.name)
                    continue
                
                # 文件名安全检查
                if any(char in file_path.name for char in ['..', '/', '\\', '|', '&', ';', '$', '`']):
                    print(f"  ❌ 文件名包含危险字符: {file_path.name}")
                    failed_files.append(file_path.name)
                    continue
                
                # 执行上传
                container_path = f"{self.input_dir}/{file_path.name}"
                await self._run_command([
                    "docker", "cp", str(file_path), f"{self.container_name}:{container_path}"
                ], f"上传文件 {file_path.name}")
                
                uploaded_files.append(file_path.name)
                file_size_mb = file_size / 1024 / 1024
                print(f"  ✅ {file_path.name} ({file_size_mb:.1f}MB)")
                
            except Exception as e:
                print(f"  ❌ 上传失败 {file_path.name}: {e}")
                failed_files.append(file_path.name)
        
        if uploaded_files:
            print(f"📤 成功上传 {len(uploaded_files)} 个文件到沙盒")
        
        if failed_files:
            print(f"⚠️  {len(failed_files)} 个文件上传失败")
        
        return uploaded_files
    
    def _is_supported_file(self, file_path: Path) -> bool:
        """检查文件是否为支持的类型"""
        return file_path.suffix.lower() in self.supported_extensions
    
    async def download_results(self) -> None:
        """自动下载分析结果文件到本地"""
        try:
            # 创建带时间戳的下载目录
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            session_dir = self.download_dir / f"session_{timestamp}"
            session_dir.mkdir(exist_ok=True)
            
            print(f"📥 开始下载结果到: {session_dir}")
            
            # 收集需要下载的文件
            all_files = []
            
            # 扫描 /workspace 目录
            workspace_files = await self._find_files_in_container("/workspace", max_depth=1)
            all_files.extend(workspace_files)
            
            # 扫描 /sandbox/output 目录
            output_files = await self._find_files_in_container(self.output_dir)
            all_files.extend(output_files)
            
            if not all_files:
                print("📥 没有找到需要下载的结果文件")
                return
            
            print(f"📋 发现 {len(all_files)} 个结果文件，开始下载...")
            
            downloaded_count = 0
            download_errors = []
            
            for file_path in all_files:
                try:
                    if not file_path.strip():
                        continue
                    
                    filename = os.path.basename(file_path)
                    local_path = session_dir / filename
                    
                    # 处理重名文件
                    counter = 1
                    original_name = local_path.stem
                    original_suffix = local_path.suffix
                    while local_path.exists():
                        local_path = session_dir / f"{original_name}_{counter}{original_suffix}"
                        counter += 1
                    
                    # 下载文件
                    await self._run_command([
                        "docker", "cp", f"{self.container_name}:{file_path}", str(local_path)
                    ], f"下载 {filename}")
                    
                    if local_path.exists():
                        file_size = local_path.stat().st_size
                        print(f" {filename} ({file_size:,} bytes)")
                        downloaded_count += 1
                    
                except Exception as e:
                    error_msg = f"下载失败 {file_path}: {e}"
                    print(f"  ❌ {error_msg}")
                    download_errors.append(error_msg)
            
            if downloaded_count > 0:
                print(f"📥 ✅ 成功下载 {downloaded_count} 个文件")
                
                # 在macOS中自动打开结果目录
                try:
                    await self._run_command(["open", str(session_dir)], "打开结果目录")
                    print(f"📂 已自动打开结果目录")
                except:
                    print(f"📂 结果保存在: {session_dir}")
            
            if download_errors:
                print(f"⚠️  {len(download_errors)} 个文件下载失败")
            
            # 生成下载报告
            # await self._generate_download_report(session_dir, downloaded_count, download_errors)
            
        except Exception as e:
            print(f"❌ 下载结果失败: {e}")
    
    async def _find_files_in_container(self, directory: str, max_depth: Optional[int] = None) -> List[str]:
        """在容器中查找文件"""
        try:
            cmd = ["docker", "exec", self.container_name, "find", directory, "-type", "f"]
            
            if max_depth is not None:
                cmd.extend(["-maxdepth", str(max_depth)])
            
            result = await self._run_command(cmd, f"搜索 {directory}")
            
            if result.stdout.strip():
                return [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
            else:
                return []
                
        except Exception:
            return []
    
    
#     async def _generate_download_report(self, session_dir: Path, downloaded_count: int, errors: List[str]) -> None:
#         """生成下载报告文件"""
#         try:
#             report_path = session_dir / "download_report.txt"
            
#             report_content = f"""nano-code 沙盒分析结果下载报告
# ====================================

# 会话时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 下载目录: {session_dir}
# 成功下载: {downloaded_count} 个文件

# """
            
#             if errors:
#                 report_content += f"下载错误 ({len(errors)} 个):\n"
#                 for error in errors:
#                     report_content += f"  - {error}\n"
#                 report_content += "\n"
            
#             # 列出下载的文件
#             downloaded_files = [f for f in session_dir.iterdir() if f.is_file() and f.name != "download_report.txt"]
#             if downloaded_files:
#                 report_content += "下载的文件列表:\n"
#                 for file_path in sorted(downloaded_files):
#                     file_size = file_path.stat().st_size
#                     report_content += f"  - {file_path.name} ({file_size:,} bytes)\n"
            
#             with open(report_path, 'w', encoding='utf-8') as f:
#                 f.write(report_content)
                
#         except Exception as e:
#             print(f"⚠️  生成下载报告失败: {e}")
    
    async def get_container_status(self) -> dict:
        """获取容器状态信息"""
        try:
            cmd = ["docker", "inspect", self.container_name]
            result = await self._run_command(cmd, "获取容器状态")
            
            container_info = json.loads(result.stdout)[0]
            
            return {
                'running': container_info['State']['Running'],
                'status': container_info['State']['Status'],
                'created': container_info['Created'],
                'image': container_info['Config']['Image']
            }
        except Exception as e:
            return {'error': str(e)}
    
    async def _run_command(self, cmd: List[str], description: str = "") -> Any:
        """执行系统命令的通用方法"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            result = type('Result', (), {
                'returncode': process.returncode,
                'stdout': stdout.decode('utf-8', errors='replace'),
                'stderr': stderr.decode('utf-8', errors='replace')
            })()
            
            if process.returncode != 0:
                error_msg = f"命令执行失败"
                if description:
                    error_msg += f" ({description})"
                error_msg += f": {' '.join(cmd)}\n"
                if result.stderr:
                    error_msg += f"错误输出: {result.stderr}"
                raise RuntimeError(error_msg)
            
            return result
            
        except Exception as e:
            if not isinstance(e, RuntimeError):
                error_msg = f"命令执行异常"
                if description:
                    error_msg += f" ({description})"
                error_msg += f": {str(e)}"
                raise RuntimeError(error_msg)
            else:
                raise
    
    def _get_api_config(self) -> tuple[str, str]:
        """从宿主机读取API配置"""
        import json
        
        # 尝试从配置文件读取
        config_path = Path.home() / ".nano_code" / "config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                api_key = config.get('llm_api_key', '')
                base_url = config.get('llm_base_url', 'https://api.openai.com/v1')
                
                if api_key:
                    print(f"📋 使用配置文件: {config_path}")
                    return api_key, base_url
            except Exception as e:
                print(f"⚠️  读取配置文件失败: {e}")
        
        # 尝试从环境变量读取
        api_key = os.getenv('OPENAI_API_KEY', '')
        base_url = os.getenv('LLM_BASE_URL', 'https://api.openai.com/v1')
        
        if api_key:
            print("📋 使用环境变量配置")
            return api_key, base_url
        
        # 配置未找到
        print("❌ 未找到API密钥配置!")
        print("💡 请设置以下配置之一:")
        print(f"   1. 创建配置文件: {config_path}")
        print("      内容: {\"llm_api_key\": \"sk-your-key\", \"llm_base_url\": \"https://api.openai.com/v1\"}")
        print("   2. 设置环境变量: export OPENAI_API_KEY=sk-your-key")
        raise RuntimeError("API配置未设置")
    
    def cleanup_handler(self, signum: int, frame) -> None:
        """信号处理器 - 处理程序退出时的清理工作"""
        print("\n🔄 检测到退出信号，正在自动下载结果...")
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.download_results())
            loop.close()
            
            print("👋 感谢使用 nano-code 沙盒系统，再见！")
            
        except Exception as e:
            print(f"❌ 自动下载失败: {e}")
            print("💡 你可以稍后手动运行下载脚本获取结果")
        
        finally:
            sys.exit(0)
    
    async def start_nano_code(self) -> None:
        """启动 nano-code 交互界面"""
        print("🚀 启动 nano-code 沙盒环境...")
        print("💡 提示：使用 Ctrl+C 退出时会自动下载结果\n")
        
        try:
            # 从宿主机读取API配置
            api_key, base_url = self._get_api_config()
            
            # 构建docker exec命令，传入环境变量
            docker_cmd = [
                "docker", "exec", "-it",
                "-e", f"OPENAI_API_KEY={api_key}",
                "-e", f"LLM_BASE_URL={base_url}",
                self.container_name, 
                "python3", "-m", "nano_code"
            ]
            
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
                stdin=None,
                stdout=None,
                stderr=None
            )
            
            returncode = await process.wait()
            
            if returncode == 0:
                print("\n✅ nano-code 正常退出")
            else:
                print(f"\n⚠️  nano-code 退出，返回码: {returncode}")
            
        except KeyboardInterrupt:
            print("\n🔄 用户中断，准备退出...")
            raise
        except Exception as e:
            print(f"\n❌ nano-code 启动失败: {e}")
            raise


async def main():

    
    manager = AutoSandboxManager()
    
    try:
        # 检查沙盒容器
        print("=" * 50)
        if not await manager.check_container_ready():
            print("❌ 沙盒环境准备失败，请检查Docker环境")
            return
        
        # 自动上传文件
        print("=" * 50)
        uploaded_files = await manager.upload_files()
        
        # 显示使用提示
        if uploaded_files:
            print(f"\n🎯 已上传的文件可以在nano-code中通过以下路径访问:")
            for filename in uploaded_files:
                print(f"   📄 {manager.input_dir}/{filename}")
            
        else:
            print(f"\n💡 没有发现待分析文件")

        
        print()
        print(f"   - 使用 Ctrl+C 退出时会自动下载分析结果")
        print(f"   - 结果将保存到 {manager.download_dir}")
        print("=" * 50)
        
        # 启动nano-code
        await manager.start_nano_code()
        
        # 正常退出时下载结果
        print("\n🔄 准备下载分析结果...")
        await manager.download_results()
        
    except KeyboardInterrupt:
        print("\n🔄 用户中断，正在自动下载结果...")
        try:
            await manager.download_results()
        except Exception as e:
            print(f"❌ 自动下载失败: {e}")
        
    except Exception as e:
        print(f"\n❌ 系统运行出错: {e}")
        print("🔍 详细错误信息：")
        import traceback
        traceback.print_exc()

        
    finally:
        print(f"\n📊 会话结束统计：")
        print(f"   工作目录: {manager.base_dir}")
        print(f"   容器名称: {manager.container_name}")
        print(f"   结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    """程序入口点"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n💥 程序启动失败: {e}")
        sys.exit(1)





        