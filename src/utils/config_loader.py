"""
配置加载器模块

功能：
- 加载YAML配置文件
- 提供配置访问接口
- 配置验证和合并

主要函数：
- load_config(): 加载单个配置文件
- load_all_configs(): 加载所有配置文件
- get_config_value(): 获取配置值（支持点号路径访问）
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, Union


def load_config(config_path: str) -> Dict[str, Any]:
    """
    加载YAML配置文件
    
    Args:
        config_path: 配置文件路径（绝对路径或相对于项目根目录的路径）
    
    Returns:
        配置字典
    
    Raises:
        FileNotFoundError: 配置文件不存在
        yaml.YAMLError: YAML解析错误
    """
    # 转换为Path对象
    config_file = Path(config_path)
    
    # 如果是相对路径，则相对于项目根目录
    if not config_file.is_absolute():
        # 获取项目根目录（假设config_loader.py在src/utils/下）
        project_root = Path(__file__).parent.parent.parent
        config_file = project_root / config_file
    
    # 检查文件是否存在
    if not config_file.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_file}")
    
    # 加载YAML文件
    with open(config_file, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config if config is not None else {}


def load_all_configs(config_dir: str = "config") -> Dict[str, Dict[str, Any]]:
    """
    加载配置目录下的所有配置文件
    
    Args:
        config_dir: 配置文件目录路径
    
    Returns:
        配置字典，键为配置文件名（不含扩展名），值为配置内容
    """
    configs = {}
    
    # 获取配置目录的绝对路径
    config_path = Path(config_dir)
    if not config_path.is_absolute():
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / config_dir
    
    # 遍历配置目录
    if config_path.exists() and config_path.is_dir():
        for config_file in config_path.glob("*.yaml"):
            config_name = config_file.stem  # 文件名（不含扩展名）
            configs[config_name] = load_config(str(config_file))
    
    return configs


def get_config_value(config: Dict[str, Any], 
                     key_path: str, 
                     default: Any = None) -> Any:
    """
    使用点号路径获取嵌套配置值
    
    Args:
        config: 配置字典
        key_path: 配置键路径，如 "detection.scenarios.fall.threshold"
        default: 默认值（当键不存在时返回）
    
    Returns:
        配置值
    
    Example:
        >>> config = {"detection": {"scenarios": {"fall": {"threshold": 0.25}}}}
        >>> get_config_value(config, "detection.scenarios.fall.threshold")
        0.25
    """
    keys = key_path.split('.')
    value = config
    
    try:
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def merge_configs(base_config: Dict[str, Any], 
                  override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    合并两个配置字典（深度合并）
    
    Args:
        base_config: 基础配置
        override_config: 覆盖配置
    
    Returns:
        合并后的配置
    """
    result = base_config.copy()
    
    for key, value in override_config.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # 递归合并嵌套字典
            result[key] = merge_configs(result[key], value)
        else:
            # 直接覆盖
            result[key] = value
    
    return result


def validate_config(config: Dict[str, Any], 
                    required_keys: list) -> bool:
    """
    验证配置是否包含必需的键
    
    Args:
        config: 配置字典
        required_keys: 必需的键列表（支持点号路径）
    
    Returns:
        验证是否通过
    
    Raises:
        ValueError: 缺少必需的配置项
    """
    missing_keys = []
    
    for key_path in required_keys:
        value = get_config_value(config, key_path)
        if value is None:
            missing_keys.append(key_path)
    
    if missing_keys:
        raise ValueError(f"配置文件缺少必需项: {', '.join(missing_keys)}")
    
    return True
