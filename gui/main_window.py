# TODO: GUI主窗口（拓展功能）
#
# 功能说明：
# 1. 使用Tkinter创建主窗口
# 2. 显示实时视频预览
# 3. 显示检测结果和警报信息
# - MainWindow: 主窗口类
#
# 开发优先级：⭐ (第10-11周完成)
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
from PIL import Image, ImageTk
import cv2

# 创建主窗口
root = tk.Tk()
root.title("主窗口 - 实时视频预览与检测")

# 获取屏幕宽高
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 设置窗口大小为屏幕的 70%
TARGET_WIDTH = int(screen_width * 0.7)
TARGET_HEIGHT = int(screen_height * 0.7)
ASPECT_RATIO = TARGET_WIDTH / TARGET_HEIGHT
VIDEO_RATIO = 16 / 9

# 计算居中位置
center_x = int((screen_width - TARGET_WIDTH) / 2)
center_y = int((screen_height - TARGET_HEIGHT) / 2)

# 设置窗口大小和位置
INITIAL_GEOMETRY = f"{TARGET_WIDTH}x{TARGET_HEIGHT}+{center_x}+{center_y}"
root.geometry(INITIAL_GEOMETRY)

# 允许缩放并设置最小尺寸
root.resizable(True, True)
root.minsize(320, int(320 / ASPECT_RATIO))

# 改一个可爱滴图标
icon = Image.open("gui/kawaii_icon.png")
root.wm_iconphoto(True, ImageTk.PhotoImage(icon))

# 配置主窗口的网格布局
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# 创建主框架，添加内边距让界面更舒适
main_frame = ttk.Frame(root, padding="20")
main_frame.grid(row=0, column=0, sticky="nsew")
main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# 创建视频显示区域的框架
video_frame = ttk.LabelFrame(main_frame, text="📹 实时视频预览", padding="10")
video_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

# 创建Canvas用于显示视频
video_canvas = tk.Canvas(
    video_frame,
    bg="#2b2b2b",  # 深灰色背景
    highlightthickness=2,
    highlightbackground="#4a4a4a",
)
video_canvas.pack(padx=5, pady=5, expand=True)

# 在Canvas中央显示提示文字
placeholder_text = video_canvas.create_text(
    0,
    0,
    text="等待视频输入...\n\n点击下方按钮开始检测",
    font=("Arial", 16),
    fill="#888888",
    justify="center",
)

# 创建控制按钮区域
control_frame = ttk.Frame(main_frame)
control_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
control_frame.grid_columnconfigure(0, weight=1)
control_frame.grid_columnconfigure(2, weight=1)

button_container = ttk.Frame(control_frame)
button_container.grid(row=0, column=1)

# 添加控制按钮
btn_start = ttk.Button(button_container, text="▶ 开始检测", width=15)
btn_start.pack(side="left", padx=5)

btn_pause = ttk.Button(button_container, text="⏸ 暂停", width=15)
btn_pause.pack(side="left", padx=5)

btn_stop = ttk.Button(button_container, text="⏹ 停止", width=15)
btn_stop.pack(side="left", padx=5)

btn_settings = ttk.Button(button_container, text="⚙ 设置", width=15)
btn_settings.pack(side="left", padx=5)


_resize_state = {
    "width": TARGET_WIDTH,
    "height": TARGET_HEIGHT,
    "lock": False,
    "initialized": False,
}


def _update_video_layout(window_width: int, window_height: int) -> None:
    """Compute a comfortable canvas size that preserves the 16:9 ratio."""
    available_width = max(320, window_width - 160)
    available_height = max(180, window_height - 240)

    width_from_height = int(available_height * VIDEO_RATIO)
    canvas_width = min(available_width, width_from_height)
    canvas_height = int(canvas_width / VIDEO_RATIO)

    video_canvas.config(width=canvas_width, height=canvas_height)
    video_canvas.coords(
        placeholder_text,
        canvas_width // 2,
        canvas_height // 2,
    )


def _ensure_initial_geometry() -> None:
    if not _resize_state["initialized"]:
        _resize_state["lock"] = True
        root.geometry(INITIAL_GEOMETRY)
        root.update_idletasks()
        actual_width = root.winfo_width()
        actual_height = root.winfo_height()
        _resize_state.update(
            {
                "width": actual_width,
                "height": actual_height,
                "initialized": True,
            }
        )
        _update_video_layout(actual_width, actual_height)
        _resize_state["lock"] = False


def _on_window_resize(event: tk.Event) -> None:
    if event.widget is not root or _resize_state["lock"]:
        return

    if not _resize_state["initialized"]:
        _ensure_initial_geometry()
        return

    new_width, new_height = event.width, event.height
    if new_width <= 0 or new_height <= 0:
        return

    if new_width == _resize_state["width"] and new_height == _resize_state["height"]:
        return

    desired_height = int(new_width / ASPECT_RATIO)
    desired_width = int(new_height * ASPECT_RATIO)

    width_delta = abs(new_width - _resize_state["width"])
    height_delta = abs(new_height - _resize_state["height"])

    if width_delta >= height_delta:
        target_width = new_width
        target_height = max(200, desired_height)
    else:
        target_height = new_height
        target_width = max(320, desired_width)

    _resize_state["lock"] = True
    root.geometry(f"{target_width}x{target_height}")
    _resize_state["lock"] = False

    _resize_state["width"] = target_width
    _resize_state["height"] = target_height

    _update_video_layout(target_width, target_height)


root.bind("<Configure>", _on_window_resize)
root.after_idle(_ensure_initial_geometry)


# 关闭窗口后释放程序资源
def _on_window_close() -> None:
    """Ensure the GUI shutdown also terminates the interpreter."""
    try:
        root.quit()
        root.destroy()
    finally:
        sys.exit(0)


root.protocol("WM_DELETE_WINDOW", _on_window_close)

root.mainloop()
