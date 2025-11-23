"""
DLC智能养老摄像头主程序

功能：
1. 整合视频流、CLIP检测、警报管理
2. 支持摄像头和本地视频两种输入
3. 使用Hydra进行配置管理
4. 支持中文提示词自动翻译

使用示例：
    # 摄像头模式（外接USB摄像头）
    python main.py mode=camera
    
    # 使用内置摄像头
    python main.py mode=camera camera.index=0
    
    # 视频文件模式
    python main.py mode=video video_path=assets/test_videos/fall_detection/test1.mp4
    
    # GUI模式
    python main.py mode=gui
    
    # 自定义配置
    python main.py mode=camera detection.scenarios.fall.threshold=0.3
"""

import hydra
from omegaconf import DictConfig, OmegaConf
import logging
import time
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from src.core.video_stream import VideoStream
from src.core.clip_detector import CLIPDetector
from src.core.alert_manager import AlertManager
from src.utils.logger import setup_logger
from src.utils.translator import ChineseTranslator

logger = logging.getLogger(__name__)


class DLCApplication:
    """DLC应用主类"""
    
    def __init__(self, cfg: DictConfig):
        """
        初始化DLC应用
        
        Args:
            cfg: Hydra配置对象
        """
        self.cfg = cfg
        
        # 设置日志
        log_config = cfg.alert.get('log', {})
        setup_logger(
            level=log_config.get('level', 'INFO'),
            log_file=log_config.get('file'),
            log_format=log_config.get('format')
        )
        
        logger.info("=" * 60)
        logger.info("DLC智能养老摄像头系统启动")
        logger.info("=" * 60)
        
        # 初始化各模块
        self._init_modules()
    
    def _init_modules(self):
        """初始化各功能模块"""
        
        # 1. 初始化中文翻译器
        translation_config = self.cfg.get('translation', {})
        if translation_config.get('enabled', True):
            api_key = translation_config.get('api_key')
            if api_key:
                logger.info("初始化中文翻译器...")
                self.translator = ChineseTranslator(
                    api_key=api_key,
                    model=translation_config.get('model', 'gemini-2.5-flash'),
                    cache_enabled=translation_config.get('cache_enabled', True)
                )
            else:
                logger.warning("未配置API密钥，翻译功能已禁用")
                self.translator = None
        else:
            logger.info("翻译功能已禁用")
            self.translator = None
        
        # 2. 初始化视频流
        logger.info("初始化视频流...")
        camera_config = OmegaConf.to_container(self.cfg.camera, resolve=True)
        self.video_stream = VideoStream(camera_config)
        
        # 3. 初始化CLIP检测器
        logger.info("初始化CLIP检测器...")
        full_config = OmegaConf.to_container(self.cfg, resolve=True)
        self.clip_detector = CLIPDetector(
            config=full_config,
            model_name=self.cfg.model.name,
            device=self.cfg.model.device,
            translator=self.translator
        )
        
        # 4. 初始化警报管理器
        logger.info("初始化警报管理器...")
        alert_config = OmegaConf.to_container(self.cfg.alert, resolve=True)
        self.alert_manager = AlertManager(alert_config)
        
        logger.info("✅ 所有模块初始化完成\n")
    
    def run_camera_mode(self):
        """运行摄像头模式（带GUI）"""
        logger.info("🎥 启动摄像头检测模式")
        logger.info(f"摄像头索引: {self.cfg.camera.index}")
        logger.info(f"分辨率: {self.cfg.camera.width}x{self.cfg.camera.height}")
        
        try:
            from gui.main_window import MainWindow
            
            # 打开摄像头
            self.video_stream.open_camera()
            
            # 启动GUI
            gui = MainWindow()
            gui.set_video_stream(self.video_stream)
            gui.set_detector(self.clip_detector)
            gui.set_alert_manager(self.alert_manager)
            gui.run()
            
        except ImportError as e:
            logger.error(f"❌ GUI模块导入失败: {e}")
            logger.info("降级到无GUI模式...")
            self._process_stream()
    
    def run_video_mode(self):
        """运行视频文件模式（带GUI）"""
        video_path = self.cfg.video_path
        
        if not video_path:
            logger.error("❌ 视频模式需要指定 video_path 参数")
            logger.info("示例: python main.py mode=video video_path=path/to/video.mp4")
            return
        
        logger.info("📹 启动视频文件检测模式")
        logger.info(f"视频路径: {video_path}")
        
        try:
            from gui.main_window import MainWindow
            
            # 打开视频文件
            self.video_stream.open_video(video_path)
            
            # 启动GUI
            gui = MainWindow()
            gui.set_video_stream(self.video_stream)
            gui.set_detector(self.clip_detector)
            gui.set_alert_manager(self.alert_manager)
            gui.run()
            
        except ImportError as e:
            logger.error(f"❌ GUI模块导入失败: {e}")
            logger.info("降级到无GUI模式...")
            self._process_stream()
    
    def run_gui_mode(self):
        """GUI模式已合并到camera/video模式"""
        logger.warning("⚠️  GUI模式已移除，请使用:")
        logger.info("  摄像头+GUI: python main.py mode=camera")
        logger.info("  视频+GUI:   python main.py mode=video video_path=xxx.mp4")
    
    def _process_stream(self):
        """处理视频流（核心检测循环）"""
        logger.info("🔍 开始检测\n")
        
        detection_count = 0
        frame_count = 0
        start_time = time.time()
        
        try:
            # 流式获取帧并检测
            for frame_idx, frame_rgb, timestamp in self.video_stream.stream_frames():
                frame_count += 1
                
                # 执行检测
                result = self.clip_detector.detect(frame_rgb, timestamp)
                
                # 处理检测结果
                if result['detected']:
                    detection_count += 1
                    
                    # 触发警报
                    self.alert_manager.trigger_alert(result, frame_rgb)
                
                # 显示进度（每10帧）
                if frame_count % 10 == 0:
                    elapsed = time.time() - start_time
                    fps = frame_count / elapsed if elapsed > 0 else 0
                    logger.info(f"已处理 {frame_count} 帧 | 检测到 {detection_count} 次异常 | {fps:.1f} fps")
        
        except KeyboardInterrupt:
            logger.info("\n⏸️  用户中断")
        
        finally:
            # 统计信息
            elapsed = time.time() - start_time
            logger.info("\n" + "=" * 60)
            logger.info("检测完成")
            logger.info("=" * 60)
            logger.info(f"总处理时间: {elapsed:.1f}秒")
            logger.info(f"总处理帧数: {frame_count}")
            logger.info(f"检测到异常: {detection_count} 次")
            
            # 警报统计
            stats = self.alert_manager.get_statistics()
            if stats.get('total_alerts', 0) > 0:
                logger.info(f"触发警报: {stats['total_alerts']} 次")
                logger.info(f"按场景统计: {stats.get('by_scenario', {})}")
            
            logger.info("=" * 60)
    
    def cleanup(self):
        """清理资源"""
        logger.info("清理资源...")
        if hasattr(self, 'video_stream'):
            self.video_stream.release()
        logger.info("程序退出")


@hydra.main(version_base=None, config_path="config", config_name="config")
def main(cfg: DictConfig):
    """主函数"""
    
    # 打印配置（调试模式）
    if cfg.get('debug', False):
        logger.info("\n当前配置：")
        logger.info(OmegaConf.to_yaml(cfg))
    
    # 创建应用实例
    app = DLCApplication(cfg)
    
    try:
        # 根据mode选择运行模式
        mode = cfg.get('mode', 'camera')
        
        if mode == 'camera':
            app.run_camera_mode()
        elif mode == 'video':
            app.run_video_mode()
        elif mode == 'gui':
            app.run_gui_mode()
        else:
            logger.error(f"❌ 未知的运行模式: {mode}")
            logger.info("支持的模式: camera | video | gui")
            sys.exit(1)
    
    except Exception as e:
        logger.exception(f"❌ 程序异常: {e}")
        sys.exit(1)
    
    finally:
        app.cleanup()


if __name__ == "__main__":
    main()
