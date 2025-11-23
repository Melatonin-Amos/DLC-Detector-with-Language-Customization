"""
工具函数模块

包含：
- image_processing.py: 图像预处理
- config_loader.py: 配置加载器
- logger.py: 日志工具
- translator.py: 中文翻译工具

主要导出：
- preprocess_for_clip: CLIP图像预处理函数
- create_clip_transform: 创建CLIP预处理变换
- load_config: 加载配置函数
- get_config_value: 获取配置值函数
- setup_logger: 日志设置函数
- ChineseTranslator: 中文翻译器类
"""

from .image_processing import (
    preprocess_for_clip,
    create_clip_transform,
    convert_to_rgb,
    resize_image,
    normalize_image,
    batch_preprocess
)

from .config_loader import (
    load_config,
    load_all_configs,
    get_config_value,
    merge_configs,
    validate_config
)

from .logger import setup_logger

from .translator import ChineseTranslator

__all__ = [
    # 图像处理
    'preprocess_for_clip',
    'create_clip_transform',
    'convert_to_rgb',
    'resize_image',
    'normalize_image',
    'batch_preprocess',
    # 配置加载
    'load_config',
    'load_all_configs',
    'get_config_value',
    'merge_configs',
    'validate_config',
    # 日志
    'setup_logger',
    # 翻译
    'ChineseTranslator'
]

