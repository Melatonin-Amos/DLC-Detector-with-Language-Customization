"""
中文提示词翻译工具

功能：
- 使用Gemini API将中文提示词翻译成英文
- 支持缓存避免重复翻译
- 去风格化翻译，适合VLM输入
"""

import logging
from typing import List, Dict, Optional
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ChineseTranslator:
    """中文提示词翻译器（惰性调用，首次翻译后缓存）"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash", 
                 cache_enabled: bool = True):
        """
        初始化翻译器
        
        Args:
            api_key: Gemini API密钥
            model: 使用的模型
            cache_enabled: 是否启用缓存
        """
        self.api_key = api_key
        self.model = model
        self.cache_enabled = cache_enabled
        self.cache: Dict[str, str] = {}
        self.cache_file = Path("data/.translation_cache.json")
        
        # 加载持久化缓存
        if self.cache_enabled:
            self._load_cache()
        
        # 延迟初始化API客户端（仅在真正需要翻译时初始化）
        self.client = None
        self._client_initialized = False
        
        if api_key:
            logger.info(f"✅ 翻译器已配置（惰性初始化）")
        else:
            logger.warning("⚠️  未提供API密钥，翻译功能已禁用")
    
    def _init_client(self):
        """延迟初始化API客户端（仅在首次需要时调用）"""
        if self._client_initialized:
            return
        
        if not self.api_key:
            logger.warning("⚠️  无API密钥，无法初始化翻译客户端")
            self._client_initialized = True
            return
        
        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            logger.info(f"✅ 翻译API客户端初始化成功，模型: {self.model}")
        except Exception as e:
            logger.error(f"❌ Gemini API初始化失败: {e}")
            self.client = None
        
        self._client_initialized = True
    
    def translate(self, text: str) -> str:
        """
        翻译单个文本（惰性调用，优先使用缓存）
        
        Args:
            text: 中文文本
            
        Returns:
            英文翻译结果，如果翻译失败则返回原文
        """
        # 如果是纯英文，直接返回
        if text.isascii():
            return text
        
        # 优先检查缓存（避免API调用）
        if self.cache_enabled and text in self.cache:
            logger.debug(f"✓ 从缓存获取翻译: {text[:20]}...")
            return self.cache[text]
        
        # 延迟初始化客户端（仅在首次需要翻译时）
        if not self._client_initialized:
            self._init_client()
        
        # 如果没有客户端，返回原文
        if not self.client:
            logger.debug(f"翻译器未启用，返回原文: {text}")
            return text
        
        try:
            # 调用API翻译
            logger.info(f"🌐 正在翻译: {text}")
            prompt = (
                f"Translate the following Chinese text to English as input for Vision-Language Models. "
                f"Provide only the translated text without any additional explanation or formatting:\n\n{text}"
            )
            
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            translated = response.text.strip()
            logger.info(f"✓ 翻译完成: {text} -> {translated}")
            
            # 保存到缓存（持久化）
            if self.cache_enabled:
                self.cache[text] = translated
                self._save_cache()
            
            return translated
            
        except Exception as e:
            logger.error(f"❌ 翻译失败: {e}，返回原文")
            return text
    
    def translate_batch(self, texts: List[str]) -> List[str]:
        """
        批量翻译
        
        Args:
            texts: 中文文本列表
            
        Returns:
            英文翻译列表
        """
        return [self.translate(text) for text in texts]
    
    def _load_cache(self):
        """加载翻译缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                logger.debug(f"加载翻译缓存: {len(self.cache)} 条")
            except Exception as e:
                logger.warning(f"加载缓存失败: {e}")
                self.cache = {}
    
    def _save_cache(self):
        """保存翻译缓存"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            logger.debug(f"保存翻译缓存: {len(self.cache)} 条")
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
