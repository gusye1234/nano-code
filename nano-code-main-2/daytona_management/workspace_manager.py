from daytona_sdk.common.process import SessionExecuteRequest
from .config import PathConfig


class WorkspaceManager:
    
    def __init__(self, sandbox):
        self.sandbox = sandbox
    
    def setup_secure_workspace(self, session_id: str):
        
        setup_commands = [
            f"mkdir -p {PathConfig.SYSTEM_DIR} {PathConfig.DOWNLOAD_DIR} {PathConfig.TMP_DIR}",
            
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
    
    def ensure_session(self, session_id_base: str) -> str:
        """
        幂等创建会话，如果冲突则自动追加数字后缀
        Args:
            session_id_base (str): 基础会话名称
        Returns:
            str: 最终创建成功的会话ID
        """
        # 先尝试基础名称
        try:
            self.create_session(session_id_base)
            return session_id_base
        except Exception as e:
            error_msg = str(e).lower()
            # 判断是否为"已存在/冲突"类错误
            conflict_keywords = ['exist', 'already', '409', 'conflict', 'duplicate']
            if not any(keyword in error_msg for keyword in conflict_keywords):
                # 非冲突错误，直接抛出
                raise
        
        # 冲突情况：尝试带数字后缀的名称
        max_attempts = 10
        for i in range(1, max_attempts + 1):
            session_id = f"{session_id_base}{i}"
            try:
                self.create_session(session_id)
                print(f"💡 创建会话: {session_id} (基础名称已占用)")
                return session_id
            except Exception as e:
                error_msg = str(e).lower()
                # 同样判断冲突类型
                if not any(keyword in error_msg for keyword in conflict_keywords):
                    # 非冲突错误，直接抛出
                    raise
                # 冲突则继续尝试下一个数字
                continue
        
        # 超过最大尝试次数
        raise Exception(f"无法创建会话：已尝试 {session_id_base} 到 {session_id_base}{max_attempts}")
    
    def delete_session(self, session_id: str):
        """删除工作会话"""
        try:
            self.sandbox.process.delete_session(session_id)
            print("🧹 会话已清理")
        except:
            pass