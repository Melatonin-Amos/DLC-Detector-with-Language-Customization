"""
FG-CLIP 2模型封装

直接使用transformers AutoModel加载FG-CLIP
"""

import torch
import torch.nn.functional as F
from PIL import Image
import numpy as np
from typing import Union, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class FGCLIPWrapper:
    """FG-CLIP 2模型封装类"""
    
    def __init__(self,
                 model_name: str = "qihoo360/fg-clip2-base",
                 device: Optional[str] = None,
                 max_caption_length: int = 196):
        """
        初始化FG-CLIP 2模型
        
        Args:
            model_name: Hugging Face模型ID
            device: 设备(cuda/cpu/auto)
            max_caption_length: 最大文本长度
        """
        self.model_name = model_name
        self.max_caption_length = max_caption_length
        
        if device == "auto" or device is None:
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device
        
        logger.info(f"加载FG-CLIP 2模型: {model_name}，设备: {self.device}")
        
        try:
            from transformers import AutoModelForCausalLM, AutoProcessor
            
            # FG-CLIP使用CausalLM架构
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                dtype="auto"
            ).to(self.device)
            self.model.eval()
            
            self.processor = AutoProcessor.from_pretrained(
                model_name,
                trust_remote_code=True
            )
            
            logger.info("✅ FG-CLIP 2模型加载成功")
            
        except Exception as e:
            logger.error(f"FG-CLIP 2模型加载失败: {e}")
            raise
    
    def predict(self, 
                image: Union[Image.Image, np.ndarray],
                texts: List[str],
                temperature: float = 1.0) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        预测图像属于各个文本类别的概率
        
        Args:
            image: PIL图像或numpy数组
            texts: 文本标签列表(支持中英文)
            temperature: softmax温度参数
            
        Returns:
            (logits, probs): logits张量和概率张量
        """
        if isinstance(image, np.ndarray):
            image = Image.fromarray(image)
        
        # 使用processor处理输入
        inputs = self.processor(
            text=texts,
            images=image,
            return_tensors="pt",
            padding=True
        ).to(self.device)
        
        # 模型推理
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits_per_image = outputs.logits_per_image
        
        # 应用temperature
        logits = logits_per_image.squeeze(0) / temperature
        probs = F.softmax(logits, dim=0)
        
        return logits, probs
    
    def encode_image(self, image: Union[Image.Image, np.ndarray], normalize: bool = True) -> torch.Tensor:
        """
        编码图像(占位符,保持接口兼容)
        
        Args:
            image: PIL图像或numpy数组
            normalize: 是否归一化
            
        Returns:
            图像特征向量
        """
        # FG-CLIP pipeline不直接暴露图像编码,这里返回占位符
        logger.warning("encode_image在pipeline模式下不可用,请使用predict方法")
        return torch.zeros(512)
    
    def encode_text(self, texts: List[str], normalize: bool = True, use_cache: bool = True) -> torch.Tensor:
        """
        编码文本(占位符,保持接口兼容)
        
        Args:
            texts: 文本列表
            normalize: 是否归一化
            use_cache: 是否使用缓存
            
        Returns:
            文本特征向量
        """
        logger.warning("encode_text在pipeline模式下不可用,请使用predict方法")
        return torch.zeros(len(texts), 512)
    
    def compute_similarity(self, img_feat: torch.Tensor, txt_feat: torch.Tensor, 
                          apply_scale_bias: bool = True) -> torch.Tensor:
        """
        计算相似度(占位符,保持接口兼容)
        
        Args:
            img_feat: 图像特征
            txt_feat: 文本特征
            apply_scale_bias: 是否应用scale和bias
            
        Returns:
            相似度分数
        """
        logger.warning("compute_similarity在pipeline模式下不可用,请使用predict方法")
        return torch.zeros(txt_feat.shape[0])
