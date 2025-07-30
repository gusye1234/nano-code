#!/usr/bin/env python3
"""
超简化的 Daytona nano-code 代理
核心理念：透明的I/O转发，nano-code在沙盒中原生运行
"""

import asyncio
import os
import sys
import signal
import json
from pathlib import Path
from daytona_sdk import Daytona, DaytonaConfig
from daytona_sdk.common.daytona import CreateSandboxFromImageParams



class NanoCodeProxy:
    
    def __init__(self):
        self.daytona_client = None
        self.sandbox = None
        self.running = True
        
        signal.signal(signal.SIGINT, self._cleanup_and_exit)
        signal.signal(signal.SIGTERM, self._cleanup_and_exit)
    
    def setup_daytona(self):
        """设置Daytona连接"""
        api_key = "dtn_d372300f7c47e669647ebba0071f89b4cb4ad801622c40144774d33187530e95"
        api_url = "https://app.daytona.io/api"
        
        config = DaytonaConfig(api_key=api_key, api_url=api_url)
        self.daytona_client = Daytona(config)
        
        create_params = CreateSandboxFromImageParams(
            image="filletofish0405/nano-code-sandbox:multiarch"
        )
        self.sandbox = self.daytona_client.create(create_params)
        
        if not self.sandbox:
            raise Exception("沙盒创建失败")

    def get_sandbox_info(self):
        sandbox_id = self.sandbox.id

        print(f"沙盒ID: {sandbox_id}")
    
    def _get_api_config(self) -> tuple[str, str]:
        """获取LLM API配置"""
        # 尝试从配置文件读取
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

    def start_nano_code(self):
        """在沙盒中启动nano-code"""
        print("🚀 在沙盒中启动nano-code...")
        
        # 获取API配置
        api_key, base_url = self._get_api_config()
        
        # 创建交互式会话
        session_id = "nano-code-session"
        try:
            self.sandbox.process.create_session(session_id)

            self.session_info_debug()

            
            # 设置环境变量
            env_commands = f'''
            export OPENAI_API_KEY="{api_key}" && \
            export LLM_BASE_URL="{base_url}" && \
            export PYTHONPATH="/workspace:$PYTHONPATH" && \
            cd /workspace && \
            echo "环境配置完成"
            '''
            
            for cmd in env_commands:
                from daytona_sdk.common.process import SessionExecuteRequest
                req = SessionExecuteRequest(command=cmd)
                self.sandbox.process.execute_session_command(session_id, req)
            
            # 启动nano-code

            steps = [
                "cd /workspace",
                "ls -la",
                "python -m nano_code"
            ]
            for step in steps:
                req = SessionExecuteRequest(command=step)
                result = self.sandbox.process.execute_session_command(session_id, req)
                print(result.output)


            self.session_info_debug()
            
        except KeyboardInterrupt:
            print("\n用户中断")
        except Exception as e:
            print(f"nano-code运行错误: {e}")
        finally:
            # 清理会话
            try:
                self.sandbox.process.delete_session(session_id)
            except:
                pass

    def session_info_debug(self):

        session_id = "nano-code-session"
        try:
            session = self.sandbox.process.get_session(session_id)
            sessions_list = self.sandbox.process.list_sessions()
            
            print(f"\n=== 会话调试信息 ===")
            print(f"当前会话ID: {session_id}")
            print(f"所有会话数量: {len(sessions_list)}")
            
            # 检查 commands 的具体内容
            print(f"commands 类型: {type(session.commands)}")
            print(f"commands 内容: {session.commands}")
            
            if session.commands:
                print(f"会话命令数量: {len(session.commands)}")
                print("执行的命令列表:")
                for i, cmd in enumerate(session.commands, 1):
                    print(f"  {i}. {cmd}")
            else:
                print("commands 为空或 None")

        except Exception as e:
            print(f"调试信息获取失败: {e}")

    
    def _cleanup_and_exit(self, signum, frame):
        """清理并退出"""
        print(f"\n接收到信号 {signum}，清理资源...")
        
        if self.sandbox and self.daytona_client:
            try:
                self.daytona_client.delete(self.sandbox)
                print("沙盒已清理")
            except:
                pass
        
        sys.exit(0)
    
    def run(self):
        """运行代理"""
        print("🔧 设置Daytona连接...")
        self.setup_daytona()
        print(f"✅ 沙盒创建成功: {self.sandbox.id}")
        
        print("=" * 50)
        print("🎯 准备启动nano-code...")
        print("💡 nano-code将在沙盒中完整运行")
        print("💡 您可以直接与AI助手交互")
        print("💡 环境变量将自动配置")
        print("=" * 50)
        
        self.get_sandbox_info()


        # 启动nano-code（包含环境配置）
        self.start_nano_code()
        
        # 清理
        #if self.sandbox and self.daytona_client:
            #self.daytona_client.delete(self.sandbox)


def main():
    """主函数"""
    try:
        proxy = NanoCodeProxy()
        proxy.run()
    except KeyboardInterrupt:
        print("\n👋 程序被中断")
    except Exception as e:
        print(f"❌ 运行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
