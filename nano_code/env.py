import os
import logging
import dataclasses
import json
from dataclasses import dataclass
from .utils.logger import SessionLogger
from .constants import NANO_CODE_DIR


class TerminalDisplay:
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    END = "\033[0m"


LOG = logging.getLogger("nano-code")
LOG.setLevel(logging.INFO)
formatter = logging.Formatter(
    f"{TerminalDisplay.BOLD}{TerminalDisplay.BLUE}%(name)s |{TerminalDisplay.END}  %(levelname)s - %(asctime)s  -  %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
LOG.addHandler(handler)


@dataclass
class Env:
    llm_api_key: str = os.getenv("OPENAI_API_KEY")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
    llm_default_query: str = None
    llm_default_header: str = None

    llm_main_model: str = os.getenv("LLM_MAIN_MODEL", "gpt-4.1")

    def __post_init__(self):
        if not self.llm_api_key:
            raise ValueError("llm_api_key is not set")

    @classmethod
    def from_home(cls):
        path = os.path.join(NANO_CODE_DIR, "config.json")
        if not os.path.exists(path):
            return cls()
        with open(path, "r") as f:
            overwrite_config = json.load(f)
        fields = {field.name for field in dataclasses.fields(cls)}
        filtered_config = {k: v for k, v in overwrite_config.items() if k in fields}
        LOG.info(f"Loaded config from {path}: {filtered_config}")
        return cls(**filtered_config)
