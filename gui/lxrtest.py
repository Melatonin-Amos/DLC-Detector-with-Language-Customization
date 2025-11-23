import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.main_window import MainWindow

# 创建主窗口实例
gui = MainWindow()
gui.root.title("场景配置测试")

# 获取配置信息
current_scene = gui.app_config["scene"]["scene_type"]
scene_types = gui.app_config["scene_types"]

print("=" * 50)
print("GUI 窗口已启动")
print("=" * 50)
print(f"✅ 当前场景: {current_scene}")
print(f"✅ 可用场景: {scene_types}")
print("=" * 50)
print("提示：关闭窗口以退出程序")
print("=" * 50)

# 启动主循环（这是关键！）
gui.run()
