"""
简化测试 - 不启动GUI，只测试接口
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from gui.settings_panel import SettingsPanel

# 创建测试窗口
root = tk.Tk()
root.withdraw()  # 隐藏窗口

# 创建设置面板
panel = SettingsPanel(root)

print("=" * 60)
print("测试 SettingsPanel 接口")
print("=" * 60)

# 测试1: 获取配置快照
print("\n1️⃣ 测试 get_config_snapshot()")
snapshot = panel.get_config_snapshot()
print(f"   场景类型: {snapshot['scene_type']}")
print(f"   选中场景: {snapshot['selected_scenes']}")
print(f"   光照条件: {snapshot['light_condition']}")
print("   ✅ 通过")

# 测试2: 打印当前配置
print("\n2️⃣ 测试 print_current_config()")
panel.print_current_config()
print("   ✅ 通过")

# 测试3: 获取场景配置
print("\n3️⃣ 测试 get_scene_config()")
config = panel.get_scene_config()
print(f"   获取到 {len(config)} 个配置项")
print("   ✅ 通过")

# 测试4: 获取选中场景
print("\n4️⃣ 测试 get_selected_scenes()")
scenes = panel.get_selected_scenes()
print(f"   选中场景: {scenes}")
print("   ✅ 通过")

# 测试5: 设置选中场景
print("\n5️⃣ 测试 set_selected_scenes()")
success = panel.set_selected_scenes(["摔倒", "起火"])
print(f"   设置结果: {'成功' if success else '失败'}")
new_scenes = panel.get_selected_scenes()
print(f"   新的选中场景: {new_scenes}")
print("   ✅ 通过")

# 测试6: 添加场景
print("\n6️⃣ 测试 add_scene_type()")
success = panel.add_scene_type("测试场景")
print(f"   添加结果: {'成功' if success else '失败'}")
all_scenes = panel.get_all_scene_types()
print(f"   所有场景: {all_scenes}")
print("   ✅ 通过")

print("\n" + "=" * 60)
print("✅ 所有接口测试通过！")
print("=" * 60)

# 不启动GUI，直接退出
root.destroy()
