import sys
from pathlib import Path
from daytona_sdk import Daytona, DaytonaConfig
from daytona_sdk.common.process import SessionExecuteRequest
from daytona_sdk.common.daytona import CreateSandboxFromImageParams
from .config import DaytonaConfig as Config


class SandboxManager:
    """Daytona沙盒生命周期管理"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = None
        self.sandbox = None
    
    def create_sandbox(self):
        """创建Daytona沙盒"""
        print("📦 创建Daytona沙盒...")
        
        # 配置Daytona客户端
        daytona_config = DaytonaConfig(
            api_key=self.config.api_key, 
            api_url=self.config.api_url
        )
        self.client = Daytona(daytona_config)
        
        # 创建沙盒
        create_params = CreateSandboxFromImageParams(image=self.config.base_image)
        self.sandbox = self.client.create(create_params)
        
        if not self.sandbox:
            raise Exception("沙盒创建失败")
        
        print(f"✅ 沙盒创建成功: {self.sandbox.id}")
        return self.sandbox
    
    def setup_environment(self):
        """设置沙盒环境"""
        if not self.sandbox:
            raise RuntimeError("沙盒未创建，请先调用 create_sandbox()")
        
        print("🔧 设置nano-code环境...")
        
        # 上传代码
        self._upload_nanocode()
        
        # 安装依赖
        self._install_dependencies()
        
        print("🎉 环境设置完成！")
    
    def _upload_nanocode(self):
        """上传本地nano-code代码"""
        # 上传nanocode1目录
        local_nanocode_path = Path(__file__).parent.parent / "nanocode1"
        if not local_nanocode_path.exists():
            raise Exception(f"本地nano-code路径不存在: {local_nanocode_path}")
        
        print("📤 上传nano-code代码...")
        self._upload_directory_recursive(local_nanocode_path, "/workspace/nanocode1")
        
        # 上传pyproject.toml
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, 'rb') as f:
                content = f.read()
            self.sandbox.fs.upload_file(content, "/workspace/pyproject.toml")
            print("📤 上传pyproject.toml")
        
        # 创建临时README.md
        readme_content = "# nanocode1\nAI coding assistant"
        self.sandbox.fs.upload_file(readme_content.encode(), "/workspace/README.md")
        print("📤 创建临时README.md")
    
    def _upload_directory_recursive(self, local_dir: Path, remote_dir: str):
        """递归上传目录"""
        from .config import PathConfig
        
        print(f"📁 上传目录: {local_dir} → {remote_dir}")
        
        for item in local_dir.rglob("*"):
            if item.is_file():
                # 跳过不需要的文件
                if any(skip in str(item) for skip in PathConfig.SKIP_PATTERNS):
                    continue
                
                # 计算相对路径
                relative_path = item.relative_to(local_dir)
                remote_path = f"{remote_dir}/{relative_path}".replace("\\", "/")
                
                try:
                    with open(item, 'rb') as f:
                        content = f.read()
                    self.sandbox.fs.upload_file(content, remote_path)
                    print(f"  ✅ {relative_path}")
                except Exception as e:
                    print(f"  ❌ 上传失败 {relative_path}: {e}")
    
    def _install_dependencies(self):
        """安装依赖并设置环境"""
        setup_session = "setup-session"
        try:
            self.sandbox.process.create_session(setup_session)
            
            setup_commands = [
                "apt-get update",
                "apt-get install -y git curl build-essential",
                "pip install --no-cache-dir rich>=14.0.0 tiktoken>=0.9.0 openai>=1.92.2 gitignore-parser>=0.1.12",
                "cd /workspace && pip install --no-cache-dir -e . || echo '项目安装失败但依赖已安装'",
                "python -c 'import rich, tiktoken, openai; print(\"依赖包安装成功\")'",
                "python -c 'import sys; sys.path.insert(0, \"/workspace\"); import nanocode1; print(\"nano-code导入成功\")'",
            ]
            
            for cmd in setup_commands:
                print(f"🔄 执行: {cmd}")
                req = SessionExecuteRequest(command=cmd)
                result = self.sandbox.process.execute_session_command(setup_session, req)
                
                if result.exit_code != 0:
                    print(f"⚠️  命令执行失败: {cmd}")
                    print(f"错误输出: {result.output}")
                else:
                    print("✅ 命令执行成功")
            
            self.sandbox.process.delete_session(setup_session)
            
        except Exception as e:
            print(f"❌ 环境设置失败: {e}")
            try:
                self.sandbox.process.delete_session(setup_session)
            except:
                pass
            raise
    
    def destroy_sandbox(self):
        """销毁沙盒"""
        if self.sandbox and self.client:
            try:
                self.client.delete(self.sandbox)
                print("🧹 沙盒已清理")
            except Exception as e:
                print(f"清理沙盒失败: {e}")
        
        self.sandbox = None
        self.client = None