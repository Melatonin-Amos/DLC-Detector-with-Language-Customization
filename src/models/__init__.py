"""
模型封装模块

包含：
- clip_wrapper.py: CLIP模型封装（ViT + Transformer）
- vision_encoder.py: 视觉编码器（可选）

主要导出：
- CLIPWrapper: CLIP模型封装类
- VisionEncoder: 视觉编码器类
"""

from .clip_wrapper import CLIPWrapper
from .vision_encoder import VisionEncoder

__all__ = ['CLIPWrapper', 'VisionEncoder']

