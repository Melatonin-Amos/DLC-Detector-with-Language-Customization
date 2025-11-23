"""
核心功能模块

包含：
- video_capture.py: 视频捕获和关键帧提取（原始实现）
- video_stream.py: 简化的视频流（用于端到端流程）
- clip_detector.py: CLIP检测器
- alert_manager.py: 警报管理器

主要导出：
- CLIPDetector: CLIP检测器类
- ScenarioConfig: 场景配置类
- AlertManager: 警报管理器类
- VideoStream: 视频流类
"""

from .clip_detector import CLIPDetector, ScenarioConfig
from .alert_manager import AlertManager
from .video_stream import VideoStream

__all__ = ['CLIPDetector', 'ScenarioConfig', 'AlertManager', 'VideoStream']

