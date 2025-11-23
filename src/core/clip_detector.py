"""
CLIP检测器模块

功能：
- 基于CLIP模型的场景检测
- 支持多场景配置和动态阈值
- 对比检测（正样本vs负样本）
- 连续帧检测和置信度统计

主要类：
- CLIPDetector: CLIP检测器，整合CLIPWrapper和场景配置

使用示例：
    >>> detector = CLIPDetector(config)
    >>> result = detector.detect(frame)
    >>> if result['detected']:
    >>>     print(f"检测到: {result['scenario']}, 置信度: {result['confidence']}")
"""

import logging
from typing import Dict, List, Union, Optional, Tuple
from collections import deque
import numpy as np
from PIL import Image

from ..models.clip_wrapper import CLIPWrapper
from ..utils.translator import ChineseTranslator

logger = logging.getLogger(__name__)


class ScenarioConfig:
    """场景配置类"""
    
    def __init__(self, scenario_dict: dict, translator: Optional[ChineseTranslator] = None):
        """
        初始化场景配置
        
        Args:
            scenario_dict: 场景配置字典（从YAML加载）
            translator: 中文翻译器（可选，FG-CLIP支持中文时为None）
        """
        self.name = scenario_dict.get('name', '')
        self.enabled = scenario_dict.get('enabled', True)
        
        # 支持单个中文提示词
        prompt_cn = scenario_dict.get('prompt_cn', '')
        
        # 如果有翻译器且配置了中文提示词，则翻译为英文（CLIP需要）
        if translator and prompt_cn:
            self.prompt = translator.translate(prompt_cn)
            logger.debug(f"场景 '{self.name}' 提示词已翻译: {prompt_cn} -> {self.prompt}")
        elif prompt_cn:
            # 无翻译器（FG-CLIP支持中文），直接使用中文提示词
            self.prompt = prompt_cn
            logger.debug(f"场景 '{self.name}' 使用中文提示词: {prompt_cn}")
        else:
            # 向后兼容：使用英文提示词
            self.prompt = scenario_dict.get('prompt', '')
        
        self.threshold = scenario_dict.get('threshold', 0.25)
        self.cooldown = scenario_dict.get('cooldown', 30)
        self.consecutive_frames = scenario_dict.get('consecutive_frames', 1)
        self.alert_level = scenario_dict.get('alert_level', 'medium')
        
        # 运行时状态
        self.last_trigger_time = 0
        self.consecutive_count = 0
        self.history = deque(maxlen=10)  # 保存最近10次检测结果


class CLIPDetector:
    """
    CLIP检测器
    
    整合CLIP模型和场景配置，提供场景检测功能
    """
    
    def __init__(self,
                 clip_model: Optional[CLIPWrapper] = None,
                 config: Optional[Dict] = None,
                 model_name: str = "ViT-B/32",
                 device: Optional[str] = None,
                 translator: Optional[ChineseTranslator] = None):
        """
        初始化CLIP检测器
        
        Args:
            clip_model: CLIP模型实例，如果为None则自动创建
            config: 完整配置字典（包含detection、model等）
            model_name: CLIP模型名称
            device: 设备
            translator: 中文翻译器（可选，FG-CLIP支持中文则不需要）
        """
        # 初始化或使用已有的CLIP模型
        if clip_model is None:
            # 检查模型类型（CLIP或FG-CLIP）
            model_config = config.get('model', {}) if config else {}
            model_type = model_config.get('type', 'clip')
            
            if model_type == 'fgclip':
                logger.info(f"创建FG-CLIP 2模型: {model_name}")
                from ..models.fgclip_wrapper import FGCLIPWrapper
                max_length = model_config.get('inference', {}).get('max_caption_length', 196)
                self.clip_model = FGCLIPWrapper(
                    model_name=model_name,
                    device=device,
                    max_caption_length=max_length
                )
                # FG-CLIP支持中文，无需翻译器
                if translator:
                    logger.info("FG-CLIP 2支持中文，翻译器将被禁用")
                    translator = None
            else:
                logger.info(f"创建CLIP模型: {model_name}")
                self.clip_model = CLIPWrapper(model_name=model_name, device=device)
        else:
            self.clip_model = clip_model
            logger.info("使用已有的CLIP模型")
        
        self.translator = translator
        
        # 解析场景配置
        self.scenarios = {}
        self.config = config or {}
        
        detection_config = self.config.get('detection', {})
        scenarios_config = detection_config.get('scenarios', {})
        
        for scenario_id, scenario_dict in scenarios_config.items():
            self.scenarios[scenario_id] = ScenarioConfig(scenario_dict, translator)
            logger.info(f"加载场景配置: {scenario_id} - {scenario_dict.get('name', '')}")
        
        # 全局配置
        self.enabled = detection_config.get('enabled', True)
        self.show_results = detection_config.get('show_results', True)
        self.show_confidence = detection_config.get('show_confidence', True)
        
        # 温度参数（从模型配置读取）
        model_config = self.config.get('model', {}).get('inference', {})
        self.temperature = model_config.get('temperature', 1.0)
        
        logger.info(f"CLIP检测器初始化完成，共加载 {len(self.scenarios)} 个场景")
    
    def detect(self,
               image: Union[Image.Image, np.ndarray],
               current_time: float = 0) -> Dict:
        """
        检测图像中的场景
        
        Args:
            image: 输入图像
            current_time: 当前时间戳（用于冷却判断）
        
        Returns:
            检测结果字典，包含：
            - detected: 是否检测到任何场景
            - scenario: 检测到的场景ID
            - scenario_name: 场景名称
            - confidence: 置信度
            - raw_score: 原始相似度分数
            - alert_level: 警报级别
            - all_scores: 所有场景的分数
        """
        if not self.enabled:
            return {'detected': False}
        
        # 收集所有启用的场景的提示词
        active_scenarios = {
            sid: scenario for sid, scenario in self.scenarios.items()
            if scenario.enabled
        }
        
        if not active_scenarios:
            logger.warning("没有启用的检测场景")
            return {'detected': False}
        
        logger.debug(f"检测图像，活跃场景数: {len(active_scenarios)}")
        
        # 一次性计算所有场景的置信度（使用softmax）
        all_prompts = [s.prompt for s in active_scenarios.values() if s.prompt]
        prompt_to_scenario = {s.prompt: sid for sid, s in active_scenarios.items() if s.prompt}
        
        if not all_prompts:
            return {'detected': False}
        
        # 使用CLIP计算所有提示词的相似度
        logits, _ = self.clip_model.predict(image, all_prompts, temperature=self.temperature)
        
        # 应用softmax归一化
        import torch.nn.functional as F
        probs = F.softmax(logits, dim=0)
        
        logger.debug(f"原始CLIP分数: {[f'{l:.4f}' for l in logits.tolist()]}")
        logger.debug(f"Softmax概率: {[f'{p:.4f}' for p in probs.tolist()]}")
        
        # 检测每个场景
        all_results = {}
        max_confidence = 0
        detected_scenario = None
        
        for idx, (prompt, scenario_id) in enumerate(prompt_to_scenario.items()):
            scenario = active_scenarios[scenario_id]
            
            # 检查冷却时间
            if current_time - scenario.last_trigger_time < scenario.cooldown:
                logger.debug(f"场景 '{scenario.name}' 冷却中，跳过")
                continue
            
            # 从预计算的softmax结果中获取置信度
            confidence = probs[idx].cpu().item()
            all_results[scenario_id] = confidence
            
            logger.info(f"场景 '{scenario.name}': {confidence:.4f} (阈值: {scenario.threshold})")
            
            # 更新历史记录
            scenario.history.append(confidence)
            
            # 判断是否超过阈值
            if confidence > scenario.threshold:
                scenario.consecutive_count += 1
                
                # 检查连续帧条件
                if scenario.consecutive_count >= scenario.consecutive_frames:
                    if confidence > max_confidence:
                        max_confidence = confidence
                        detected_scenario = scenario_id
            else:
                scenario.consecutive_count = 0
        
        # 构建检测结果
        if detected_scenario is not None:
            scenario = self.scenarios[detected_scenario]
            scenario.last_trigger_time = current_time
            scenario.consecutive_count = 0  # 重置计数
            
            result = {
                'detected': True,
                'scenario': detected_scenario,
                'scenario_name': scenario.name,
                'confidence': max_confidence,
                'raw_score': max_confidence,
                'alert_level': scenario.alert_level,
                'all_scores': all_results
            }
            
            logger.info(f"检测到场景: {scenario.name} (置信度: {max_confidence:.3f})")
        else:
            result = {
                'detected': False,
                'all_scores': all_results
            }
        
        return result
    
    def _compute_scenario_confidence(self,
                                    image: Union[Image.Image, np.ndarray],
                                    scenario: ScenarioConfig) -> float:
        """
        计算场景的置信度（使用softmax归一化）
        
        Args:
            image: 输入图像
            scenario: 场景配置
        
        Returns:
            置信度分数（0-1之间）
        """
        # 计算单个提示词的相似度
        if not scenario.prompt:
            return 0.0
        
        # 收集所有场景的提示词进行对比
        all_prompts = [s.prompt for s in self.scenarios.values() if s.enabled and s.prompt]
        
        if len(all_prompts) <= 1:
            # 只有一个场景，直接返回原始相似度
            logits, _ = self.clip_model.predict(
                image,
                [scenario.prompt],
                temperature=self.temperature
            )
            score = logits.cpu().item()
            logger.debug(f"场景 '{scenario.name}' 原始分数: {score:.4f}")
            return score
        
        # 多场景：使用softmax归一化
        logits, _ = self.clip_model.predict(
            image,
            all_prompts,
            temperature=self.temperature
        )
        
        # 应用softmax
        import torch.nn.functional as F
        probs = F.softmax(logits, dim=0)
        
        # 找到当前场景的索引
        try:
            idx = all_prompts.index(scenario.prompt)
            confidence = probs[idx].cpu().item()
            logger.debug(f"场景 '{scenario.name}' softmax分数: {confidence:.4f} (原始: {logits[idx].item():.4f})")
            return confidence
        except ValueError:
            return 0.0

    
    def batch_detect(self,
                    images: List[Union[Image.Image, np.ndarray]],
                    current_time: float = 0) -> List[Dict]:
        """
        批量检测多张图像
        
        Args:
            images: 图像列表
            current_time: 当前时间戳
        
        Returns:
            检测结果列表
        """
        results = []
        for image in images:
            result = self.detect(image, current_time)
            results.append(result)
        return results
    
    def get_scenario_statistics(self, scenario_id: str) -> Dict:
        """
        获取场景的统计信息
        
        Args:
            scenario_id: 场景ID
        
        Returns:
            统计信息字典
        """
        if scenario_id not in self.scenarios:
            return {}
        
        scenario = self.scenarios[scenario_id]
        history = list(scenario.history)
        
        if not history:
            return {
                'scenario_id': scenario_id,
                'scenario_name': scenario.name,
                'enabled': scenario.enabled,
                'threshold': scenario.threshold,
                'history_size': 0
            }
        
        return {
            'scenario_id': scenario_id,
            'scenario_name': scenario.name,
            'enabled': scenario.enabled,
            'threshold': scenario.threshold,
            'history_size': len(history),
            'mean_confidence': np.mean(history),
            'max_confidence': np.max(history),
            'min_confidence': np.min(history),
            'std_confidence': np.std(history)
        }
    
    def reset_scenario(self, scenario_id: str):
        """
        重置场景状态
        
        Args:
            scenario_id: 场景ID
        """
        if scenario_id in self.scenarios:
            scenario = self.scenarios[scenario_id]
            scenario.consecutive_count = 0
            scenario.last_trigger_time = 0
            scenario.history.clear()
            logger.info(f"场景 {scenario_id} 已重置")
    
    def reset_all_scenarios(self):
        """重置所有场景状态"""
        for scenario_id in self.scenarios:
            self.reset_scenario(scenario_id)
        logger.info("所有场景已重置")
    
    def enable_scenario(self, scenario_id: str, enabled: bool = True):
        """
        启用或禁用场景
        
        Args:
            scenario_id: 场景ID
            enabled: 是否启用
        """
        if scenario_id in self.scenarios:
            self.scenarios[scenario_id].enabled = enabled
            status = "启用" if enabled else "禁用"
            logger.info(f"场景 {scenario_id} 已{status}")
    
    def update_threshold(self, scenario_id: str, threshold: float):
        """
        更新场景阈值
        
        Args:
            scenario_id: 场景ID
            threshold: 新阈值
        """
        if scenario_id in self.scenarios:
            old_threshold = self.scenarios[scenario_id].threshold
            self.scenarios[scenario_id].threshold = threshold
            logger.info(f"场景 {scenario_id} 阈值已更新: {old_threshold:.3f} -> {threshold:.3f}")
    
    def get_enabled_scenarios(self) -> List[str]:
        """
        获取所有启用的场景ID列表
        
        Returns:
            场景ID列表
        """
        return [
            sid for sid, scenario in self.scenarios.items()
            if scenario.enabled
        ]
    
    def get_detector_info(self) -> Dict:
        """
        获取检测器信息
        
        Returns:
            检测器配置信息
        """
        return {
            'enabled': self.enabled,
            'temperature': self.temperature,
            'total_scenarios': len(self.scenarios),
            'enabled_scenarios': len(self.get_enabled_scenarios()),
            'model_info': self.clip_model.get_model_info()
        }

