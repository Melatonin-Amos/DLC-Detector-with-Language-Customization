"""
SettingsPanel API 简化示例（无需GUI）

展示如何通过 app_config 字典与 SettingsPanel 交互
适用于集成测试和理解接口设计

作者: LXR（李修然）
日期: 2025年11月11日
"""


def demo_read_config():
    """演示：读取用户配置"""
    print("=" * 60)
    print("示例1: 读取用户配置")
    print("=" * 60)

    # 模拟 app_config（与 SettingsPanel 共享的配置字典）
    app_config = {
        "scene": {
            "scene_type": "摔倒",
            "light_condition": "normal",
            "enable_roi": False,
            "enable_sound": True,
            "enable_email": False,
            "auto_record": False,
        },
        "scene_types": ["摔倒", "起火", "闯入"],
    }

    # 协作者通过接口获取配置
    print("\n✓ 获取完整场景配置:")
    scene_config = app_config["scene"]
    for key, value in scene_config.items():
        print(f"  {key}: {value}")

    print(f"\n✓ 当前场景类型: {app_config['scene']['scene_type']}")
    print(f"✓ 所有场景类型: {app_config['scene_types']}")
    print(f"✓ 光照条件: {app_config['scene']['light_condition']}")

    # 获取报警设置
    alert_settings = {
        "sound": app_config["scene"]["enable_sound"],
        "email": app_config["scene"]["enable_email"],
        "record": app_config["scene"]["auto_record"],
    }
    print(f"✓ 报警设置: {alert_settings}")


def demo_update_config():
    """演示：修改配置"""
    print("\n" + "=" * 60)
    print("示例2: 修改配置")
    print("=" * 60)

    app_config = {
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

    print("\n原始配置:")
    print(f"  场景: {app_config['scene']['scene_type']}")
    print(f"  光照: {app_config['scene']['light_condition']}")
    print(f"  声音报警: {app_config['scene']['enable_sound']}")

    # 模拟通过 update_scene_config() 修改
    updates = {
        "scene_type": "起火",
        "light_condition": "bright",
        "enable_sound": True,
        "enable_email": True,
    }

    for key, value in updates.items():
        app_config["scene"][key] = value

    print("\n✓ 更新后的配置:")
    print(f"  场景: {app_config['scene']['scene_type']}")
    print(f"  光照: {app_config['scene']['light_condition']}")
    print(f"  声音报警: {app_config['scene']['enable_sound']}")
    print(f"  邮件通知: {app_config['scene']['enable_email']}")


def demo_add_scene():
    """演示：添加新场景"""
    print("\n" + "=" * 60)
    print("示例3: 添加新场景")
    print("=" * 60)

    app_config = {
        "scene": {"scene_type": "摔倒", "light_condition": "normal"},
        "scene_types": ["摔倒", "起火"],
    }

    print(f"\n初始场景列表: {app_config['scene_types']}")

    # 模拟通过 add_scene_type() 添加
    new_scenes = ["闯入", "打架", "人员聚集"]
    for scene in new_scenes:
        if scene not in app_config["scene_types"]:
            app_config["scene_types"].append(scene)
            print(f"  ✓ 已添加场景: {scene}")
        else:
            print(f"  ✗ 场景已存在: {scene}")

    print(f"\n更新后的场景列表: {app_config['scene_types']}")


def demo_integration_with_detector():
    """演示：与检测模块集成"""
    print("\n" + "=" * 60)
    print("示例4: 与检测模块集成")
    print("=" * 60)

    app_config = {
        "scene": {
            "scene_type": "摔倒",
            "light_condition": "dim",
            "enable_roi": False,
            "enable_sound": True,
            "enable_email": False,
            "auto_record": True,
        },
        "scene_types": ["摔倒", "起火"],
    }

    print("\n🔍 开始检测流程...\n")

    # 1. 获取场景类型
    scene_type = app_config["scene"]["scene_type"]
    print(f"1. 场景类型: {scene_type}")

    # 2. 根据场景选择提示词
    prompts_map = {
        "摔倒": ["person falling down", "person lying on ground"],
        "起火": ["fire", "flames", "smoke"],
    }
    prompts = prompts_map.get(scene_type, [])
    print(f"   → 检测提示词: {prompts}")

    # 3. 根据光照调整阈值
    light_condition = app_config["scene"]["light_condition"]
    threshold_map = {"bright": 0.3, "normal": 0.25, "dim": 0.2}
    threshold = threshold_map.get(light_condition, 0.25)
    print(f"\n2. 光照条件: {light_condition}")
    print(f"   → 检测阈值: {threshold}")

    # 4. 检查ROI设置
    enable_roi = app_config["scene"]["enable_roi"]
    print(f"\n3. ROI设置: {'启用' if enable_roi else '禁用'}")
    if enable_roi:
        print("   → 仅在ROI区域内检测")
    else:
        print("   → 全画面检测")

    # 5. 模拟检测到事件
    detected = True
    if detected:
        print(f"\n⚠️  检测到事件: {scene_type}")

        # 根据报警设置触发警报
        if app_config["scene"]["enable_sound"]:
            print("   → 🔊 播放声音报警")

        if app_config["scene"]["enable_email"]:
            print("   → 📧 发送邮件通知")

        if app_config["scene"]["auto_record"]:
            print("   → 📹 开始自动录像")


def demo_config_persistence():
    """演示：配置持久化"""
    print("\n" + "=" * 60)
    print("示例5: 配置持久化（与主窗口共享）")
    print("=" * 60)

    # 主窗口创建共享配置
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

    print("\n主窗口的初始配置:")
    print(f"  场景: {shared_config['scene']['scene_type']}")
    print(f"  邮件: {shared_config['scene']['enable_email']}")

    # 模拟 SettingsPanel 修改配置（引用传递）
    print("\n用户在设置面板中修改配置...")
    shared_config["scene"]["scene_type"] = "起火"
    shared_config["scene"]["enable_email"] = True
    shared_config["scene"]["auto_record"] = True

    print("\n主窗口读取配置（自动同步）:")
    print(f"  场景: {shared_config['scene']['scene_type']}")
    print(f"  邮件: {shared_config['scene']['enable_email']}")
    print(f"  录像: {shared_config['scene']['auto_record']}")

    print("\n✓ 配置已通过引用传递自动同步")


def demo_real_world_usage():
    """演示：真实使用场景"""
    print("\n" + "=" * 60)
    print("示例6: 真实使用场景（推荐模式）")
    print("=" * 60)

    # 模拟完整的检测系统
    class DetectionSystem:
        def __init__(self, app_config):
            """
            初始化检测系统

            Args:
                app_config: 与 SettingsPanel 共享的配置字典
            """
            self.config = app_config
            print("\n✓ 检测系统初始化完成")

        def process_frame(self, frame_id):
            """处理视频帧"""
            # 获取当前配置
            scene = self.config["scene"]["scene_type"]
            light = self.config["scene"]["light_condition"]
            roi_enabled = self.config["scene"]["enable_roi"]

            print(f"\n处理帧 #{frame_id}")
            print(f"  场景: {scene}")
            print(f"  光照: {light}")
            print(f"  ROI: {'启用' if roi_enabled else '禁用'}")

            # 根据配置执行检测...
            # result = self.detect(frame, scene, light)

        def change_scene(self, new_scene):
            """动态切换场景"""
            if new_scene in self.config["scene_types"]:
                self.config["scene"]["scene_type"] = new_scene
                print(f"\n✓ 场景已切换到: {new_scene}")
                print("  → 重新加载检测模型...")
            else:
                print(f"\n✗ 场景不存在: {new_scene}")

    # 创建共享配置
    app_config = {
        "scene": {
            "scene_type": "摔倒",
            "light_condition": "normal",
            "enable_roi": False,
            "enable_sound": True,
            "enable_email": False,
            "auto_record": False,
        },
        "scene_types": ["摔倒", "起火", "闯入"],
    }

    # 创建检测系统并传入配置
    system = DetectionSystem(app_config)

    # 处理视频帧
    system.process_frame(1)

    # 用户在GUI中切换场景（配置自动同步）
    print("\n用户在设置面板中切换场景...")
    app_config["scene"]["scene_type"] = "起火"

    # 系统读取最新配置
    system.process_frame(2)

    # 也可以通过代码切换场景
    system.change_scene("闯入")
    system.process_frame(3)


def main():
    """运行所有示例"""
    print("\n" + "🚀 " * 30)
    print("SettingsPanel API 简化示例")
    print("（展示如何通过 app_config 字典获取用户输入）")
    print("🚀 " * 30)

    demo_read_config()
    demo_update_config()
    demo_add_scene()
    demo_integration_with_detector()
    demo_config_persistence()
    demo_real_world_usage()

    print("\n" + "=" * 60)
    print("✓ 所有示例运行完成")
    print("=" * 60)

    print("\n" + "📋 核心要点:")
    print("  1. SettingsPanel 通过 app_config 字典与外部通信")
    print("  2. 使用引用传递实现配置自动同步")
    print("  3. 公开接口封装了底层的 tkinter 变量")
    print("  4. 协作者只需读取 app_config 即可获取用户输入")
    print("  5. 在检测循环中定期读取配置支持热更新")

    print("\n" + "📖 详细文档:")
    print("  gui/SETTINGS_PANEL_API.md - 完整API参考文档")
    print("  examples/settings_panel_api_demo.py - 完整示例（需GUI）")


if __name__ == "__main__":
    main()
