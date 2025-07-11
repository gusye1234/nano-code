<div align="center">
  <picture>
    <img alt="Shows the nano-code logo" src="./assets/logo.png">
  </picture>
  <h1>nano-code</h1>
	<p>
    <strong>
      A tiny agent in your terminal
    </strong>
  </p>
  <p>
    <code>uvx nano-code@latest</code>
  </p>
  <p>
    <a href="https://pypi.org/project/nano-code/">
      <img src="https://img.shields.io/pypi/v/nano-code.svg">
    </a>
  </p>
</div>







`nano-code` is a **tiny, batteries-included code-assistant** written in Python.  Inspired by Google’s *Gemini Code*, it lets you spin up an interactive CLI agent powered by OpenAI (or any compatible) LLM and a growing toolbox of actions such as reading files, listing directories, searching text and more.

The project aims to be **small enough to grok in one sitting** yet **powerful enough to be genuinely useful** when navigating or refactoring real-world codebases.

---

## ✨ Features

* ⚡ **Agent CLI** – run `nano-code` and start chatting immediately.
* 🛠 **Basic Tools** – easily add new tools.  Out-of-the-box you get:
  * `list_dir`, `find_files`, `read_file`, `write_file`, `search_text` …
  * `add_tasks` for quick TODO-list capture.
* 🧠 **Session memory** – every run stores context (working dir, conversation, cost tracking).
* 🔌 **Pluggable LLM** – ships with an OpenAI client but the design allows dropping in other providers.

---

## 🚀 Installation

We recommend the blazingly fast [uv](https://github.com/astral-sh/uv) package manager, but classic `pip` works too.

```bash
# 1. Clone the repo (optional – the package can also live on PyPI later)
git clone https://github.com/gusye1234/nano-code.git
cd nano-code

# 2. Install (requires Python ≥ 3.11)
uv sync

# or for editable dev installs (includes test dependencies)
uv pip install -e '.[dev]'

# fallback (slower) – replace `uv pip` with classic pip if you don't have uv
```

Make sure you have an OpenAI-compatible API key in your environment:

```bash
export OPENAI_API_KEY="sk-..."
# Optional – point to an OpenAI-compatible endpoint
export LLM_BASE_URL="https://api.openai.com/v1"
```

## ⚙️ Configuration

nano-code supports configuration via environment variables and an optional config file. You must provide an OpenAI-compatible API key, and can customize the LLM endpoint or other defaults if desired.

### Option 1: Environment variables (recommended for quickstart)

### Option 2: config.json file

You can optionally create a config file at:

```
~/.nano_code/config.json
```

Where `~` is your home directory (e.g., `/home/yourname/.nano_code/config.json` on Linux/macOS, or `C:\Users\yourname\.nano_code\config.json` on Windows).

Example contents:
```json
{
  "llm_api_key": "sk-...",
  "llm_base_url": "https://api.openai.com/v1",
  "llm_main_model": "gpt-4.1"
}
```
- Any keys matching the Env class (see `nano_code/env.py`) are supported.
- File-based config takes effect if present, otherwise environment variables are used as fallback.

---

## 🏃‍♀️ Quickstart

```bash
uvx nano-code
```
---

## 🗂 Project structure

```
nano-code/
├── nano_code/                 # Library package
│   ├── agent/                 # Agent implementations (interactive / non-interactive)
│   ├── agent_tool/            # Tool registry & concrete tools
│   │   ├── os_tool/           # File-system helpers (list_dir, read_file, ...)
│   │   └── util_tool/         # Misc utilities (add_tasks)
│   ├── core/                  # Session handling, cost tracking
│   ├── llm/                   # LLM client abstraction & OpenAI driver
│   ├── utils/                 # Shared helpers (logger, file paths)
│   ├── constants.py           # Global paths & limits
│   ├── env.py                 # Runtime configuration loader
│   └── __main__.py            # CLI entry-point (`python -m nano_code`)
├── tests/                     # Pytest suite exercising tools & flows
├── pyproject.toml             # Project metadata / dependencies
└── README.md                  # ← You are here
```

---

## 🤝 Contributing

Pull requests are welcome!  The codebase is intentionally small – feel free to add new tools, improve docs or extend test coverage.  For larger changes, please open an issue first to discuss what you would like to change.

```bash
# run the tests
pytest -q
```

---

## 📜 License

This project is licensed under the MIT License.  See `LICENSE` for details.