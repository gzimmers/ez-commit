"""
Configuration management for ez-commit
"""

import os
import yaml
from pathlib import Path
import platform

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that generates clear and concise git commit messages.
Follow these guidelines:
- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters
- Provide more detailed explanation in subsequent paragraphs if necessary
- Reference relevant issue numbers if applicable
- Focus on the "what" and "why" of the changes, not the "how"
"""

DEFAULT_CONFIG = {
    "openai": {
        "api_key": "",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 500
    },
    "system_prompt": DEFAULT_SYSTEM_PROMPT
}

def get_config_dir() -> Path:
    """Get the appropriate config directory based on the operating system."""
    if platform.system() == "Windows":
        base_dir = os.environ.get("APPDATA")
        return Path(base_dir) / "ez-commit"
    else:
        # Linux/Mac: Use XDG_CONFIG_HOME or fallback to ~/.config
        base_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return Path(base_dir) / "ez-commit"

def get_config_file() -> Path:
    """Get the path to the config file."""
    config_dir = get_config_dir()
    return config_dir / "config.yaml"

def ensure_config_exists():
    """Create default config file if it doesn't exist."""
    config_file = get_config_file()
    if not config_file.exists():
        config_file.parent.mkdir(parents=True, exist_ok=True)
        save_config(DEFAULT_CONFIG)

def load_config() -> dict:
    """Load configuration from file."""
    ensure_config_exists()
    config_file = get_config_file()
    
    with open(config_file, 'r') as f:
        config = yaml.safe_load(f)
    
    # Merge with defaults to ensure all fields exist
    merged_config = DEFAULT_CONFIG.copy()
    merged_config.update(config or {})
    return merged_config

def save_config(config: dict):
    """Save configuration to file."""
    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w') as f:
        yaml.safe_dump(config, f, default_flow_style=False)

def get_openai_api_key() -> str:
    """Get OpenAI API key from config or environment variable."""
    config = load_config()
    return os.environ.get("OPENAI_API_KEY") or config["openai"]["api_key"]

def validate_config():
    """Validate that the configuration is valid and complete."""
    config = load_config()
    api_key = get_openai_api_key()
    
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Either set it in the config file "
            "or set the OPENAI_API_KEY environment variable."
        )
    
    return config
