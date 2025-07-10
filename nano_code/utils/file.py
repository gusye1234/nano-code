import os
import mimetypes

mimetypes.init()

TEXT_EXT = {
    ".md",
    ".txt",
    ".py",
    ".js",
    ".css",
    ".go",
    ".java",
    ".php",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".html",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".conf",
    ".cfg",
    ".log",
    ".csv",
    ".tsv",
    ".xml",
    ".sql",
    ".mdx",
}
SPECIAL_FILE_NAME = {
    ".gitignore",
}


def mime_file_type(file_path: str) -> str:
    return mimetypes.guess_type(file_path, strict=False)[0]


def get_file_extname(file_path: str):
    return os.path.splitext(file_path)[1]


def get_filename(file_path: str):
    return os.path.basename(file_path)


def is_text_file(file_path: str) -> tuple[bool, str]:
    """
    Use python-magic to determine if a file is text-based
    Returns: (is_text, mime_type)
    """
    # Get MIME type
    mime_type = mime_file_type(file_path)
    if mime_type is None:
        ext = get_file_extname(file_path)
        if ext in TEXT_EXT:
            return True, ext
        if ext.strip() != "":
            return False, ext

        file_name = get_filename(file_path)
        if file_name in SPECIAL_FILE_NAME:
            return True, file_name
        return False, file_name

    # Text file patterns
    text_mime_types = [
        "text/",
        "application/json",
        "application/xml",
        "application/javascript",
        "application/x-sh",
        "application/x-python",
    ]

    is_text = any(mime_type.startswith(pattern) for pattern in text_mime_types)

    return is_text, mime_type
