"""
SettingsPanel 对外接口使用示例

本示例演示如何使用 SettingsPanel 类的公开接口获取和设置用户配置。
适用于需要与 GUI 集成的其他模块开发者。

作者: LXR
日期: 2025年11月11日
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import tkinter as tk
from gui.settings_panel import SettingsPanel


def example_1_get_scene_config():
    """示例1: 获取当前场景配置"""
    print("=" * 60)
    print("示例1: 获取当前场景配置")
    print("=" * 60)

    # 直接使用配置字典测试（无需创建GUI）
    test_config = {
        "scene": {
            "scene_type": "摔倒",
            "light_condition": "normal",
            "enable_roi": False,
            "enable_sound": True,
            "enable_email": False,
            "auto_record": False,
        },
        "scene_types": ["摔倒", "起火"],
    }

    # 模拟SettingsPanel的接口
    class MockPanel:
        def __init__(self, config):
            self.app_config = config
            self.scene_types = config["scene_types"]

        def get_scene_config(self):
            return self.app_config["scene"].copy()

        def get_current_scene_type(self):
            return self.app_config["scene"]["scene_type"]

        def get_light_condition(self):
            return self.app_config["scene"]["light_condition"]

        def get_roi_settings(self):
            return {
                "enabled": self.app_config["scene"]["enable_roi"],
                "coordinates": None,
            }

        def get_alert_settings(self):
            return {
                "sound": self.app_config["scene"]["enable_sound"],
                "email": self.app_config["scene"]["enable_email"],
                "record": self.app_config["scene"]["auto_record"],
            }

    panel = MockPanel(test_config)

    # 获取完整配置
    config = panel.get_scene_config()
    print(f"\n完整场景配置:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    # 获取单独的配置项
    print(f"\n单独获取配置项:")
    print(f"  当前场景: {panel.get_current_scene_type()}")
    print(f"  光照条件: {panel.get_light_condition()}")
    print(f"  ROI设置: {panel.get_roi_settings()}")
    print(f"  报警设置: {panel.get_alert_settings()}")


def example_2_set_scene_config():
    """示例2: 以编程方式设置场景配置"""
    print("\n" + "=" * 60)
    print("示例2: 以编程方式设置场景配置")
    print("=" * 60)

    root = tk.Tk()
    root.withdraw()

    panel = SettingsPanel(root)

    # 方式1: 使用 update_scene_config 批量更新
    print("\n方式1: 批量更新配置")
    panel.update_scene_config(
        {
            "scene_type": "起火",
            "light_condition": "bright",
            "enable_sound": True,
            "enable_email": True,
            "auto_record": True,
        }
    )
    print(f"  更新后的配置: {panel.get_scene_config()}")

    # 方式2: 使用单独的setter方法
    print("\n方式2: 使用单独方法")
    success = panel.set_scene_type("摔倒")
    print(f"  切换场景到'摔倒': {'成功' if success else '失败'}")
    print(f"  当前场景: {panel.get_current_scene_type()}")

    root.destroy()


def example_3_add_custom_scene():
    """示例3: 添加自定义场景类型"""
    print("\n" + "=" * 60)
    print("示例3: 添加自定义场景类型")
    print("=" * 60)

    root = tk.Tk()
    root.withdraw()

    panel = SettingsPanel(root)

    print(f"\n初始场景列表: {panel.get_all_scene_types()}")

    # 添加新场景
    new_scenes = ["闯入", "打架", "人员聚集"]
    for scene in new_scenes:
        success = panel.add_scene_type(scene)
        print(f"  添加场景 '{scene}': {'成功' if success else '失败'}")

    print(f"\n更新后的场景列表: {panel.get_all_scene_types()}")

    # 切换到新场景
    panel.set_scene_type("闯入")
    print(f"\n当前选中场景: {panel.get_current_scene_type()}")

    root.destroy()


def example_4_integration_with_detector():
    """示例4: 与检测模块集成"""
    print("\n" + "=" * 60)
    print("示例4: 与检测模块集成")
    print("=" * 60)

    root = tk.Tk()
    root.withdraw()

    panel = SettingsPanel(root)

    # 模拟检测流程
    print("\n模拟检测流程:")

    # 1. 获取当前场景
    scene_type = panel.get_current_scene_type()
    print(f"\n  1. 获取场景类型: {scene_type}")

    # 2. 根据光照条件调整检测参数
    light_condition = panel.get_light_condition()
    print(f"  2. 获取光照条件: {light_condition}")

    # 模拟调整检测阈值
    threshold_map = {"bright": 0.3, "normal": 0.25, "dim": 0.2}
    threshold = threshold_map.get(light_condition, 0.25)
    print(f"     → 调整检测阈值为: {threshold}")

    # 3. 检查是否启用ROI
    roi_settings = panel.get_roi_settings()
    print(f"  3. ROI设置: {roi_settings}")
    if roi_settings["enabled"]:
        print("     → 将在ROI区域内进行检测")
    else:
        print("     → 在整个画面进行检测")

    # 4. 处理检测结果（模拟）
    alert_settings = panel.get_alert_settings()
    print(f"\n  4. 报警设置: {alert_settings}")

    # 模拟检测到事件
    detected = True
    if detected:
        print("\n  ⚠️  检测到事件: " + scene_type)
        if alert_settings["sound"]:
            print("     → 播放声音报警")
        if alert_settings["email"]:
            print("     → 发送邮件通知")
        if alert_settings["record"]:
            print("     → 开始自动录像")

    root.destroy()


def example_5_config_persistence():
    """示例5: 配置持久化（与主窗口共享配置）"""
    print("\n" + "=" * 60)
    print("示例5: 配置持久化")
    print("=" * 60)

    root = tk.Tk()
    root.withdraw()

    # 创建共享配置字典（模拟主窗口的 app_config）
    shared_config = {
        "scene": {
            "scene_type": "摔倒",
            "light_condition": "normal",
            "enable_roi": False,
            "enable_sound": True,
            "enable_email": False,
            "auto_record": False,
        },
        "scene_types": ["摔倒", "起火"],
    }

    print("\n初始共享配置:")
    print(f"  {shared_config['scene']}")

    # 创建设置面板并传入共享配置
    panel = SettingsPanel(root, app_config=shared_config)

    # 修改配置
    panel.update_scene_config(
        {
            "scene_type": "起火",
            "light_condition": "bright",
            "enable_email": True,
            "auto_record": True,
        }
    )

    # 保存配置（这会更新 shared_config）
    panel._save_scene_config()

    print("\n修改后的共享配置:")
    print(f"  {shared_config['scene']}")
    print("\n✓ 配置已通过引用传递同步到主窗口")

    root.destroy()


def example_6_real_world_usage():
    """示例6: 真实场景使用模式"""
    print("\n" + "=" * 60)
    print("示例6: 真实场景使用模式（推荐）")
    print("=" * 60)

    class DetectionSystem:
        """模拟的检测系统类"""

        def __init__(self, settings_panel: SettingsPanel):
            self.panel = settings_panel
            print("\n✓ 检测系统初始化完成")

        def process_frame(self, frame):
            """处理视频帧"""
            # 获取当前配置
            config = self.panel.get_scene_config()

            print(f"\n处理帧 - 场景: {config['scene_type']}")
            print(f"  光照: {config['light_condition']}")
            print(f"  ROI: {'启用' if config['enable_roi'] else '禁用'}")

            # 根据配置执行检测...
            # detection_result = self.detect(frame, config)

            # 根据报警设置触发警报
            alerts = self.panel.get_alert_settings()
            if alerts["sound"]:
                print("  → 已启用声音报警")
            if alerts["record"]:
                print("  → 已启用自动录像")

        def change_scene(self, scene_name: str):
            """切换检测场景"""
            success = self.panel.set_scene_type(scene_name)
            if success:
                print(f"\n✓ 场景已切换到: {scene_name}")
                # 可能需要重新加载模型或调整参数
                self.reload_model_for_scene(scene_name)
            else:
                print(f"\n✗ 场景切换失败: {scene_name} 不存在")

        def reload_model_for_scene(self, scene_name: str):
            """为特定场景重新加载模型"""
            print(f"  → 为场景 '{scene_name}' 重新加载检测模型...")

    # 使用示例
    root = tk.Tk()
    root.withdraw()

    # 创建设置面板
    panel = SettingsPanel(root)

    # 创建检测系统并注入设置面板
    system = DetectionSystem(panel)

    # 模拟处理视频帧
    system.process_frame(None)

    # 动态切换场景
    system.change_scene("起火")
    system.process_frame(None)

    root.destroy()


def main():
    """运行所有示例"""
    print("\n" + "🚀 " * 30)
    print("SettingsPanel 公开接口使用示例集")
    print("🚀 " * 30)

    example_1_get_scene_config()
    example_2_set_scene_config()
    example_3_add_custom_scene()
    example_4_integration_with_detector()
    example_5_config_persistence()
    example_6_real_world_usage()

    print("\n" + "=" * 60)
    print("✓ 所有示例运行完成")
    print("=" * 60)
    print(
        "\n建议:\n"
        "  1. 使用 get_scene_config() 获取完整配置\n"
        "  2. 使用 get_alert_settings() 获取报警设置\n"
        "  3. 使用 update_scene_config() 批量更新配置\n"
        "  4. 通过 app_config 实现配置持久化\n"
        "  5. 在检测循环中定期读取配置以支持动态切换\n"
    )


if __name__ == "__main__":
    main()
