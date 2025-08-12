from daytona_sdk.common.process import SessionExecuteRequest
from .config import PathConfig


class WorkspaceManager:
    """工作区管理和环境设置"""
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
    
    def setup_secure_workspace(self, session_id: str):
        """设置安全工作区目录结构"""
        print("🔒 设置工作区...")
        
        setup_commands = [
            f"mkdir -p {PathConfig.SYSTEM_DIR} {PathConfig.UPLOAD_DIR} {PathConfig.DOWNLOAD_DIR} {PathConfig.TMP_DIR}",
            
            f"mv {PathConfig.WORKSPACE_ROOT}/nanocode1 {PathConfig.SYSTEM_DIR}/ 2>/dev/null || true",
            
            f"chmod -R 555 {PathConfig.SYSTEM_DIR}/ 2>/dev/null || true",
        ]
        
        for cmd in setup_commands:
            try:
                req = SessionExecuteRequest(command=cmd)
                result = self.sandbox.process.execute_session_command(session_id, req)
                
                if result is None:
                    print(f"⚠️  命令执行失败（返回None）: {cmd}")
                    continue
                    
                if result.exit_code != 0 and "No such file" not in str(result.output):
                    print(f"⚠️  设置命令失败: {cmd}")
            except Exception as e:
                print(f"⚠️  执行命令异常: {cmd} - {e}")
    
    def copy_files_to_workspace(self, session_id: str, remote_files: list) -> list:
        """将上传的文件复制到工作区临时目录"""
        tmp_files = []
        
        if not remote_files:
            return tmp_files
        
        for upload_file in remote_files:
            filename = upload_file.split('/')[-1]
            tmp_file = f"{PathConfig.TMP_DIR}/{filename}"
            copy_cmd = f"cp '{upload_file}' '{tmp_file}'"
            req = SessionExecuteRequest(command=copy_cmd)
            result = self.sandbox.process.execute_session_command(session_id, req)
            
            if result.exit_code == 0:
                tmp_files.append(tmp_file)
                print(f"✅ 复制文件: {filename}")
            else:
                print(f"⚠️  复制失败: {filename}")
        
        return tmp_files
    
    def create_session(self, session_id: str):
        """创建工作会话"""
        self.sandbox.process.create_session(session_id)
    
    def delete_session(self, session_id: str):
        """删除工作会话"""
        try:
            self.sandbox.process.delete_session(session_id)
            print("🧹 会话已清理")
        except:
            pass