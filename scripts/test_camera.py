"""
视频捕获测试脚本

功能：
1. 测试摄像头录制功能（选项1）：按S键开始录制，按Q键停止
2. 测试本地视频处理功能（选项2）：读取本地视频并抽帧
3. 所有配置从camera_config.yaml读取

使用方法：
    python scripts/test_camera.py
"""

import sys
from pathlib import Path
import logging

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.video_capture import VideoCapture

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """主函数：测试视频捕获功能"""
    
    logger.info("=" * 60)
    logger.info("视频捕获测试程序")
    logger.info("=" * 60)
    logger.info("\n请选择功能:")
    logger.info("1 - 摄像头录制（按S开始，按Q停止）")
    logger.info("2 - 本地视频处理（输入文件路径进行抽帧）")
    logger.info("0 - 退出程序")
    
    try:
        choice = input("\n请输入选项 (0/1/2): ").strip()
        
        if choice == '0':
            logger.info("退出程序")
            return
        
        # 创建VideoCapture对象（从配置文件加载参数）
        capture = VideoCapture()
        
        if choice == '1':
            # 摄像头录制模式
            capture.start_camera_recording()
            
        elif choice == '2':
            # 本地视频处理模式
            capture.process_local_video()
            
        else:
            logger.error("❌ 无效的选项，请输入 0、1 或 2")
            return
        
        # 释放资源
        capture.release()
        
    except KeyboardInterrupt:
        logger.info("\n用户中断程序")
    except Exception as e:
        logger.error(f"❌ 错误：{e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
