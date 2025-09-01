import os

USER_HOME = os.path.expanduser("~")
NANO_CODE_DIR = os.path.join(os.path.expanduser("~"), ".nano_code")
NANO_CODE_TEMP_DIR = os.path.join(NANO_CODE_DIR, "temp")

MEMORY_FILE = "CODE.md"

MAX_READ_FILE_LINES = 20000
MAX_LINE_CHAR_LENGTH = 20000
MAX_FOR_LLM_TOOL_RETURN_TOKENS = 16000
