"""
图像预处理工具模块

功能：
- 图像大小调整和归一化（CLIP标准）
- 相机畸变矫正（可选）
- 图像格式转换（PIL <-> numpy <-> tensor）
- 图像增强（对比度、亮度调整）

主要函数：
- preprocess_for_clip(): 为CLIP模型预处理图像
- resize_image(): 调整图像大小
- normalize_image(): 归一化图像
- convert_to_rgb(): 转换为RGB格式
- undistort_image(): 畸变矫正（需要相机标定参数）
"""

import cv2
import numpy as np
from PIL import Image
import torch
from torchvision import transforms
from typing import Union, Tuple, Optional


# CLIP标准归一化参数
CLIP_MEAN = [0.48145466, 0.4578275, 0.40821073]
CLIP_STD = [0.26862954, 0.26130258, 0.27577711]


def convert_to_rgb(image: Union[np.ndarray, Image.Image]) -> Image.Image:
    """
    将图像转换为RGB格式的PIL Image
    
    Args:
        image: 输入图像（numpy数组或PIL Image）
    
    Returns:
        RGB格式的PIL Image
    """
    if isinstance(image, np.ndarray):
        # OpenCV使用BGR格式，需要转换为RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image)
    
    # 确保是RGB格式
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    return image


def resize_image(image: Image.Image, 
                 size: Union[int, Tuple[int, int]],
                 interpolation: int = Image.BICUBIC) -> Image.Image:
    """
    调整图像大小
    
    Args:
        image: 输入图像（PIL Image）
        size: 目标大小，可以是整数（正方形）或(width, height)元组
        interpolation: 插值方法，默认为BICUBIC
    
    Returns:
        调整大小后的图像
    """
    if isinstance(size, int):
        # 保持宽高比，短边调整为size
        w, h = image.size
        if w < h:
            new_w = size
            new_h = int(h * size / w)
        else:
            new_h = size
            new_w = int(w * size / h)
        size = (new_w, new_h)
    
    return image.resize(size, interpolation)


def center_crop(image: Image.Image, size: int) -> Image.Image:
    """
    中心裁剪图像
    
    Args:
        image: 输入图像
        size: 裁剪尺寸（正方形）
    
    Returns:
        裁剪后的图像
    """
    w, h = image.size
    left = (w - size) // 2
    top = (h - size) // 2
    right = left + size
    bottom = top + size
    
    return image.crop((left, top, right, bottom))


def normalize_image(image: torch.Tensor,
                    mean: list = CLIP_MEAN,
                    std: list = CLIP_STD) -> torch.Tensor:
    """
    归一化图像张量
    
    Args:
        image: 图像张量，形状为(C, H, W)，值域[0, 1]
        mean: 均值列表
        std: 标准差列表
    
    Returns:
        归一化后的图像张量
    """
    # 转换为张量
    if not isinstance(image, torch.Tensor):
        image = torch.tensor(image)
    
    # 归一化
    mean_tensor = torch.tensor(mean).view(-1, 1, 1)
    std_tensor = torch.tensor(std).view(-1, 1, 1)
    
    return (image - mean_tensor) / std_tensor


def preprocess_for_clip(image: Union[np.ndarray, Image.Image],
                        size: int = 224) -> torch.Tensor:
    """
    为CLIP模型预处理图像
    
    处理流程：
    1. 转换为RGB PIL Image
    2. 调整大小（短边缩放到size）
    3. 中心裁剪为size x size
    4. 转换为张量
    5. 归一化
    
    Args:
        image: 输入图像（numpy数组或PIL Image）
        size: 目标尺寸，默认224（ViT-B/32标准）
    
    Returns:
        预处理后的图像张量，形状为(C, H, W)
    """
    # 1. 转换为RGB
    image = convert_to_rgb(image)
    
    # 2. 调整大小（短边缩放）
    image = resize_image(image, size)
    
    # 3. 中心裁剪
    image = center_crop(image, size)
    
    # 4. 转换为张量
    image_tensor = transforms.ToTensor()(image)
    
    # 5. 归一化
    image_tensor = normalize_image(image_tensor)
    
    return image_tensor


def create_clip_transform(size: int = 224) -> transforms.Compose:
    """
    创建CLIP标准的图像预处理变换
    
    Args:
        size: 图像大小
    
    Returns:
        torchvision transforms组合
    """
    return transforms.Compose([
        transforms.Resize(size, interpolation=Image.BICUBIC),
        transforms.CenterCrop(size),
        transforms.ToTensor(),
        transforms.Normalize(mean=CLIP_MEAN, std=CLIP_STD)
    ])


def undistort_image(image: np.ndarray,
                   camera_matrix: np.ndarray,
                   distortion_coeffs: np.ndarray) -> np.ndarray:
    """
    使用相机标定参数矫正图像畸变
    
    Args:
        image: 输入图像（numpy数组）
        camera_matrix: 相机内参矩阵 (3x3)
        distortion_coeffs: 畸变系数 (k1, k2, p1, p2, k3)
    
    Returns:
        矫正后的图像
    """
    return cv2.undistort(image, camera_matrix, distortion_coeffs)


def enhance_contrast(image: Union[np.ndarray, Image.Image],
                    factor: float = 1.5) -> Union[np.ndarray, Image.Image]:
    """
    增强图像对比度
    
    Args:
        image: 输入图像
        factor: 对比度增强因子（>1增强，<1减弱）
    
    Returns:
        增强后的图像（与输入格式相同）
    """
    is_numpy = isinstance(image, np.ndarray)
    
    if is_numpy:
        image = Image.fromarray(image)
    
    # 使用PIL增强对比度
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Contrast(image)
    enhanced = enhancer.enhance(factor)
    
    if is_numpy:
        enhanced = np.array(enhanced)
    
    return enhanced


def adjust_brightness(image: Union[np.ndarray, Image.Image],
                     factor: float = 1.2) -> Union[np.ndarray, Image.Image]:
    """
    调整图像亮度
    
    Args:
        image: 输入图像
        factor: 亮度调整因子（>1变亮，<1变暗）
    
    Returns:
        调整后的图像（与输入格式相同）
    """
    is_numpy = isinstance(image, np.ndarray)
    
    if is_numpy:
        image = Image.fromarray(image)
    
    # 使用PIL调整亮度
    from PIL import ImageEnhance
    enhancer = ImageEnhance.Brightness(image)
    adjusted = enhancer.enhance(factor)
    
    if is_numpy:
        adjusted = np.array(adjusted)
    
    return adjusted


def batch_preprocess(images: list,
                    size: int = 224) -> torch.Tensor:
    """
    批量预处理图像
    
    Args:
        images: 图像列表
        size: 目标尺寸
    
    Returns:
        批量图像张量，形状为(B, C, H, W)
    """
    processed = [preprocess_for_clip(img, size) for img in images]
    return torch.stack(processed)

