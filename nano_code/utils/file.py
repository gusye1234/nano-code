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
    ".tsx",
    ".jsx",
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
    ".coveragerc",
    ".env",
    ".env.local",
    ".env.development",
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


if __name__ == "__main__":
    print(
        is_text_file(
            "/Users/gustavoye/Desktop/learn_w/daytona/apps/api/src/app.module.ts"
        )
    )
