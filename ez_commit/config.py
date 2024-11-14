"""
Configuration management for ez-commit
"""

import os
import yaml
from pathlib import Path
import platform
from typing import Dict, Any

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that generates clear and concise git commit messages.
Follow these guidelines:
- Use the imperative mood ("Add feature" not "Added feature")
- Keep the first line under 50 characters and have it provide a general summary
- Reference relevant issue numbers if applicable, and if so start the commit message with the issue as the header.
- Focus on the "what" and "why" of the changes, not the "how"
- Be brief and concise, don't use excessive detail
"""

DEFAULT_CONFIG = {
    "openai": {
        "api_key": "",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 10000
    },
    "system_prompt": DEFAULT_SYSTEM_PROMPT
}

def deep_merge(source: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    for key, value in source.items():
        if key in destination:
            if isinstance(value, dict) and isinstance(destination[key], dict):
                destination[key] = deep_merge(value, destination[key])
            else:
                destination[key] = value
        else:
            destination[key] = value
    return destination

def validate_config_structure(config: Dict[str, Any]) -> None:
    """Validate the structure of the configuration."""
    required_keys = {
        "openai": {
            "api_key": str,
            "model": str,
            "temperature": (int, float),
            "max_tokens": int
        },
        "system_prompt": str
    }

    def validate_dict(config_dict: Dict[str, Any], required: Dict[str, Any], path: str = "") -> None:
        for key, value_type in required.items():
            if key not in config_dict:
                raise ValueError(f"Missing required configuration key: {path + key}")
            
            if isinstance(value_type, dict):
                if not isinstance(config_dict[key], dict):
                    raise ValueError(f"Invalid type for {path + key}: expected dict")
                validate_dict(config_dict[key], value_type, f"{path + key}.")
            else:
                if isinstance(value_type, tuple):
                    if not isinstance(config_dict[key], value_type):
                        raise ValueError(f"Invalid type for {path + key}: expected {value_type}")
                else:
                    if not isinstance(config_dict[key], value_type):
                        raise ValueError(f"Invalid type for {path + key}: expected {value_type.__name__}")

    validate_dict(config, required_keys)

    # Additional validation for specific values
    temp = config["openai"]["temperature"]
    if not (isinstance(temp, (int, float)) and 0 <= temp <= 1):
        raise ValueError("Temperature must be between 0.0 and 1.0")

    max_tokens = config["openai"]["max_tokens"]
    if not (isinstance(max_tokens, int) and max_tokens > 0):
        raise ValueError("max_tokens must be a positive integer")

def get_config_dir() -> Path:
    """Get the appropriate config directory based on the operating system."""
    if platform.system() == "Windows":
        base_dir = os.environ.get("APPDATA")
        if not base_dir:
            raise ValueError("APPDATA environment variable not found")
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

def reset_config() -> bool:
    """Reset configuration to default values."""
    try:
        save_config(DEFAULT_CONFIG)
        return True
    except Exception:
        return False

def load_config() -> dict:
    """Load configuration from file."""
    ensure_config_exists()
    config_file = get_config_file()
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            try:
                config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in config file: {str(e)}")
    except Exception as e:
        raise ValueError(f"Error reading config file: {str(e)}")
    
    # Deep merge with defaults to ensure all fields exist
    merged_config = DEFAULT_CONFIG.copy()
    if config:
        merged_config = deep_merge(config, merged_config)
    
    # Validate the merged configuration
    try:
        validate_config_structure(merged_config)
    except ValueError as e:
        # If validation fails, reset to defaults
        save_config(DEFAULT_CONFIG)
        raise ValueError(f"Invalid configuration detected, reset to defaults: {str(e)}")
    
    return merged_config

def save_config(config: dict):
    """Save configuration to file."""
    # Validate configuration before saving
    try:
        validate_config_structure(config)
    except ValueError as e:
        raise ValueError(f"Invalid configuration: {str(e)}")
    
    config_file = get_config_file()
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.safe_dump(config, f, default_flow_style=False)
    except Exception as e:
        raise ValueError(f"Error saving config file: {str(e)}")

def get_openai_api_key() -> str:
    """Get OpenAI API key from config or environment variable."""
    env_key = os.environ.get("OPENAI_API_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    
    config = load_config()
    config_key = config["openai"]["api_key"]
    if config_key and config_key.strip():
        return config_key.strip()
    
    return ""

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
