"""
CLIP模型封装模块

功能：
- 加载预训练的CLIP模型
- 提供图像编码接口（ViT视觉编码器）
- 提供文本编码接口（Transformer语义编码器）
- 计算余弦相似度
- 支持批量处理和缓存

主要类：
- CLIPWrapper: CLIP模型封装类

使用示例：
    >>> clip_model = CLIPWrapper(model_name="ViT-B/32", device="cuda")
    >>> image_features = clip_model.encode_image(image)
    >>> text_features = clip_model.encode_text(["a person falling down"])
    >>> similarity = clip_model.compute_similarity(image_features, text_features)
"""

import torch
import torch.nn.functional as F
import clip
from PIL import Image
import numpy as np
from typing import Union, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class CLIPWrapper:
    """
    CLIP模型封装类
    
    提供统一的接口用于：
    - 图像编码（使用ViT作为视觉编码器）
    - 文本编码（使用Transformer作为语义编码器）
    - 相似度计算（余弦相似度）
    """
    
    def __init__(self,
                 model_name: str = "ViT-B/32",
                 device: Optional[str] = None,
                 jit: bool = False):
        """
        初始化CLIP模型
        
        Args:
            model_name: 模型名称，可选: "ViT-B/32", "ViT-B/16", "ViT-L/14"等
            device: 设备，None表示自动选择（优先GPU）
            jit: 是否使用JIT编译（可能提升性能）
        """
        self.model_name = model_name
        
        # 自动选择设备，有独显建议使用CUDA
        if device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        elif device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"加载CLIP模型: {model_name}，设备: {self.device}")
        
        # 加载CLIP模型和预处理器
        try:
            self.model, self.preprocess = clip.load(
                model_name,
                device=self.device,
                jit=jit
            )
            self.model.eval()  # 设置为评估模式
            logger.info("CLIP模型加载成功")
        except Exception as e:
            logger.error(f"CLIP模型加载失败: {e}")
            raise
        
        # 获取模型配置信息
        self.image_size = self.model.visual.input_resolution
        self.context_length = self.model.context_length
        
        # 特征缓存（可选）
        self._text_feature_cache = {}
    
    @torch.no_grad()
    def encode_image(self,
                     image: Union[Image.Image, torch.Tensor, np.ndarray, List],
                     normalize: bool = True) -> torch.Tensor:
        """
        编码图像为特征向量（使用ViT视觉编码器）
        
        Args:
            image: 输入图像，支持多种格式：
                  - PIL Image
                  - torch.Tensor (已预处理)
                  - numpy数组
                  - 以上类型的列表（批量处理）
            normalize: 是否对特征进行L2归一化
        
        Returns:
            图像特征张量，形状为(N, D)，其中N为图像数量，D为特征维度
        """
        # 处理输入格式
        if isinstance(image, list):
            # 批量处理
            processed_images = []
            for img in image:
                if isinstance(img, torch.Tensor):
                    processed_images.append(img)
                else:
                    # 使用CLIP的预处理器
                    processed_images.append(self.preprocess(img))
            image_tensor = torch.stack(processed_images).to(self.device)
        elif isinstance(image, torch.Tensor):
            # 已经是张量
            if image.dim() == 3:
                image_tensor = image.unsqueeze(0)  # 添加batch维度
            else:
                image_tensor = image
            image_tensor = image_tensor.to(self.device)
        elif isinstance(image, np.ndarray):
            # numpy数组，转换为PIL然后预处理
            image = Image.fromarray(image)
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        else:
            # PIL Image
            image_tensor = self.preprocess(image).unsqueeze(0).to(self.device)
        
        # 编码图像（ViT视觉编码器）
        image_features = self.model.encode_image(image_tensor)
        
        # L2归一化
        if normalize:
            image_features = F.normalize(image_features, p=2, dim=-1)
        
        return image_features
    
    @torch.no_grad()
    def encode_text(self,
                    text: Union[str, List[str]],
                    normalize: bool = True,
                    use_cache: bool = True) -> torch.Tensor:
        """
        编码文本为特征向量（使用Transformer语义编码器）
        
        Args:
            text: 输入文本，可以是单个字符串或字符串列表
            normalize: 是否对特征进行L2归一化
            use_cache: 是否使用缓存（对于重复的文本提示词）
        
        Returns:
            文本特征张量，形状为(N, D)，其中N为文本数量，D为特征维度
        """
        # 统一为列表格式
        if isinstance(text, str):
            text = [text]
        
        # 检查缓存
        if use_cache:
            cached_features = []
            uncached_texts = []
            uncached_indices = []
            
            for idx, t in enumerate(text):
                if t in self._text_feature_cache:
                    cached_features.append(self._text_feature_cache[t])
                else:
                    uncached_texts.append(t)
                    uncached_indices.append(idx)
            
            # 如果全部命中缓存
            if not uncached_texts:
                return torch.stack(cached_features)
            
            # 编码未缓存的文本
            if uncached_texts:
                text_tokens = clip.tokenize(uncached_texts).to(self.device)
                new_features = self.model.encode_text(text_tokens)
                
                if normalize:
                    new_features = F.normalize(new_features, p=2, dim=-1)
                
                # 更新缓存
                for t, feat in zip(uncached_texts, new_features):
                    self._text_feature_cache[t] = feat
                
                # 合并缓存和新特征
                all_features = [None] * len(text)
                cached_idx = 0
                new_idx = 0
                for idx in range(len(text)):
                    if idx in uncached_indices:
                        all_features[idx] = new_features[new_idx]
                        new_idx += 1
                    else:
                        all_features[idx] = cached_features[cached_idx]
                        cached_idx += 1
                
                return torch.stack(all_features)
        
        # 不使用缓存，直接编码
        text_tokens = clip.tokenize(text).to(self.device)
        text_features = self.model.encode_text(text_tokens)
        
        # L2归一化
        if normalize:
            text_features = F.normalize(text_features, p=2, dim=-1)
        
        return text_features
    
    @staticmethod
    def compute_similarity(image_features: torch.Tensor,
                          text_features: torch.Tensor,
                          temperature: float = 1.0) -> torch.Tensor:
        """
        计算图像和文本特征之间的余弦相似度
        
        由于特征已经过L2归一化，余弦相似度等价于特征向量的点积
        
        Args:
            image_features: 图像特征，形状为(N, D)
            text_features: 文本特征，形状为(M, D)
            temperature: 温度参数，用于缩放相似度分数
        
        Returns:
            相似度矩阵，形状为(N, M)，每个元素表示对应图像和文本的相似度
        """
        # 计算余弦相似度（特征已归一化，直接点积）
        similarity = image_features @ text_features.T
        
        # 应用温度参数
        similarity = similarity / temperature
        
        return similarity
    
    def predict(self,
                image: Union[Image.Image, torch.Tensor, np.ndarray],
                text_prompts: List[str],
                temperature: float = 1.0) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        端到端预测：计算图像与多个文本提示的相似度
        
        Args:
            image: 输入图像
            text_prompts: 文本提示列表
            temperature: 温度参数
        
        Returns:
            (logits, probabilities):
            - logits: 相似度分数张量
            - probabilities: softmax归一化后的概率张量
        """
        # 编码图像和文本
        image_features = self.encode_image(image)
        text_features = self.encode_text(text_prompts)
        
        # 计算相似度
        logits = self.compute_similarity(image_features, text_features, temperature)
        
        # 计算概率（softmax）
        probs = F.softmax(logits, dim=-1)
        
        return logits[0], probs[0]
    
    def get_top_predictions(self,
                           image: Union[Image.Image, torch.Tensor, np.ndarray],
                           text_prompts: List[str],
                           top_k: int = 3) -> List[Tuple[str, float]]:
        """
        获取top-k预测结果
        
        Args:
            image: 输入图像
            text_prompts: 文本提示列表
            top_k: 返回前k个结果
        
        Returns:
            (text, score)元组的列表，按分数降序排列
        """
        logits, probs = self.predict(image, text_prompts)
        
        # 获取top-k索引
        top_k = min(top_k, len(text_prompts))
        top_indices = torch.topk(logits, top_k).indices.cpu().tolist()
        
        # 构建结果
        results = [(text_prompts[idx], probs[idx]) for idx in top_indices]
        
        return results
    
    def clear_cache(self):
        """清除文本特征缓存"""
        self._text_feature_cache.clear()
        logger.info("文本特征缓存已清除")
    
    def get_model_info(self) -> dict:
        """
        获取模型信息
        
        Returns:
            模型配置信息字典
        """
        return {
            "model_name": self.model_name,
            "device": self.device,
            "image_size": self.image_size,
            "context_length": self.context_length,
            "cache_size": len(self._text_feature_cache)
        }

