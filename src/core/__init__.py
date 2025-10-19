"""
核心功能模块

包含：
- video_capture.py: 视频捕获和关键帧提取
- clip_detector.py: CLIP检测器
- alert_manager.py: 警报管理器

主要导出：
- CLIPDetector: CLIP检测器类
- ScenarioConfig: 场景配置类
"""

from .clip_detector import CLIPDetector, ScenarioConfig

__all__ = ['CLIPDetector', 'ScenarioConfig']

