"""
CLIP检测功能使用示例

展示如何使用实现的CLIP相关功能：
1. CLIPWrapper - CLIP模型封装（ViT + Transformer）
2. CLIPDetector - 场景检测器
3. 图像预处理和配置加载
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.models import CLIPWrapper
from src.core import CLIPDetector
from src.utils import load_config, preprocess_for_clip
from PIL import Image
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_clip_wrapper():
    """示例1：使用CLIPWrapper进行图像-文本匹配"""
    logger.info("=" * 50)
    logger.info("示例1：CLIPWrapper基础使用")
    logger.info("=" * 50)
    
    # 1. 初始化CLIP模型
    clip_model = CLIPWrapper(model_name="ViT-B/32", device="auto")
    logger.info(f"模型信息: {clip_model.get_model_info()}")
    
    # 2. 准备测试图像（这里用占位，实际使用时替换为真实图像）
    # image = Image.open("test_image.jpg")
    logger.info("\n提示：请准备测试图像")
    
    # 3. 准备文本提示词
    text_prompts = [
        "a person falling down",
        "an elderly person fallen on the ground",
        "a person standing normally",
        "fire in a room"
    ]
    
    # 4. 编码文本（演示缓存功能）
    logger.info("\n编码文本提示词...")
    text_features = clip_model.encode_text(text_prompts, use_cache=True)
    logger.info(f"文本特征形状: {text_features.shape}")
    
    # 5. 演示相似度计算（需要实际图像）
    logger.info("\n注意：图像编码和相似度计算需要实际图像")
    logger.info("示例代码：")
    logger.info("  image_features = clip_model.encode_image(image)")
    logger.info("  similarity = clip_model.compute_similarity(image_features, text_features)")
    logger.info("  logits, probs = clip_model.predict(image, text_prompts)")
    
    # 6. 清除缓存
    clip_model.clear_cache()
    logger.info("\n文本特征缓存已清除")


def example_2_clip_detector():
    """示例2：使用CLIPDetector进行场景检测"""
    logger.info("\n" + "=" * 50)
    logger.info("示例2：CLIPDetector场景检测")
    logger.info("=" * 50)
    
    # 1. 加载配置
    try:
        config = load_config("config/detection_config.yaml")
        logger.info("配置加载成功")
    except Exception as e:
        logger.error(f"配置加载失败: {e}")
        logger.info("请确保 config/detection_config.yaml 存在")
        return
    
    # 2. 创建检测器
    detector = CLIPDetector(config=config, device="auto")
    logger.info(f"检测器信息: {detector.get_detector_info()}")
    
    # 3. 显示启用的场景
    enabled_scenarios = detector.get_enabled_scenarios()
    logger.info(f"\n启用的场景: {enabled_scenarios}")
    
    # 4. 演示检测功能（需要实际图像）
    logger.info("\n检测功能演示：")
    logger.info("示例代码：")
    logger.info("  result = detector.detect(image, current_time=0)")
    logger.info("  if result['detected']:")
    logger.info("      print(f\"检测到: {result['scenario_name']}\")")
    logger.info("      print(f\"置信度: {result['confidence']:.3f}\")")
    logger.info("      print(f\"警报级别: {result['alert_level']}\")")
    
    # 5. 查看场景统计
    for scenario_id in enabled_scenarios:
        stats = detector.get_scenario_statistics(scenario_id)
        logger.info(f"\n场景统计 - {scenario_id}:")
        logger.info(f"  名称: {stats.get('scenario_name', 'N/A')}")
        logger.info(f"  阈值: {stats.get('threshold', 0):.3f}")
        logger.info(f"  启用: {stats.get('enabled', False)}")


def example_3_image_processing():
    """示例3：图像预处理"""
    logger.info("\n" + "=" * 50)
    logger.info("示例3：图像预处理")
    logger.info("=" * 50)
    
    logger.info("\nCLIP标准预处理流程：")
    logger.info("1. 转换为RGB格式")
    logger.info("2. 调整大小（短边缩放到224）")
    logger.info("3. 中心裁剪为224x224")
    logger.info("4. 转换为张量并归一化")
    logger.info("\n示例代码：")
    logger.info("  from src.utils import preprocess_for_clip")
    logger.info("  image_tensor = preprocess_for_clip(image, size=224)")
    logger.info("  # image_tensor形状: (3, 224, 224)")


def example_4_complete_workflow():
    """示例4：完整检测流程"""
    logger.info("\n" + "=" * 50)
    logger.info("示例4：完整检测流程")
    logger.info("=" * 50)
    
    logger.info("\n完整工作流程：")
    logger.info("""
1. 加载配置
   config = load_config('config/detection_config.yaml')

2. 创建检测器
   detector = CLIPDetector(config=config)

3. 读取视频帧/图像
   image = cv2.imread('frame.jpg')  # 或从视频流读取

4. 执行检测
   import time
   current_time = time.time()
   result = detector.detect(image, current_time)

5. 处理结果
   if result['detected']:
       print(f"⚠️  检测到: {result['scenario_name']}")
       print(f"   置信度: {result['confidence']:.3f}")
       print(f"   警报级别: {result['alert_level']}")
       
       # 触发警报（后续实现）
       # alert_manager.trigger_alert(result)

6. 查看所有场景的分数
   print("所有场景分数:", result.get('all_scores', {}))
    """)


def main():
    """主函数"""
    logger.info("DLC-CLIP功能演示")
    logger.info("=" * 50)
    
    try:
        # 示例1：CLIP模型基础使用
        example_1_clip_wrapper()
        
        # 示例2：场景检测器
        example_2_clip_detector()
        
        # 示例3：图像预处理
        example_3_image_processing()
        
        # 示例4：完整流程
        example_4_complete_workflow()
        
        logger.info("\n" + "=" * 50)
        logger.info("演示完成！")
        logger.info("=" * 50)
        
        logger.info("\n下一步：")
        logger.info("1. 准备测试图像/视频")
        logger.info("2. 调整 config/detection_config.yaml 中的阈值参数")
        logger.info("3. 实现视频捕获模块 (src/core/video_capture.py)")
        logger.info("4. 实现警报管理器 (src/core/alert_manager.py)")
        logger.info("5. 编写主程序 (main.py)")
        
    except Exception as e:
        logger.error(f"演示过程出错: {e}", exc_info=True)


if __name__ == "__main__":
    main()
