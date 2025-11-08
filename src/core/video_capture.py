"""
视频捕获和关键帧提取模块

功能说明：
1. 支持从USB摄像头实时录制（按S键开始，按Q键停止）
2. 支持从本地视频文件读取并处理
3. 固定时间间隔抽帧（可配置）
4. 支持实时预览和自动保存
5. 从配置文件读取所有参数

主要类：
- VideoCapture: 统一的视频捕获接口

"""

import cv2
import time
import os
import numpy as np
import yaml
from typing import Optional, List
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class VideoCapture:
    """
    统一的视频捕获接口
    
    支持从USB摄像头实时录制或本地视频文件处理，固定时间间隔提取关键帧
    """
    
    def __init__(self, config_path: str = None):
        """
        初始化视频捕获器，从配置文件读取参数
        
        Args:
            config_path: 配置文件路径，默认使用项目中的camera_config.yaml
        """
        # 加载配置文件
        self.config = self._load_config(config_path)
        
        # 从配置文件读取参数
        self.camera_index = self.config['camera']['camera_index']
        self.target_width = self.config['camera']['target_width']
        self.target_height = self.config['camera']['target_height']
        self.extract_interval = self.config['video']['extract_interval']
        self.codec = self.config['video']['codec']
        self.default_fps = self.config['video']['default_fps']
        self.video_save_dir = self.config['paths']['video_save_dir']
        self.frame_save_dir = self.config['paths']['frame_save_dir']
        self.live_video_prefix = self.config['prefixes']['live_video']
        self.live_frame_prefix = self.config['prefixes']['live_frame']
        self.local_video_prefix = self.config['prefixes']['local_video']
        self.local_frame_prefix = self.config['prefixes']['local_frame']
        
        # 运行状态变量
        self.cap = None
        self.video_writer = None
        self.video_save_path = None
        self.frame_save_path = None
        self.is_running = False
        self.current_frame_index = 0
        self.last_extract_time = 0
        self.actual_width = 0
        self.actual_height = 0
        self.fps = 0
        self.source_type = None  # 'camera' 或 'local_video'
        
        logger.info("✅ VideoCapture初始化完成，配置已加载")
    
    def _load_config(self, config_path: str = None) -> dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if config_path is None:
            # 默认配置文件路径
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / 'config' / 'camera_config.yaml'
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"✅ 成功加载配置文件: {config_path}")
            return config
        except Exception as e:
            logger.error(f"❌ 加载配置文件失败: {e}")
            raise
    
    def start_camera_recording(self):
        """
        启动摄像头录制模式
        会先预览并等待用户按S键开始录制，按Q键可退出
        """
        logger.info("=" * 60)
        logger.info(f"启动摄像头录制 (摄像头索引: {self.camera_index})")
        logger.info("=" * 60)
        
        self.source_type = 'camera'
        
        # 初始化摄像头
        temp_cap = cv2.VideoCapture(self.camera_index)
        if not temp_cap.isOpened():
            logger.error(f"❌ 无法打开摄像头{self.camera_index}")
            raise RuntimeError(f"无法打开摄像头{self.camera_index}")
        
        logger.info("📹 摄像头已启动")
        logger.info("👀 预览窗口已打开")
        logger.info("\n⏸️  请按 'S' 键开始录制...")
        
        # 等待用户按S键开始录制
        waiting = True
        while waiting:
            ret, frame = temp_cap.read()
            if not ret:
                logger.error("❌ 无法读取摄像头画面")
                temp_cap.release()
                raise RuntimeError("无法读取摄像头画面")
            
            # 在画面上显示提示
            cv2.putText(frame, "Press 'S' to START recording", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'Q' to QUIT", (50, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow('Camera Preview', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord('s') or key == ord('S'):
                waiting = False
                logger.info("\n🔴 开始录制！")
                break
            elif key == ord('q') or key == ord('Q'):
                logger.info("\n❌ 用户取消录制")
                temp_cap.release()
                cv2.destroyAllWindows()
                return
        
        # 释放临时捕获器
        temp_cap.release()
        cv2.destroyAllWindows()
        
        # 初始化正式的摄像头捕获
        self._init_capture(self.camera_index, is_camera=True)
        
        # 开始录制和抽帧
        logger.info("开始录制和抽帧...")
        logger.info(f"- 完整视频保存到: {self.video_save_dir}")
        logger.info(f"- 抽帧保存到: {self.frame_save_dir}")
        logger.info(f"- 抽帧间隔: {self.extract_interval}秒")
        logger.info("按 'Q' 键停止录制\n")
        
        keyframes = self.extract_keyframes()
        logger.info(f"\n✅ 录制完成！共抽取 {len(keyframes)} 帧")
        
        return keyframes
    
    def process_local_video(self):
        """
        处理本地视频文件
        提示用户输入文件路径，然后进行抽帧处理
        """
        logger.info("=" * 60)
        logger.info("本地视频处理模式")
        logger.info("=" * 60)
        
        self.source_type = 'local_video'
        
        # 获取用户输入的文件路径
        video_path = input("\n请输入本地视频文件路径: ").strip()
        
        # 去除可能的引号
        video_path = video_path.strip('"').strip("'")
        
        # 验证文件是否存在
        if not os.path.exists(video_path):
            logger.error(f"❌ 文件不存在: {video_path}")
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        logger.info(f"✅ 找到视频文件: {video_path}")
        
        # 初始化视频捕获
        self._init_capture(video_path, is_camera=False)
        
        # 开始处理和抽帧
        logger.info("开始处理视频和抽帧...")
        logger.info(f"- 处理后的视频保存到: {self.video_save_dir}")
        logger.info(f"- 抽帧保存到: {self.frame_save_dir}")
        logger.info(f"- 抽帧间隔: {self.extract_interval}秒")
        logger.info("按 'Q' 键可提前停止\n")
        
        keyframes = self.extract_keyframes()
        logger.info(f"\n✅ 处理完成！共抽取 {len(keyframes)} 帧")
        
        return keyframes
    
    def _init_capture(self, source, is_camera: bool):
        """
        初始化视频捕获器
        
        Args:
            source: 摄像头索引或视频文件路径
            is_camera: 是否为摄像头
        """
        self.cap = cv2.VideoCapture(source)
        
        if not self.cap.isOpened():
            raise RuntimeError(f"无法打开视频源: {source}")
        
        # 设置分辨率（仅对摄像头有效）
        if is_camera:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.target_width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.target_height)
        
        # 获取视频属性
        self.actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        
        # 如果无法获取FPS，使用默认值
        if self.fps == 0 or self.fps is None:
            self.fps = self.default_fps
        
        logger.info(f"视频属性: {self.actual_width}x{self.actual_height} @ {self.fps:.2f} FPS")
        
        # 初始化视频写入器和帧保存目录
        self._init_video_writer()
        self._init_frame_save_dir()
    
    def _init_video_writer(self):
        """初始化视频写入器"""
        # 创建保存目录
        os.makedirs(self.video_save_dir, exist_ok=True)
        
        # 根据源类型选择文件名前缀
        if self.source_type == 'camera':
            prefix = self.live_video_prefix
        else:
            prefix = self.local_video_prefix
        
        # 生成文件名（基于时间戳）
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        filename = f"{prefix}_{timestamp}.mp4"
        self.video_save_path = os.path.join(self.video_save_dir, filename)
        
        # 创建VideoWriter
        fourcc = cv2.VideoWriter_fourcc(*self.codec)
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
            logger.info(f"✅ 视频将保存到: {self.video_save_path}")
    
    def _init_frame_save_dir(self):
        """初始化帧保存目录"""
        # 根据源类型选择目录名前缀
        if self.source_type == 'camera':
            prefix = self.live_frame_prefix
        else:
            prefix = self.local_frame_prefix
        
        # 创建基于时间戳的子目录
        timestamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
        self.frame_save_path = os.path.join(self.frame_save_dir, f"{prefix}_{timestamp}")
        os.makedirs(self.frame_save_path, exist_ok=True)
        
        logger.info(f"✅ 抽帧将保存到: {self.frame_save_path}")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取下一帧
        
        Returns:
            帧图像（numpy数组），如果读取失败则返回None
        """
        ret, frame = self.cap.read()
        
        if not ret:
            return None
        
        # 显示窗口标题根据源类型
        if self.source_type == 'camera':
            window_title = 'Live Recording (Press Q to stop)'
        else:
            window_title = 'Processing Video (Press Q to stop)'
        
        # 实时显示
        cv2.imshow(window_title, frame)
        
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
        """
        保存单帧图像
        
        Args:
            frame: 要保存的帧
            frame_index: 帧索引
        """
        # 根据源类型选择文件名前缀
        if self.source_type == 'camera':
            prefix = self.live_frame_prefix
        else:
            prefix = self.local_frame_prefix
        
        # 生成文件名（毫秒级时间戳）
        timestamp_ms = int(time.time() * 1000)
        filename = os.path.join(
            self.frame_save_path,
            f"{prefix}_{timestamp_ms}.jpg"
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
            self.cap = None
        
        # 释放视频写入器
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
        
        # 关闭预览窗口
        cv2.destroyAllWindows()
        
        logger.info("✅ 资源释放完毕，文件保存完成。")
        if self.video_save_path:
            logger.info(f"📹 视频已保存: {self.video_save_path}")
        if self.frame_save_path:
            logger.info(f"🖼️  抽帧已保存: {self.frame_save_path}")
    
    def __del__(self):
        """析构函数，确保资源被释放"""
        if hasattr(self, 'cap') and self.cap is not None:
            self.release()
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.release()
        return False
