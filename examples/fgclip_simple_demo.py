#!/usr/bin/env python3
"""
FG-CLIP 2简单示例

演示如何使用FG-CLIP进行零样本图像分类
支持中文提示词，无需翻译
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import torch
from PIL import Image
import logging

from src.models.fgclip_wrapper import FGCLIPWrapper

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """FG-CLIP简单示例"""
    
    # 1. 初始化模型
    device = "cuda" if torch.cuda.is_available() else "cpu"
    logger.info(f"使用设备: {device}")
    
    model = FGCLIPWrapper(
        model_name="fgclip2-base-patch16",
        device=device,
        max_caption_length=196
    )
    logger.info("✅ FG-CLIP 2模型加载成功\n")
    
    # 2. 加载图像（使用测试图像或创建示例）
    # 如果有真实图像可以替换这里
    image = Image.new('RGB', (640, 480), color=(120, 180, 220))
    logger.info(f"图像尺寸: {image.size}\n")
    
    # 3. 定义中文提示词（养老场景）
    scenarios = [
        "一个老人正在房间里正常走动",
        "老人突然失去平衡摔倒在地上",
        "房间内起火冒烟，非常危险",
        "老人躺在床上休息",
        "老人在厨房做饭"
    ]
    
    logger.info("场景提示词（中文）:")
    for i, text in enumerate(scenarios, 1):
        logger.info(f"  {i}. {text}")
    logger.info("")
    
    # 4. 推理
    logger.info("正在推理...")
    logits, probs = model.predict(image, scenarios, temperature=1.0)
    
    # 5. 显示结果
    logger.info("\n检测结果:")
    logger.info("-" * 60)
    
    # 按置信度排序
    sorted_indices = probs.argsort(descending=True)
    
    for rank, idx in enumerate(sorted_indices, 1):
        scenario = scenarios[idx]
        confidence = probs[idx].item()
        logit = logits[idx].item()
        
        # 显示前3个结果
        if rank <= 3:
            logger.info(f"{rank}. {scenario}")
            logger.info(f"   置信度: {confidence:.4f} ({confidence*100:.2f}%)")
            logger.info(f"   Logit: {logit:.4f}\n")
    
    # 最终判断
    predicted_idx = probs.argmax().item()
    predicted_scenario = scenarios[predicted_idx]
    predicted_confidence = probs[predicted_idx].item()
    
    logger.info("=" * 60)
    logger.info(f"最可能的场景: {predicted_scenario}")
    logger.info(f"置信度: {predicted_confidence:.4f} ({predicted_confidence*100:.2f}%)")
    logger.info("=" * 60)
    
    # 6. 额外演示：动态分辨率处理
    logger.info("\n动态分辨率测试:")
    for size in [(320, 240), (640, 480), (1920, 1080)]:
        test_img = Image.new('RGB', size, color=(100, 150, 200))
        max_patches = model._determine_max_patches(test_img)
        logger.info(f"  {size[0]}x{size[1]} -> max_num_patches={max_patches}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n用户中断")
    except Exception as e:
        logger.error(f"错误: {e}")
        import traceback
        traceback.print_exc()
