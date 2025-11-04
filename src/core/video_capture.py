"""
视频捕获和关键帧提取模块

功能说明：
1. 支持从USB摄像头读取
2. 支持从视频文件读取
3. 固定时间间隔抽帧（默认0.5秒）
4. 支持实时预览和保存

主要类：
- VideoCapture: 统一的视频捕获接口

"""

import cv2
import time
import os
import numpy as np
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class VideoCapture:
    """
    统一的视频捕获接口
    
    支持从USB摄像头或视频文件读取帧，固定时间间隔提取关键帧，并可选地保存视频和帧
    """
    
    def __init__(self, 
                 source_type: str,
                 source_path,
                 target_width: int = 1920,
                 target_height: int = 1080,
                 video_save_dir: str = 'D:/Video_Records',
                 frame_save_dir: str = 'D:/Frames_Analysis',
                 extract_interval: float = 0.5):
        """
        初始化视频捕获器
        
        Args:
            source_type: 视频源类型，'camera' 或 'video'
            source_path: 摄像头索引(int)或视频文件路径(str)
            target_width: 目标宽度，默认1920
            target_height: 目标高度，默认1080
            video_save_dir: 视频保存目录，默认'D:/Video_Records'
            frame_save_dir: 帧保存目录，默认'D:/Frames_Analysis'
            extract_interval: 抽帧时间间隔（秒），默认0.5秒
        """
        self.source_type = source_type.lower()
        self.source_path = source_path
        self.target_width = target_width
        self.target_height = target_height
        self.video_save_dir = video_save_dir
        self.frame_save_dir = frame_save_dir
        self.extract_interval = extract_interval
        
        # 验证源类型
        if self.source_type not in ['camera', 'video']:
            raise ValueError(f"不支持的source_type: {source_type}，必须是 'camera' 或 'video'")
        
        # 验证视频文件是否存在
        if self.source_type == 'video':
            if not os.path.exists(source_path):
                raise FileNotFoundError(f"视频文件不存在: {source_path}")
        
        # 初始化视频捕获
        logger.info(f"初始化视频捕获器: {source_type} - {source_path}")
        self.cap = cv2.VideoCapture(source_path)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开视频源: {source_path}")
        
        # 设置分辨率（对摄像头有效）
        if target_width and target_height:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
        
        # 获取视频属性
        self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30.0  # 默认30fps
        
        logger.info(f"视频属性: {self.actual_width}x{self.actual_height} @ {self.fps:.2f} FPS")
        
        # 初始化视频写入器
        self.video_writer = None
        self.video_save_path = None
        self._init_video_writer()
        
        # 初始化帧保存目录
        self.frame_save_path = None
        self._init_frame_save_dir()
        
        # 运行状态
        self.is_running = False
        self.current_frame_index = 0
        self.start_time = time.time()
        self.last_extract_time = 0  # 上次抽帧时间
    
    def _init_video_writer(self):
        """初始化视频写入器"""
        # 创建保存目录
        os.makedirs(self.video_save_dir, exist_ok=True)
        logger.info(f"✅ 自动创建或确认视频主目录: {self.video_save_dir}")
        
        # 生成文件名（基于时间戳）
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        filename = f"{timestamp}_VIDEO.mp4"
        self.video_save_path = os.path.join(self.video_save_dir, filename)
        
        # 创建VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.video_writer = cv2.VideoWriter(
            self.video_save_path,
            fourcc,
            self.fps,
            (self.actual_width, self.actual_height)
        )
        
        if not self.video_writer.isOpened():
            logger.warning(f"❌ 无法创建视频写入器: {self.video_save_path}")
            self.video_writer = None
        else:
            logger.info(f"✅ 完整视频文件将保存到: {self.video_save_path}")
    
    def _init_frame_save_dir(self):
        """初始化帧保存目录"""
        # 创建基于时间戳的子目录
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        self.frame_save_path = os.path.join(self.frame_save_dir, f"{timestamp}_RUN")
        os.makedirs(self.frame_save_path, exist_ok=True)
        
        logger.info(f"✅ 自动创建本次抽帧运行目录: {self.frame_save_path}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取下一帧
        
        Returns:
            帧图像（numpy数组），如果读取失败则返回None
        """
        ret, frame = self.cap.read()
        
        if not ret:
            logger.warning("❌ 警告：无法读取到帧，流已中断。")
            return None
        
        # 实时显示
        cv2.imshow('Live Camera Stream (Press Q to stop)', frame)
        
        # 保存到视频文件
        if self.video_writer is not None:
            self.video_writer.write(frame)
        
        # 按Q键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            logger.info("用户按Q键退出")
            self.is_running = False
        
        # 更新帧索引
        self.current_frame_index += 1
        
        return frame
    
    def extract_keyframes(self, max_frames: Optional[int] = None) -> List:
        """
        按固定时间间隔提取关键帧
        
        Args:
            max_frames: 最大提取帧数（None表示不限制）
        
        Returns:
            关键帧列表，每个元素为(frame_index, frame_image)
        """
        keyframes = []
        
        logger.info(f"开始提取关键帧: 时间间隔={self.extract_interval}秒")
        
        self.is_running = True
        self.last_extract_time = time.time()
        
        while self.is_running:
            frame = self.get_frame()
            current_time = time.time()
            
            if frame is None:
                logger.info("视频流结束或读取失败，停止提取")
                break
            
            # 判断是否到达抽帧时间间隔
            if current_time - self.last_extract_time >= self.extract_interval:
                # 提取关键帧
                keyframes.append((self.current_frame_index, frame.copy()))
                self.last_extract_time = current_time
                
                # 保存关键帧图像
                self._save_frame(frame, self.current_frame_index)
                
                logger.info(f"⭐ 抽取并保存一帧：帧 #{len(keyframes)}")
                
                # 检查是否达到最大帧数
                if max_frames and len(keyframes) >= max_frames:
                    logger.info(f"已提取最大帧数 {max_frames}，停止提取")
                    break
        
        logger.info(f"关键帧提取完成: 共提取 {len(keyframes)} 帧")
        return keyframes
    
    def _save_frame(self, frame: np.ndarray, frame_index: int):
        """保存单帧图像"""
        # 生成文件名（毫秒级时间戳）
        timestamp_ms = int(time.time() * 1000)
        filename = os.path.join(
            self.frame_save_path,
            f"Frame_{timestamp_ms}.jpg"
        )
        
        try:
            success = cv2.imwrite(filename, frame)
            if success:
                logger.info(f"✅ 已保存帧: {os.path.basename(filename)}")
            else:
                logger.error(f"❌ 保存图片失败: {filename}")
        except Exception as e:
            logger.error(f"❌ 保存图片异常：{e}")
    
    def __iter__(self):
        """
        迭代器接口，支持 for frame in capture 语法
        
        Yields:
            视频帧（numpy数组）
        """
        self.is_running = True
        while self.is_running:
            frame = self.get_frame()
            if frame is None:
                break
            yield frame
    
    def release(self):
        """释放资源"""
        logger.info("\n程序停止，正在释放资源...")
        
        self.is_running = False
        
        # 释放视频捕获
        if self.cap is not None:
            self.cap.release()
        
        # 释放视频写入器
        if self.video_writer is not None:
            self.video_writer.release()
        
        # 关闭预览窗口
        cv2.destroyAllWindows()
        
        logger.info("✅ 资源释放完毕，文件保存完成。")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        self.release()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()
        return False
