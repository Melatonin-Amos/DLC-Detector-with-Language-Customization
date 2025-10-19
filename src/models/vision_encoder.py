"""
视觉编码器模块

功能：
- 独立的ViT视觉编码器封装
- 支持特征提取和可视化
- 便于扩展和自定义

主要类：
- VisionEncoder: ViT视觉编码器

注意：
本模块提供独立的视觉编码器接口，但在实际使用中，
推荐直接使用CLIPWrapper的encode_image方法，因为它已经集成了完整的功能。
本模块主要用于：
1. 需要单独使用视觉编码器的场景
2. 进行特征可视化和分析
3. 自定义视觉编码器的扩展
"""

import torch
import torch.nn as nn
from typing import Union, Optional
from PIL import Image
import numpy as np
import logging

logger = logging.getLogger(__name__)


class VisionEncoder:
    """
    ViT视觉编码器封装
    
    从CLIP模型中提取视觉编码器部分，提供独立的接口
    """
    
    def __init__(self,
                 clip_model: Optional[nn.Module] = None,
                 device: Optional[str] = None):
        """
        初始化视觉编码器
        
        Args:
            clip_model: CLIP模型实例（用于提取visual部分）
            device: 设备
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        if clip_model is None:
            # 如果没有提供CLIP模型，需要加载
            import clip
            logger.info("加载CLIP模型以提取视觉编码器")
            clip_model, _ = clip.load("ViT-B/32", device=self.device)
        
        # 提取视觉编码器
        self.visual_encoder = clip_model.visual
        self.visual_encoder.eval()
        
        # 获取配置信息
        self.input_resolution = self.visual_encoder.input_resolution
        self.output_dim = self.visual_encoder.output_dim
        
        logger.info(f"视觉编码器初始化完成 - 输入分辨率: {self.input_resolution}, 输出维度: {self.output_dim}")
    
    @torch.no_grad()
    def encode(self,
               image: torch.Tensor,
               normalize: bool = True) -> torch.Tensor:
        """
        编码图像为特征向量
        
        Args:
            image: 预处理后的图像张量，形状为(B, 3, H, W)
            normalize: 是否进行L2归一化
        
        Returns:
            图像特征，形状为(B, D)
        """
        image = image.to(self.device)
        features = self.visual_encoder(image)
        
        if normalize:
            features = torch.nn.functional.normalize(features, p=2, dim=-1)
        
        return features
    
    def get_intermediate_features(self,
                                 image: torch.Tensor,
                                 layer_indices: Optional[list] = None) -> dict:
        """
        获取中间层特征（用于可视化和分析）
        
        Args:
            image: 输入图像张量
            layer_indices: 要提取的层索引列表，None表示提取所有层
        
        Returns:
            中间层特征字典
        """
        # 这个功能需要修改forward过程，暂时返回最终特征
        logger.warning("中间层特征提取功能待实现")
        features = self.encode(image, normalize=False)
        return {'final': features}
    
    def get_attention_weights(self,
                            image: torch.Tensor) -> torch.Tensor:
        """
        获取注意力权重（用于可视化）
        
        Args:
            image: 输入图像张量
        
        Returns:
            注意力权重张量
        """
        # 注意力权重提取需要深入模型内部
        logger.warning("注意力权重提取功能待实现")
        return None
    
    def get_encoder_info(self) -> dict:
        """
        获取编码器信息
        
        Returns:
            编码器配置信息
        """
        return {
            'type': 'Vision Transformer (ViT)',
            'input_resolution': self.input_resolution,
            'output_dim': self.output_dim,
            'device': self.device
        }


# 辅助函数：特征相似度计算
def compute_feature_similarity(features1: torch.Tensor,
                              features2: torch.Tensor) -> torch.Tensor:
    """
    计算两组特征之间的余弦相似度
    
    Args:
        features1: 特征矩阵1，形状为(N, D)
        features2: 特征矩阵2，形状为(M, D)
    
    Returns:
        相似度矩阵，形状为(N, M)
    """
    # 归一化
    features1 = torch.nn.functional.normalize(features1, p=2, dim=-1)
    features2 = torch.nn.functional.normalize(features2, p=2, dim=-1)
    
    # 计算余弦相似度
    similarity = features1 @ features2.T
    
    return similarity
