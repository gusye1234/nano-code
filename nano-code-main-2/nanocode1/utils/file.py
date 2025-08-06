import os
import mimetypes

mimetypes.init()

TEXT_EXT = {
    ".py",      # Python源码
    ".txt",     # 文本文件
    ".csv",     # CSV数据文件
    ".json",    # JSON数据文件
    ".yaml",    # YAML配置文件
    ".yml",     # YAML配置文件
    ".toml",    # TOML配置文件（Python项目常用）
    ".ini",     # INI配置文件
    ".conf",    # 配置文件
    ".cfg",     # 配置文件
    ".log",     # 日志文件
    ".md",      # Markdown文档
}
SPECIAL_FILE_NAME = {
    ".gitignore",     # Git忽略文件
    ".coveragerc",    # Python测试覆盖率配置
    ".env",           # 环境变量文件
    "requirements.txt", # Python依赖文件
    "setup.py",       # Python安装脚本
    "setup.cfg",      # Python配置
    "pyproject.toml", # Python项目配置
}


def mime_file_type(file_path: str) -> str:
    return mimetypes.guess_type(file_path, strict=False)[0]


def get_file_extname(file_path: str):
    return os.path.splitext(file_path)[1]


def get_filename(file_path: str):
    return os.path.basename(file_path)


def is_text_file(file_path: str) -> tuple[bool, str | None]:
    """
    Use python-magic to determine if a file is text-based
    Returns: (is_text, label/mime_type/extension)
    """
    # Get MIME type
    ext = get_file_extname(file_path)
    if ext in TEXT_EXT:
        return True, ext

    mime_type = mime_file_type(file_path)
    if mime_type is None:
        file_name = get_filename(file_path)
        if file_name in SPECIAL_FILE_NAME:
            return True, file_name
        # No mime and no special file, return False, None
        return False, None
    # Python相关的MIME类型
    text_mime_types = [
        "text/",
        "application/json",
        "application/x-python",
        "text/x-python",
    ]

    is_text = any(mime_type.startswith(pattern) for pattern in text_mime_types)

    return is_text, mime_type


if __name__ == "__main__":
    # 测试Python文件检测
    print(is_text_file("example.py"))
    print(is_text_file("data.csv"))
    print(is_text_file("config.json"))
