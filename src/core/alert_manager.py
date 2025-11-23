"""
警报管理器模块

功能：
- 接收检测结果并触发警报
- 支持多种输出方式（控制台、日志、保存图像）
- 管理警报历史和统计
"""

import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import cv2
import numpy as np

logger = logging.getLogger(__name__)


class AlertManager:
    """警报管理器"""
    
    def __init__(self, config: Dict):
        """
        初始化警报管理器
        
        Args:
            config: 警报配置字典
        """
        self.config = config
        self.alert_history = []
        
        # 输出配置
        self.console_enabled = config.get('console', {}).get('enabled', True)
        self.use_color = config.get('console', {}).get('use_color', True)
        self.log_enabled = config.get('log', {}).get('enabled', True)
        self.save_frame_enabled = config.get('save_frame', {}).get('enabled', True)
        
        # 保存路径
        if self.save_frame_enabled:
            self.alert_dir = Path(config['save_frame'].get('path', 'data/outputs/alerts'))
            self.alert_dir.mkdir(parents=True, exist_ok=True)
            
        self.add_annotation = config.get('save_frame', {}).get('add_annotation', True)
        
        logger.info("✅ 警报管理器初始化完成")
    
    def trigger_alert(self, result: Dict, frame: Optional[np.ndarray] = None):
        """
        触发警报（过滤normal场景）
        
        Args:
            result: 检测结果字典
            frame: 触发警报的帧图像（可选，RGB格式）
        """
        # 过滤normal/普通场景（不报警）
        scenario_name = result.get('scenario_name', '').lower()
        if scenario_name in ['normal', '普通', '正常']:
            self.logger.debug(f"跳过普通场景警报: {result['scenario_name']}")
            return
        
        timestamp = datetime.now()
        
        # 构建警报信息
        alert_info = {
            'timestamp': timestamp,
            'scenario': result['scenario'],
            'scenario_name': result['scenario_name'],
            'confidence': result['confidence'],
            'alert_level': result['alert_level']
        }
        
        # 记录历史
        self.alert_history.append(alert_info)
        
        # 1. 控制台输出
        if self.console_enabled:
            self._print_alert(alert_info)
        
        # 2. 日志记录
        if self.log_enabled:
            self._log_alert(alert_info)
        
        # 3. 保存警报帧
        if self.save_frame_enabled and frame is not None:
            self._save_alert_frame(alert_info, frame)
    
    def _print_alert(self, alert_info: Dict):
        """打印警报到控制台（支持彩色输出）"""
        if self.use_color:
            # ANSI颜色代码
            RED = '\033[91m'
            YELLOW = '\033[93m'
            RESET = '\033[0m'
            BOLD = '\033[1m'
            
            level_colors = {
                'high': RED,
                'medium': YELLOW,
                'low': RESET
            }
            
            color = level_colors.get(alert_info['alert_level'], RESET)
            
            print(f"\n{BOLD}{color}{'=' * 60}{RESET}")
            print(f"{BOLD}{color}⚠️  警报触发！{RESET}")
            print(f"{BOLD}{color}{'=' * 60}{RESET}")
            print(f"时间: {alert_info['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"场景: {alert_info['scenario_name']}")
            print(f"置信度: {alert_info['confidence']:.3f}")
            print(f"级别: {alert_info['alert_level'].upper()}")
            print(f"{BOLD}{color}{'=' * 60}{RESET}\n")
        else:
            print(f"\n⚠️  警报: {alert_info['scenario_name']} "
                  f"(置信度: {alert_info['confidence']:.3f})")
    
    def _log_alert(self, alert_info: Dict):
        """记录警报到日志"""
        logger.warning(
            f"警报触发 - 场景: {alert_info['scenario_name']}, "
            f"置信度: {alert_info['confidence']:.3f}, "
            f"级别: {alert_info['alert_level']}"
        )
    
    def _save_alert_frame(self, alert_info: Dict, frame: np.ndarray):
        """保存警报帧图像"""
        timestamp_str = alert_info['timestamp'].strftime('%Y%m%d_%H%M%S')
        filename = f"{alert_info['scenario']}_{timestamp_str}.jpg"
        filepath = self.alert_dir / filename
        
        # 在图像上标注信息（如果启用）
        if self.add_annotation:
            annotated_frame = self._annotate_frame(frame, alert_info)
        else:
            annotated_frame = frame
        
        # RGB转BGR（OpenCV保存格式）
        frame_bgr = cv2.cvtColor(annotated_frame, cv2.COLOR_RGB2BGR)
        
        # 保存
        cv2.imwrite(str(filepath), frame_bgr)
        logger.info(f"警报帧已保存: {filepath}")
    
    def _annotate_frame(self, frame: np.ndarray, alert_info: Dict) -> np.ndarray:
        """在帧上标注警报信息"""
        annotated = frame.copy()
        
        # RGB转BGR进行标注
        annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_RGB2BGR)
        
        # 添加文本标注
        text = f"{alert_info['scenario_name']} - {alert_info['confidence']:.3f}"
        
        # 设置颜色（根据级别）
        color_map = {
            'high': (0, 0, 255),      # 红色
            'medium': (0, 165, 255),  # 橙色
            'low': (0, 255, 255)      # 黄色
        }
        color = color_map.get(alert_info['alert_level'], (0, 255, 0))
        
        # 绘制文本
        cv2.putText(
            annotated_bgr,
            text,
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            color,
            3
        )
        
        # 绘制边框
        h, w = annotated_bgr.shape[:2]
        cv2.rectangle(annotated_bgr, (10, 10), (w-10, h-10), color, 5)
        
        # BGR转回RGB
        return cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)
    
    def get_statistics(self) -> Dict:
        """获取警报统计信息"""
        if not self.alert_history:
            return {'total_alerts': 0}
        
        # 按场景统计
        scenario_counts = {}
        for alert in self.alert_history:
            scenario = alert['scenario_name']
            scenario_counts[scenario] = scenario_counts.get(scenario, 0) + 1
        
        return {
            'total_alerts': len(self.alert_history),
            'by_scenario': scenario_counts,
            'first_alert': self.alert_history[0]['timestamp'],
            'last_alert': self.alert_history[-1]['timestamp']
        }
