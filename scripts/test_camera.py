"""
测试视频捕获功能

功能：
1. 自动连接USB摄像头（索引0）
2. 按 'S' 键开始录制
3. 自动显示实时画面
4. 自动保存完整视频到 D:/Video_Records/
5. 自动按0.5秒间隔抽帧并保存到 D:/Frames_Analysis/
6. 按 'Q' 键停止录制

使用方法：
    python scripts/test_camera.py
"""

import sys
from pathlib import Path
import logging
import cv2

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
    """主函数：简单测试视频捕获"""
    import sys
    
    # 固定使用摄像头1
    source_type = 'camera'
    source_path = 1
    
    logger.info("=" * 60)
    logger.info("USB摄像头录制程序 (摄像头索引: 1)")
    logger.info("=" * 60)
    
    try:
        # 先创建一个临时捕获器用于等待按键
        logger.info("\n📹 摄像头预热中...")
        temp_cap = cv2.VideoCapture(source_path)
        if not temp_cap.isOpened():
            logger.error("❌ 无法打开摄像头1，请检查摄像头连接")
            sys.exit(1)
        
        logger.info("👀 预览窗口已打开")
        logger.info("\n⏸️  请按 'S' 键开始录制...")
        
        # 等待用户按S键开始录制
        waiting = True
        while waiting:
            ret, frame = temp_cap.read()
            if not ret:
                logger.error("❌ 无法读取摄像头画面")
                break
            
            # 在画面上显示提示
            cv2.putText(frame, "Press 'S' to START recording", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press 'Q' to QUIT", (50, 100),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            cv2.imshow('Real-time Video', frame)
            
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
        
        # 创建正式的视频捕获器（自动预览、保存视频、保存关键帧）
        logger.info("实时窗口会自动显示")
        logger.info("完整视频会自动保存到: D:/Video_Records/")
        logger.info("每0.5秒自动抽取一帧并保存到: D:/Frames_Analysis/")
        logger.info("请在实时窗口中按 'Q' 键停止并退出程序...\n")
        
        with VideoCapture(
            source_type=source_type,
            source_path=source_path
        ) as capture:
            # 提取关键帧（会自动显示和保存）
            keyframes = capture.extract_keyframes()
            
            logger.info(f"\n✅ 录制完成！共抽取 {len(keyframes)} 帧")
        
    except FileNotFoundError as e:
        logger.error(f"❌ 错误：文件不存在 - {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 错误：{e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
