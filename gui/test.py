import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from gui.settings_panel import SettingsPanel
from gui.main_window import MainWindow
from typing import Dict, Any

# 创建主窗口实例
gui = MainWindow()


# 定义配置变化回调函数
def on_config_change(old_config: Dict, new_config: Dict):
    """
    当配置发生变化时的回调函数

    Args:
        old_config: 变化前的配置
        new_config: 变化后的配置
    """
    # 这里可以添加自定义的处理逻辑
    print("\n💡 自定义回调: 配置已更新！")

    # 示例：检测场景是否变化
    if old_config.get("scene_type") != new_config.get("scene_type"):
        print(f"   ➜ 场景已切换，可能需要重新加载检测模型")

    # 示例：检测选中场景列表变化
    old_scenes = set(old_config.get("selected_scenes", []))
    new_scenes = set(new_config.get("selected_scenes", []))
    if old_scenes != new_scenes:
        print(f"   ➜ 场景选择已更新，当前启用 {len(new_scenes)} 个场景")


# 打印初始配置
print("\n" + "🚀" * 30)
print("系统启动 - 初始配置")
print("🚀" * 30)
gui.settings_panel.print_current_config()

# 启动配置监听（使用SettingsPanel的接口）
gui.settings_panel.start_config_monitor(
    callback=on_config_change,
    interval=500,  # 每500毫秒检查一次
    print_changes=True,  # 自动打印配置变化
    print_full_config=True,  # 变化时打印完整配置
)

print("💡 提示: 在GUI中修改任何配置，终端会自动显示变化详情")
print("💡 提示: 配置监听器已启动，每500ms检查一次配置变化\n")

# 启动GUI
gui.run()
