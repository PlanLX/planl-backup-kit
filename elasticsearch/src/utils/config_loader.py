"""Configuration loading utilities."""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Union
from dotenv import load_dotenv

from models.config import SnapshotConfig


def load_config_from_file(config_path: Union[str, Path]) -> SnapshotConfig:
    """Load configuration from a file.

    Args:
        config_path: Path to configuration file (JSON, YAML, or .env)

    Returns:
        SnapshotConfig instance

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file format is not supported
    """
    config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    suffix = config_path.suffix.lower()
    name = config_path.name.lower()

    if suffix in [".env", ".example"] or name in [".env", ".example"]:
        return _load_from_env_file(config_path)
    elif suffix in [".json", ".yaml", ".yml"]:
        return _load_from_structured_file(config_path)
    else:
        raise ValueError(f"Unsupported configuration file format: {suffix}")


def load_config_from_env() -> SnapshotConfig:
    """Load configuration from environment variables.

    Returns:
        SnapshotConfig instance

    Raises:
        ValueError: If required environment variables are missing
    """
    # 只在开发环境中加载 .env 文件
    env_file = Path(".env")
    if env_file.exists():
        try:
            load_dotenv(env_file)
        except Exception as e:
            # 如果 .env 文件有问题，继续尝试从系统环境变量加载
            pass

    try:
        return SnapshotConfig()
    except Exception as e:
        raise ValueError(f"Failed to load configuration from environment: {e}")


def _load_from_env_file(env_path: Path) -> SnapshotConfig:
    """Load configuration from .env file."""
    load_dotenv(env_path)
    return SnapshotConfig()


def _load_from_structured_file(config_path: Path) -> SnapshotConfig:
    """Load configuration from JSON or YAML file."""
    with open(config_path, "r", encoding="utf-8") as f:
        if config_path.suffix.lower() == ".json":
            config_data = json.load(f)
        else:  # YAML
            config_data = yaml.safe_load(f)

    # Convert to SnapshotConfig
    return SnapshotConfig(**config_data)


def create_sample_config() -> Dict[str, Any]:
    """Create a sample configuration dictionary.

    Returns:
        Sample configuration dictionary
    """
    return {
        "snapshot_hosts": ["http://localhost:9200"],
        "snapshot_username": None,
        "snapshot_password": None,
        "snapshot_verify_certs": True,
        "restore_hosts": ["http://localhost:9200"],
        "restore_username": None,
        "restore_password": None,
        "restore_verify_certs": True,
        "repository_name": "my-s3-repository",
        "snapshot_name": None,  # Auto-generated if not provided
        "indices": ["my-index-1", "my-index-2"],
        "bucket_name": "my-elasticsearch-snapshots",
        "base_path": "elasticsearch-snapshots",
        "region": "us-east-1",
        "access_key": "your-access-key",
        "secret_key": "your-secret-key",
        "wait_for_completion": True,
        "timeout": 300,
    }


def save_sample_config(config_path: Union[str, Path], format: str = "yaml") -> None:
    """Save a sample configuration file.

    Args:
        config_path: Path where to save the sample config
        format: Output format ("yaml" or "json")
    """
    config_path = Path(config_path)
    config_data = create_sample_config()

    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, "w", encoding="utf-8") as f:
        if format.lower() == "json":
            json.dump(config_data, f, indent=2, ensure_ascii=False)
        else:  # YAML
            yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)

    print(f"Sample configuration saved to: {config_path}")
    print("Please update the configuration with your actual values.")
