#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUI 字体配置加载器

功能：
1. 从 config/gui_fonts.yaml 加载字体配置
2. 自动检测当前操作系统并选择对应字体
3. 验证字体是否可用，自动回退到备用字体
4. 提供统一的字体配置接口供 GUI 模块使用

使用方法:
    from src.utils.font_loader import FontLoader
    
    fonts = FontLoader()
    font_family = fonts.get_font_family()  # 获取当前平台的字体族
    font_config = fonts.get_font("normal")  # 获取普通字体配置 (family, size, weight)
"""

import os
import sys
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import yaml

# 尝试导入 tkinter 用于字体验证
try:
    import tkinter as tk
    from tkinter import font as tkfont
    HAS_TKINTER = True
except ImportError:
    HAS_TKINTER = False


class FontLoader:
    """GUI 字体配置加载器"""
    
    # 默认配置（作为最终回退）
    DEFAULT_FONTS = {
        "font_families": {
            "windows": {"primary": "Microsoft YaHei", "fallback": ["SimHei", "Arial"]},
            "linux": {"primary": "Noto Sans CJK SC", "fallback": ["DejaVu Sans", "Arial"]},
            "macos": {"primary": "PingFang SC", "fallback": ["Heiti SC", "Arial"]},
        },
        "header_font": {
            "windows": {"family": "Georgia", "fallback": ["Times New Roman"]},
            "linux": {"family": "DejaVu Serif", "fallback": ["Liberation Serif"]},
            "macos": {"family": "Georgia", "fallback": ["Times New Roman"]},
            "size": 22,
            "weight": "bold",
            "slant": "italic",
        },
        "font_styles": {
            "normal": {"size": 12, "weight": "bold", "slant": "roman"},
            "title": {"size": 16, "weight": "bold", "slant": "roman"},
            "large": {"size": 18, "weight": "bold", "slant": "roman"},
            "small": {"size": 11, "weight": "bold", "slant": "roman"},
            "italic": {"size": 12, "weight": "bold", "slant": "italic"},
            "replay": {"size": 24, "weight": "bold", "slant": "roman"},
        },
        "title_color": "#2c3e50",
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化字体加载器
        
        Args:
            config_path: 配置文件路径，如果为 None 则自动查找
        """
        self._platform = self._detect_platform()
        self._config = self._load_config(config_path)
        self._available_fonts: Optional[set] = None
        self._validated_font_family: Optional[str] = None
        self._validated_header_font: Optional[str] = None
        
    def _detect_platform(self) -> str:
        """
        检测当前操作系统平台
        
        Returns:
            平台名称: 'windows', 'linux', 或 'macos'
        """
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        else:
            return "linux"
    
    def _find_config_path(self) -> Optional[Path]:
        """
        查找配置文件路径
        
        Returns:
            配置文件路径，如果未找到则返回 None
        """
        # 可能的配置文件位置
        possible_paths = [
            Path(__file__).parent.parent.parent / "config" / "gui_fonts.yaml",  # 项目根目录
            Path.cwd() / "config" / "gui_fonts.yaml",  # 当前工作目录
            Path(__file__).parent / "gui_fonts.yaml",  # 与此文件同目录
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        return None
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict:
        """
        加载字体配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            配置字典
        """
        if config_path:
            path = Path(config_path)
        else:
            path = self._find_config_path()
        
        if path and path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    if config:
                        print(f"✓ 已加载字体配置: {path}")
                        return config
            except Exception as e:
                print(f"⚠️  加载字体配置失败 ({path}): {e}")
        
        print("⚠️  使用默认字体配置")
        return self.DEFAULT_FONTS.copy()
    
    def _get_available_fonts(self) -> set:
        """
        获取系统中可用的字体列表
        
        Returns:
            可用字体名称的集合
        """
        if self._available_fonts is not None:
            return self._available_fonts
        
        if not HAS_TKINTER:
            self._available_fonts = set()
            return self._available_fonts
        
        try:
            # 创建临时 Tk 窗口来获取字体列表
            temp_root = tk.Tk()
            temp_root.withdraw()
            self._available_fonts = set(tkfont.families())
            temp_root.destroy()
        except Exception as e:
            print(f"⚠️  获取系统字体列表失败: {e}")
            self._available_fonts = set()
        
        return self._available_fonts
    
    def _validate_font(self, font_name: str) -> bool:
        """
        验证字体是否可用
        
        Args:
            font_name: 字体名称
            
        Returns:
            True 如果字体可用
        """
        available = self._get_available_fonts()
        if not available:
            # 无法验证，假设可用
            return True
        return font_name in available
    
    def get_platform(self) -> str:
        """
        获取当前平台名称
        
        Returns:
            平台名称
        """
        return self._platform
    
    def get_font_family(self, validate: bool = True) -> str:
        """
        获取当前平台的主字体族
        
        Args:
            validate: 是否验证字体可用性并自动回退
            
        Returns:
            字体族名称
        """
        if self._validated_font_family and validate:
            return self._validated_font_family
        
        families_config = self._config.get("font_families", {})
        platform_config = families_config.get(self._platform, {})
        
        primary = platform_config.get("primary", "Arial")
        fallback = platform_config.get("fallback", [])
        
        if not validate:
            return primary
        
        # 验证主字体
        if self._validate_font(primary):
            self._validated_font_family = primary
            return primary
        
        # 尝试回退字体
        for font in fallback:
            if self._validate_font(font):
                print(f"⚠️  主字体 '{primary}' 不可用，使用回退字体 '{font}'")
                self._validated_font_family = font
                return font
        
        # 最终回退
        print(f"⚠️  所有配置字体都不可用，使用系统默认字体")
        self._validated_font_family = "Arial"
        return "Arial"
    
    def get_header_font_family(self, validate: bool = True) -> str:
        """
        获取标题字体族（用于艺术标题）
        
        Args:
            validate: 是否验证字体可用性
            
        Returns:
            标题字体族名称
        """
        if self._validated_header_font and validate:
            return self._validated_header_font
        
        header_config = self._config.get("header_font", {})
        platform_config = header_config.get(self._platform, {})
        
        primary = platform_config.get("family", "Georgia")
        fallback = platform_config.get("fallback", [])
        
        if not validate:
            return primary
        
        # 验证主字体
        if self._validate_font(primary):
            self._validated_header_font = primary
            return primary
        
        # 尝试回退字体
        for font in fallback:
            if self._validate_font(font):
                print(f"⚠️  标题字体 '{primary}' 不可用，使用回退字体 '{font}'")
                self._validated_header_font = font
                return font
        
        # 最终回退到主字体族
        self._validated_header_font = self.get_font_family(validate=True)
        return self._validated_header_font
    
    def get_font_style(self, style_name: str) -> Dict[str, Any]:
        """
        获取指定样式的字体配置
        
        Args:
            style_name: 样式名称 (normal, title, large, small, italic, replay)
            
        Returns:
            样式配置字典，包含 size, weight, slant
        """
        styles = self._config.get("font_styles", {})
        style = styles.get(style_name, styles.get("normal", self.DEFAULT_FONTS["font_styles"]["normal"]))
        return style
    
    def get_font(self, style_name: str, validate: bool = True) -> Tuple[str, int, str]:
        """
        获取完整的字体配置元组（适用于 Tkinter）
        
        Args:
            style_name: 样式名称
            validate: 是否验证字体可用性
            
        Returns:
            (font_family, size, weight) 元组
        """
        family = self.get_font_family(validate=validate)
        style = self.get_font_style(style_name)
        
        size = style.get("size", 12)
        weight = style.get("weight", "normal")
        
        return (family, size, weight)
    
    def get_header_font(self, validate: bool = True) -> Tuple[str, int, str]:
        """
        获取标题字体配置元组（用于艺术标题）
        
        Args:
            validate: 是否验证字体可用性
            
        Returns:
            (font_family, size, "weight slant") 元组
        """
        family = self.get_header_font_family(validate=validate)
        header_config = self._config.get("header_font", {})
        
        size = header_config.get("size", 22)
        weight = header_config.get("weight", "bold")
        slant = header_config.get("slant", "italic")
        
        # Tkinter 字体格式: (family, size, "bold italic")
        style_str = f"{weight} {slant}" if slant != "roman" else weight
        
        return (family, size, style_str)
    
    def get_all_fonts(self, validate: bool = True) -> Dict[str, Tuple[str, int, str]]:
        """
        获取所有字体配置（用于 GUI 初始化）
        
        Args:
            validate: 是否验证字体可用性
            
        Returns:
            字体配置字典，键为样式名称，值为 (family, size, weight) 元组
        """
        fonts = {}
        family = self.get_font_family(validate=validate)
        
        for style_name, style_config in self._config.get("font_styles", {}).items():
            size = style_config.get("size", 12)
            weight = style_config.get("weight", "normal")
            fonts[style_name] = (family, size, weight)
        
        # 添加标题字体
        fonts["header"] = self.get_header_font(validate=validate)
        
        return fonts
    
    def get_title_color(self) -> str:
        """
        获取标题颜色
        
        Returns:
            颜色值（十六进制字符串）
        """
        return self._config.get("title_color", "#2c3e50")
    
    def get_config(self) -> Dict:
        """
        获取原始配置字典
        
        Returns:
            配置字典
        """
        return self._config.copy()


# 全局单例实例（延迟初始化）
_font_loader: Optional[FontLoader] = None


def get_font_loader() -> FontLoader:
    """
    获取全局字体加载器实例
    
    Returns:
        FontLoader 实例
    """
    global _font_loader
    if _font_loader is None:
        _font_loader = FontLoader()
    return _font_loader


# 便捷函数
def get_fonts() -> Dict[str, Tuple[str, int, str]]:
    """获取所有字体配置"""
    return get_font_loader().get_all_fonts()


def get_font_family() -> str:
    """获取当前平台的字体族"""
    return get_font_loader().get_font_family()


if __name__ == "__main__":
    # 测试代码
    loader = FontLoader()
    print(f"\n当前平台: {loader.get_platform()}")
    print(f"主字体族: {loader.get_font_family()}")
    print(f"标题字体: {loader.get_header_font_family()}")
    print(f"标题颜色: {loader.get_title_color()}")
    print("\n所有字体配置:")
    for name, config in loader.get_all_fonts().items():
        print(f"  {name}: {config}")
