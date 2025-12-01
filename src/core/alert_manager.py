"""
警报管理器模块

功能：
- 接收检测结果并触发警报
- 支持多种输出方式（控制台、日志、保存图像、邮件）
- 管理警报历史和统计
- 对高级别警报(alert_level: high)发送邮件通知
"""

import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional
import cv2
import numpy as np

from src.alert.email_sender import EmailSender

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
        
        # 初始化邮件发送器（仅对high级别警报启用）
        email_config = config.get('email', {})
        self.email_sender = EmailSender(email_config)
        
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
            logger.debug(f"跳过普通场景警报: {result['scenario_name']}")
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
        
        # 4. 发送邮件警报（仅对high级别）
        if alert_info['alert_level'] == 'high':
            self.email_sender.send_alert(alert_info, frame)
    
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
        """在帧上标注警报信息（使用PIL支持中文）"""
        from PIL import Image, ImageDraw, ImageFont
        import subprocess
        
        # 转换为PIL图像
        pil_img = Image.fromarray(frame)
        draw = ImageDraw.Draw(pil_img)
        
        # 智能查找可用的中文字体
        font = None
        font_paths = [
            # Noto Sans CJK系列
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            # 文泉驿系列
            "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
            "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
            # AR PL系列
            "/usr/share/fonts/truetype/arphic/uming.ttc",
            "/usr/share/fonts/truetype/arphic/ukai.ttc",
            # DejaVu备选
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        
        for font_path in font_paths:
            try:
                font = ImageFont.truetype(font_path, 40)
                break
            except:
                continue
        
        # 如果静态路径都失败，尝试使用fc-match动态查找
        if font is None:
            try:
                result = subprocess.run(
                    ["fc-match", "-f", "%{file}", ":lang=zh"],
                    capture_output=True, text=True, timeout=3
                )
                if result.stdout.strip():
                    font = ImageFont.truetype(result.stdout.strip(), 40)
            except:
                pass
        
        # 最终回退
        if font is None:
            font = ImageFont.load_default()
        
        # 准备文本
        text = f"{alert_info['scenario_name']} - {alert_info['confidence']:.1%}"
        
        # 设置颜色（根据级别）
        color_map = {
            'high': (255, 0, 0),      # 红色
            'medium': (255, 165, 0),  # 橙色
            'low': (255, 255, 0)      # 黄色
        }
        color = color_map.get(alert_info['alert_level'], (0, 255, 0))
        
        # 绘制文本（带黑色描边）
        x, y = 50, 50
        for offset in [(-2,-2), (-2,2), (2,-2), (2,2)]:
            draw.text((x+offset[0], y+offset[1]), text, font=font, fill=(0, 0, 0))
        draw.text((x, y), text, font=font, fill=color)
        
        # 绘制边框
        w, h = pil_img.size
        draw.rectangle([(10, 10), (w-10, h-10)], outline=color, width=5)
        
        # 转回numpy数组
        return np.array(pil_img)
    
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
