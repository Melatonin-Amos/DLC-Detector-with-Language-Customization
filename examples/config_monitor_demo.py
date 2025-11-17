"""
配置监听功能演示

展示如何使用 SettingsPanel 的配置监听接口
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import MainWindow
from typing import Dict


def on_config_change(old_config: Dict, new_config: Dict):
    """
    配置变化回调函数

    Args:
        old_config: 变化前的配置
        new_config: 变化后的配置
    """
    print("\n" + "💡" * 30)
    print("自定义回调函数被触发！")
    print("💡" * 30)

    # 场景变化处理
    if old_config.get("scene_type") != new_config.get("scene_type"):
        print(
            f"✅ 检测到场景切换: {old_config.get('scene_type')} → {new_config.get('scene_type')}"
        )
        print("   → 可以在这里重新加载检测模型")

    # 多场景选择变化
    old_scenes = set(old_config.get("selected_scenes", []))
    new_scenes = set(new_config.get("selected_scenes", []))
    if old_scenes != new_scenes:
        added = new_scenes - old_scenes
        removed = old_scenes - new_scenes
        if added:
            print(f"✅ 新增场景: {', '.join(added)}")
            print(f"   → 可以为新场景加载提示词")
        if removed:
            print(f"✅ 移除场景: {', '.join(removed)}")
            print(f"   → 可以卸载场景资源")

    # 摄像头变化
    if old_config.get("camera_id") != new_config.get("camera_id"):
        print(
            f"✅ 摄像头切换: {old_config.get('camera_id')} → {new_config.get('camera_id')}"
        )
        print("   → 可以重启视频流")

    # 报警设置变化
    if old_config.get("enable_sound") != new_config.get("enable_sound"):
        status = "启用" if new_config.get("enable_sound") else "禁用"
        print(f"✅ 声音报警已{status}")

    if old_config.get("enable_email") != new_config.get("enable_email"):
        status = "启用" if new_config.get("enable_email") else "禁用"
        print(f"✅ 邮件通知已{status}")

    print("💡" * 30 + "\n")


def main():
    """主函数"""
    # 创建主窗口
    gui = MainWindow()

    # 打印初始配置
    print("\n" + "=" * 70)
    print("🚀 配置监听演示程序启动")
    print("=" * 70)
    print("\n📋 初始配置:")
    gui.settings_panel.print_current_config()

    # 启动配置监听
    print("🔧 启动配置监听器...")
    gui.settings_panel.start_config_monitor(
        callback=on_config_change,  # 自定义回调函数
        interval=500,  # 每500ms检查一次
        print_changes=True,  # 自动打印配置变化详情
        print_full_config=True,  # 变化时打印完整配置
    )

    print("✅ 配置监听器已启动！")
    print("\n" + "💡" * 35)
    print("提示:")
    print("  1. 在GUI中修改任何配置，终端会自动显示变化")
    print("  2. 系统会先打印变化详情，再打印完整配置")
    print("  3. 然后触发自定义回调函数 on_config_change()")
    print("  4. 你可以在回调函数中添加自己的处理逻辑")
    print("💡" * 35 + "\n")

    # 演示手动获取配置快照
    print("📸 手动获取配置快照示例:")
    snapshot = gui.settings_panel.get_config_snapshot()
    print(f"  当前场景: {snapshot['scene_type']}")
    print(f"  选中场景: {snapshot['selected_scenes']}")
    print(f"  光照条件: {snapshot['light_condition']}")
    print(f"  声音报警: {'启用' if snapshot['enable_sound'] else '禁用'}")
    print()

    # 启动GUI
    gui.run()


if __name__ == "__main__":
    main()
