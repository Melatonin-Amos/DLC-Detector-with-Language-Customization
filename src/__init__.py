"""
DLC - Detector with Language Customization

智能养老摄像头模块 - 核心功能包

主要模块：
- models: CLIP模型封装（ViT视觉编码器 + Transformer语义编码器）
- core: 核心检测功能
- utils: 工具函数（图像处理、配置加载等）
- alert: 警报功能（拓展）

主要类和函数：
- CLIPWrapper: CLIP模型封装
- CLIPDetector: CLIP检测器
- preprocess_for_clip: 图像预处理
- load_config: 配置加载

使用示例：
    >>> from src.models import CLIPWrapper
    >>> from src.core import CLIPDetector
    >>> from src.utils import load_config
    >>> 
    >>> # 加载配置
    >>> config = load_config('config/detection_config.yaml')
    >>> 
    >>> # 创建检测器
    >>> detector = CLIPDetector(config=config)
    >>> 
    >>> # 检测图像
    >>> result = detector.detect(image)
    >>> if result['detected']:
    >>>     print(f"检测到: {result['scenario_name']}")
"""

__version__ = "0.1.0"
__author__ = "DLC Team"

# 导出主要类和函数
from .models import CLIPWrapper, VisionEncoder
from .core import CLIPDetector, ScenarioConfig
from .utils import (
    preprocess_for_clip,
    load_config,
    get_config_value
)

__all__ = [
    # 模型
    'CLIPWrapper',
    'VisionEncoder',
    # 核心功能
    'CLIPDetector',
    'ScenarioConfig',
    # 工具函数
    'preprocess_for_clip',
    'load_config',
    'get_config_value',
]

