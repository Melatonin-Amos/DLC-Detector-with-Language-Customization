"""
测试多场景选择功能

展示如何使用新的多场景接口
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def test_multi_scene_config():
    """测试多场景配置（无需GUI）"""
    print("=" * 60)
    print("测试多场景配置功能")
    print("=" * 60)

    # 模拟 app_config（与 SettingsPanel 共享的配置字典）
    app_config = {
        "scene": {
            "scene_type": "摔倒",
            "selected_scenes": ["摔倒"],  # 新增：多场景选择
            "light_condition": "normal",
            "enable_roi": False,
            "enable_sound": True,
            "enable_email": False,
            "auto_record": False,
        },
        "scene_types": ["摔倒", "起火", "闯入"],
    }

    print("\n初始配置:")
    print(f"  选中场景: {app_config['scene']['selected_scenes']}")
    print(f"  scene_type（兼容）: {app_config['scene']['scene_type']}")

    # 模拟用户选择多个场景
    print("\n用户选择多个场景: ['摔倒', '起火']")
    app_config["scene"]["selected_scenes"] = ["摔倒", "起火"]
    app_config["scene"]["scene_type"] = "摔倒"  # 第一个

    print(f"  选中场景: {app_config['scene']['selected_scenes']}")
    print(f"  scene_type（兼容）: {app_config['scene']['scene_type']}")

    # 检测模块使用示例
    print("\n" + "=" * 60)
    print("检测模块使用示例")
    print("=" * 60)

    selected_scenes = app_config["scene"]["selected_scenes"]
    print(f"\n检测系统获取选中的场景: {selected_scenes}")

    # 为每个选中的场景执行检测
    prompts_map = {
        "摔倒": ["person falling", "person on ground"],
        "起火": ["fire", "flames", "smoke"],
        "闯入": ["person entering", "unauthorized person"],
    }

    print("\n为每个场景生成检测提示词:")
    for scene in selected_scenes:
        prompts = prompts_map.get(scene, [])
        print(f"  {scene}: {prompts}")

    # 向后兼容性测试
    print("\n" + "=" * 60)
    print("向后兼容性测试")
    print("=" * 60)

    # 旧代码仍然可以工作
    first_scene = app_config["scene"]["scene_type"]
    print(f"\n旧接口 scene_type: {first_scene}")
    print(f"新接口 selected_scenes: {app_config['scene']['selected_scenes']}")
    print("\n✓ 向后兼容，旧代码仍可正常工作")

    # 新增场景
    print("\n" + "=" * 60)
    print("添加新场景")
    print("=" * 60)

    app_config["scene_types"].append("打架")
    print(f"\n所有场景: {app_config['scene_types']}")

    app_config["scene"]["selected_scenes"].append("打架")
    print(f"选中场景: {app_config['scene']['selected_scenes']}")

    print("\n" + "=" * 60)
    print("✓ 测试完成")
    print("=" * 60)


if __name__ == "__main__":
    test_multi_scene_config()
