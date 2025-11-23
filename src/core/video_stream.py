"""
简化的视频捕获模块 - 用于端到端检测流程

功能：
- 支持摄像头实时流
- 支持视频文件流
- 流式产出RGB帧供检测使用
- 不进行视频保存（简化流程）
"""

import cv2
import time
import numpy as np
from typing import Generator, Tuple, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VideoStream:
    """
    视频流捕获器（简化版）
    
    专注于为检测模块提供帧流，不进行复杂的录制和保存
    """
    
    def __init__(self, camera_config: dict):
        """
        初始化视频流
        
        Args:
            camera_config: 摄像头配置字典
        """
        self.camera_index = camera_config.get('index', 1)
        self.width = camera_config.get('width', 1920)
        self.height = camera_config.get('height', 1080)
        self.extract_interval = camera_config.get('extract_interval', 0.5)
        
        self.cap = None
        self.fps = 0
        self.frame_count = 0
        self.last_extract_time = 0
        
        logger.info("✅ VideoStream初始化完成")
    
    def open_camera(self):
        """打开摄像头"""
        logger.info(f"尝试打开摄像头索引: {self.camera_index}")
        
        self.cap = cv2.VideoCapture(self.camera_index)
        
        if not self.cap.isOpened():
            raise RuntimeError(
                f"无法打开摄像头索引 {self.camera_index}\n"
                f"请尝试其他索引值（0, 2, 4等）"
            )
        
        # 设置分辨率
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        # 获取实际参数
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        logger.info(f"✅ 摄像头已打开: 索引{self.camera_index}, {actual_width}x{actual_height} @ {self.fps:.1f}fps")
        
        # 获取实际参数
        actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        
        logger.info(f"摄像头已打开: {actual_width}x{actual_height} @ {self.fps:.1f}fps")
    
    def open_video(self, video_path: str):
        """
        打开视频文件
        
        Args:
            video_path: 视频文件路径
        """
        logger.info(f"打开视频文件: {video_path}")
        
        if not Path(video_path).exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        self.cap = cv2.VideoCapture(video_path)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开视频文件: {video_path}")
        
        # 获取视频参数
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0
        total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        logger.info(f"视频已打开: {width}x{height} @ {self.fps:.1f}fps, {total_frames}帧")
    
    def stream_frames(self) -> Generator[Tuple[int, np.ndarray, float], None, None]:
        """
        流式产出帧（按时间间隔抽取）
        
        Yields:
            (frame_index, frame_rgb, timestamp) 元组
        """
        if self.cap is None:
            raise RuntimeError("请先调用 open_camera() 或 open_video()")
        
        logger.info(f"开始流式处理 (抽帧间隔: {self.extract_interval}秒)")
        
        frame_interval = int(self.fps * self.extract_interval)  # 转换为帧数间隔
        
        while True:
            ret, frame_bgr = self.cap.read()
            
            if not ret:
                logger.info("视频流结束")
                break
            
            self.frame_count += 1
            
            # 按帧数间隔抽取
            if self.frame_count % frame_interval == 0:
                # BGR转RGB
                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                
                # 当前时间戳
                timestamp = time.time()
                
                yield (self.frame_count, frame_rgb, timestamp)
    
    def read_frame(self) -> Optional[Tuple[np.ndarray, float]]:
        """
        读取单帧（用于GUI实时显示）
        
        Returns:
            (frame_rgb, timestamp) 或 None（如果读取失败）
        """
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame_bgr = self.cap.read()
        
        if not ret:
            return None
        
        # BGR转RGB
        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        timestamp = time.time()
        
        return (frame_rgb, timestamp)
    
    def release(self):
        """释放资源"""
        if self.cap is not None:
            self.cap.release()
            logger.info("视频流已释放")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
