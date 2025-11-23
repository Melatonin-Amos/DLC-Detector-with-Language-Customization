#!/usr/bin/env python3
"""测试图标加载功能"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import Image, ImageTk
import tkinter as tk

def test_icon_loading():
    """测试图标是否能正确加载"""
    print("="*50)
    print("测试图标加载功能")
    print("="*50)
    
    # 测试1: 检查图标文件是否存在
    icon_path = os.path.join(os.path.dirname(__file__), "gui", "kawaii_icon.png")
    if os.path.exists(icon_path):
        print(f"✅ 图标文件存在: {icon_path}")
    else:
        print(f"❌ 图标文件不存在: {icon_path}")
        return False
    
    # 测试2: 尝试用PIL打开图标
    try:
        icon = Image.open(icon_path)
        print(f"✅ PIL成功打开图标，尺寸: {icon.size}")
    except Exception as e:
        print(f"❌ PIL无法打开图标: {e}")
        return False
    
    # 测试3&4: 在Tkinter窗口中测试
    try:
        root = tk.Tk()
        root.withdraw()  # 隐藏窗口
        
        # 转换为ImageTk格式
        photo = ImageTk.PhotoImage(icon)
        print(f"✅ 成功转换为ImageTk.PhotoImage")
        
        # 设置图标
        root.wm_iconphoto(True, photo)
        print(f"✅ 成功在Tkinter窗口中设置图标")
        
        root.destroy()
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False
    
    print("="*50)
    print("🎉 所有测试通过！图标加载功能正常！")
    print("="*50)
    return True

if __name__ == "__main__":
    success = test_icon_loading()
    sys.exit(0 if success else 1)
