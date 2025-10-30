# TODO: GUI主窗口（拓展功能）
#
# 功能说明：
# 1. 使用Tkinter创建主窗口
# 2. 显示实时视频预览
# 3. 显示检测结果和警报信息
# 4. 提供场景配置界面
#
# 主要类：
# - MainWindow: 主窗口类
#
# 开发优先级：⭐ (第10-11周完成)

import sys
import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional
from PIL import Image, ImageTk
import cv2


class MainWindow:
    """DLC检测系统主窗口类"""

    # 类常量
    VIDEO_RATIO = 16 / 9  # 视频显示比例
    SCREEN_RATIO = 0.7  # 窗口占屏幕比例

    def __init__(self) -> None:
        """初始化主窗口"""
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("主窗口 - 实时视频预览与检测")

        # 获取屏幕尺寸
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # 计算窗口尺寸
        self.target_width = int(self.screen_width * self.SCREEN_RATIO)
        self.target_height = int(self.screen_height * self.SCREEN_RATIO)
        self.aspect_ratio = self.target_width / self.target_height

        # 缩放状态跟踪
        self._resize_state: Dict[str, any] = {
            "width": self.target_width,
            "height": self.target_height,
            "lock": False,
            "initialized": False,
        }

        # 初始化GUI组件
        self._setup_window()
        self._setup_icon()
        self._create_widgets()
        self._bind_events()

        # 确保初始几何形状
        self.root.after_idle(self._ensure_initial_geometry)

    def _setup_window(self) -> None:
        """配置窗口基本属性"""
        # 计算居中位置
        center_x = int((self.screen_width - self.target_width) / 2)
        center_y = int((self.screen_height - self.target_height) / 2)

        # 设置窗口大小和位置
        geometry = f"{self.target_width}x{self.target_height}+{center_x}+{center_y}"
        self.root.geometry(geometry)

        # 允许缩放并设置最小尺寸
        self.root.resizable(True, True)
        min_height = int(320 / self.aspect_ratio)
        self.root.minsize(320, min_height)

        # 配置网格布局
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _setup_icon(self) -> None:
        """设置窗口图标"""
        try:
            icon = Image.open("gui/kawaii_icon.png")
            photo = ImageTk.PhotoImage(icon)
            self.root.wm_iconphoto(True, photo)
        except Exception as e:
            print(f"无法加载图标: {e}")

    def _create_widgets(self) -> None:
        """创建所有GUI组件"""
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 创建视频显示区域
        self._create_video_frame()

        # 创建控制按钮区域
        self._create_control_buttons()

    def _create_video_frame(self) -> None:
        """创建视频显示区域"""
        # 视频框架
        self.video_frame = ttk.LabelFrame(
            self.main_frame, text="📹 实时视频预览", padding="10"
        )
        self.video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # 视频画布
        self.video_canvas = tk.Canvas(
            self.video_frame,
            bg="#2b2b2b",
            highlightthickness=2,
            highlightbackground="#4a4a4a",
        )
        self.video_canvas.pack(padx=5, pady=5, expand=True)

        # 占位提示文字
        self.placeholder_text = self.video_canvas.create_text(
            0,
            0,
            text="等待视频输入...\n\n点击下方按钮开始检测",
            font=("Arial", 16),
            fill="#888888",
            justify="center",
        )

    def _create_control_buttons(self) -> None:
        """创建控制按钮"""
        # 控制按钮框架
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)

        # 按钮容器（用于居中）
        button_container = ttk.Frame(control_frame)
        button_container.grid(row=0, column=1)

        # 创建按钮
        self.btn_start = ttk.Button(
            button_container,
            text="▶ 开始检测",
            width=15,
            command=self._on_start_detection,
        )
        self.btn_start.pack(side="left", padx=5)

        self.btn_pause = ttk.Button(
            button_container, text="⏸ 暂停", width=15, command=self._on_pause
        )
        self.btn_pause.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(
            button_container, text="⏹ 停止", width=15, command=self._on_stop
        )
        self.btn_stop.pack(side="left", padx=5)

        self.btn_settings = ttk.Button(
            button_container, text="⚙ 设置", width=15, command=self._on_settings
        )
        self.btn_settings.pack(side="left", padx=5)

    def _bind_events(self) -> None:
        """绑定事件处理器"""
        self.root.bind("<Configure>", self._on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _update_video_layout(self, window_width: int, window_height: int) -> None:
        """更新视频画布布局以保持16:9比例"""
        available_width = max(320, window_width - 160)
        available_height = max(180, window_height - 240)

        width_from_height = int(available_height * self.VIDEO_RATIO)
        canvas_width = min(available_width, width_from_height)
        canvas_height = int(canvas_width / self.VIDEO_RATIO)

        self.video_canvas.config(width=canvas_width, height=canvas_height)
        self.video_canvas.coords(
            self.placeholder_text,
            canvas_width // 2,
            canvas_height // 2,
        )

    def _ensure_initial_geometry(self) -> None:
        """确保窗口以正确的初始尺寸显示"""
        if not self._resize_state["initialized"]:
            self._resize_state["lock"] = True

            # 强制更新几何形状
            center_x = int((self.screen_width - self.target_width) / 2)
            center_y = int((self.screen_height - self.target_height) / 2)
            geometry = f"{self.target_width}x{self.target_height}+{center_x}+{center_y}"
            self.root.geometry(geometry)
            self.root.update_idletasks()

            # 获取实际尺寸
            actual_width = self.root.winfo_width()
            actual_height = self.root.winfo_height()

            # 更新状态
            self._resize_state.update(
                {
                    "width": actual_width,
                    "height": actual_height,
                    "initialized": True,
                }
            )

            # 更新视频布局
            self._update_video_layout(actual_width, actual_height)
            self._resize_state["lock"] = False

    def _on_window_resize(self, event: tk.Event) -> None:
        """窗口缩放事件处理器，保持窗口宽高比"""
        if event.widget is not self.root or self._resize_state["lock"]:
            return

        if not self._resize_state["initialized"]:
            self._ensure_initial_geometry()
            return

        new_width, new_height = event.width, event.height
        if new_width <= 0 or new_height <= 0:
            return

        if (
            new_width == self._resize_state["width"]
            and new_height == self._resize_state["height"]
        ):
            return

        # 计算目标尺寸
        desired_height = int(new_width / self.aspect_ratio)
        desired_width = int(new_height * self.aspect_ratio)

        # 根据拉伸方向决定基准
        width_delta = abs(new_width - self._resize_state["width"])
        height_delta = abs(new_height - self._resize_state["height"])

        if width_delta >= height_delta:
            target_width = new_width
            target_height = max(200, desired_height)
        else:
            target_height = new_height
            target_width = max(320, desired_width)

        # 更新窗口尺寸
        self._resize_state["lock"] = True
        self.root.geometry(f"{target_width}x{target_height}")
        self._resize_state["lock"] = False

        # 更新状态
        self._resize_state["width"] = target_width
        self._resize_state["height"] = target_height

        # 更新视频布局
        self._update_video_layout(target_width, target_height)

    def _on_start_detection(self) -> None:
        """开始检测按钮回调"""
        print("开始检测...")
        # TODO: 实现检测逻辑

    def _on_pause(self) -> None:
        """暂停按钮回调"""
        print("暂停检测...")
        # TODO: 实现暂停逻辑

    def _on_stop(self) -> None:
        """停止按钮回调"""
        print("停止检测...")
        # TODO: 实现停止逻辑

    def _on_settings(self) -> None:
        """设置按钮回调"""
        print("打开设置...")
        # TODO: 实现设置界面

    def _on_window_close(self) -> None:
        """窗口关闭事件处理器"""
        try:
            self.root.quit()
            self.root.destroy()
        finally:
            sys.exit(0)

    def run(self) -> None:
        """运行主窗口"""
        self.root.mainloop()


def main() -> None:
    """程序入口"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
