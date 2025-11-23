"""
多场景GUI简单测试
"""

import tkinter as tk
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gui.settings_panel import SettingsPanel


def test_gui():
    """测试多场景GUI"""
    root = tk.Tk()
    root.title("多场景配置测试")
    root.geometry("1000x666")

    # 创建设置面板
    panel = SettingsPanel(root)

    # 添加测试按钮
    test_frame = tk.Frame(root)
    test_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

    def show_selected():
        """显示选中的场景"""
        scenes = panel.get_selected_scenes()
        config = panel.get_scene_config()

        msg = f"选中的场景: {scenes}\n"
        msg += f"scene_type（兼容）: {config['scene_type']}\n"
        msg += f"selected_scenes: {config['selected_scenes']}"

        tk.messagebox.showinfo("当前配置", msg)

    tk.Button(
        test_frame, text="查看选中场景", command=show_selected, font=("Arial", 12)
    ).pack(side=tk.LEFT, padx=5)

    def set_multi():
        """设置多个场景"""
        success = panel.set_selected_scenes(["摔倒", "起火"])
        if success:
            tk.messagebox.showinfo("成功", "已设置场景为：摔倒、起火")
        else:
            tk.messagebox.showerror("失败", "设置失败")

    tk.Button(
        test_frame,
        text="设置多场景（摔倒+起火）",
        command=set_multi,
        font=("Arial", 12),
    ).pack(side=tk.LEFT, padx=5)

    root.mainloop()


if __name__ == "__main__":
    test_gui()
