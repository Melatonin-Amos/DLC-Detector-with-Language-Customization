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
import os

# 添加项目根目录到 Python 路径（必须在其他导入之前）
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, Optional
from PIL import Image, ImageTk
import cv2
import numpy as np

try:
    from ttkthemes import ThemedTk

    HAS_THEMES = True
except ImportError:
    HAS_THEMES = False
    print("⚠️ ttkthemes 未安装，使用默认主题")

from gui.settings_panel import SettingsPanel
from src.utils.config_updater import ConfigUpdater
from src.utils.font_loader import FontLoader


class MainWindow:
    """DLC检测系统主窗口类"""

    # 类常量
    VIDEO_RATIO = 16 / 9  # 视频显示比例
    SCREEN_RATIO = 0.75  # 窗口占屏幕比例
    VIDEO_CANVAS_WIDTH = 880  # 固定视频画布宽度（加大）
    VIDEO_CANVAS_HEIGHT = 495  # 固定视频画布高度（16:9）
    ALERT_PANEL_WIDTH = 250  # 警报面板宽度（加宽）

    def __init__(self) -> None:
        """初始化主窗口"""
        # 创建主窗口（使用主题）
        if HAS_THEMES:
            self.root = ThemedTk(theme="arc")
        else:
            self.root = tk.Tk()

        self.root.title("DLC检测系统 - 智能养老监护")

        # 初始化字体配置
        self._setup_fonts()

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

        # 设置窗口引用
        self.settings_window: Optional[tk.Toplevel] = None
        self.settings_panel: Optional[SettingsPanel] = None

        # 配置更新器
        try:
            self.config_updater = ConfigUpdater()
        except Exception as e:
            print(f"⚠️  配置更新器初始化失败: {e}")
            self.config_updater = None

        # 持久化配置数据
        self.app_config = {
            "video": {
                "default_path": "",
                "auto_play": True,
                "loop_play": False,
                "default_speed": "1.0",
            },
            "camera": {
                "camera_index": "0",
                "resolution": "1280x720",
            },
            "scene": {
                "scene_type": "摔倒",
                "selected_scenes": ["摔倒"],
                "light_condition": "normal",
                "enable_email": False,
            },
            "scene_types": ["摔倒", "起火", "正常"],
        }

        # 视频流相关变量
        self.video_capture: Optional[cv2.VideoCapture] = None
        self.video_stream = None
        self.detector = None
        self.alert_manager = None
        self.extract_interval = 1.0
        self.last_detect_time = 0
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.update_id: Optional[str] = None

        # 本地视频相关
        self.current_video_path: Optional[str] = None
        self.is_local_video: bool = False
        self.video_total_frames: int = 0
        self.video_fps: float = 30.0
        self.current_frame_pos: int = 0
        self.playback_speed: float = 1.0
        self.video_finished: bool = False

        # 警报相关变量
        self.is_alert_active: bool = False  # 是否有警报
        self.alert_flash_id: Optional[str] = None  # 闪烁定时器ID
        self.alert_flash_state: bool = False  # 闪烁状态
        self.alert_history: list = []  # 警报历史记录

        # 自动启动相关（从终端传入的配置）
        self._auto_start_mode: Optional[str] = None  # 'camera' 或 'video'
        self._auto_start_camera_index: int = 0
        self._auto_start_video_path: Optional[str] = None

        # 初始化GUI组件
        self._setup_window()
        self._setup_icon()
        self._create_widgets()
        self._bind_events()

        # 确保初始几何形状
        self.root.after_idle(self._ensure_initial_geometry)

    def _setup_fonts(self) -> None:
        """配置字体和样式 - 从配置文件加载，支持跨平台"""
        # 使用 FontLoader 从配置文件加载字体设置
        # 配置文件位置: config/gui_fonts.yaml
        self.font_loader = FontLoader()
        
        # 获取当前平台的主字体族（自动回退到备用字体）
        self.font_family = self.font_loader.get_font_family()
        
        # 获取所有字体配置（从配置文件加载）
        self.fonts = self.font_loader.get_all_fonts()
        
        # 获取标题颜色（用于艺术标题）
        self.title_color = self.font_loader.get_title_color()
        
        print(f"✓ 字体配置已加载 (平台: {self.font_loader.get_platform()}, 字体: {self.font_family})")

        # 配置ttk样式
        style = ttk.Style()
        style.configure(".", font=self.fonts["normal"])
        style.configure("TButton", font=self.fonts["normal"], padding=(12, 6))
        style.configure("TLabel", font=self.fonts["normal"])
        style.configure("TLabelframe", padding=15)
        style.configure("TLabelframe.Label", font=self.fonts["title"])

        # 自定义按钮样式
        style.configure("Action.TButton", font=self.fonts["normal"], padding=(15, 8))

    def _setup_window(self) -> None:
        """配置窗口基本属性"""
        center_x = int((self.screen_width - self.target_width) / 2)
        center_y = int((self.screen_height - self.target_height) / 2)
        geometry = f"{self.target_width}x{self.target_height}+{center_x}+{center_y}"
        self.root.geometry(geometry)
        self.root.resizable(True, True)
        min_height = int(800 / self.aspect_ratio)
        self.root.minsize(800, min_height)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def _setup_icon(self) -> None:
        """设置窗口图标"""
        try:
            icon_path = os.path.join(os.path.dirname(__file__), "kawaii_icon.png")
            icon = Image.open(icon_path)
            icon = icon.resize((64, 64), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(icon)
            self.root.wm_iconphoto(True, photo)
            self._icon_photo = photo
        except Exception as e:
            print(f"⚠️  图标加载失败: {e}")

    def _center_window(self, window: tk.Toplevel, width: int, height: int) -> None:
        """将窗口居中显示"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        center_x = int((screen_width - width) / 2)
        center_y = int((screen_height - height) / 2)
        window.geometry(f"{width}x{height}+{center_x}+{center_y}")

    def _create_widgets(self) -> None:
        """创建所有GUI组件"""
        # 创建主框架（减小padding让内容更饱满）
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)  # 视频区域可扩展
        self.main_frame.grid_columnconfigure(0, weight=1)

        # 创建顶部标题区域（Logo + 标题）
        self._create_header()

        # 创建视频和警报的水平容器
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)

        # 创建视频显示区域（左侧）
        self._create_video_frame()

        # 创建警报面板（右侧）
        self._create_alert_frame()

        # 创建进度条区域
        self._create_progress_bar()

        # 创建控制按钮区域
        self._create_control_buttons()

    def _create_header(self) -> None:
        """创建顶部标题区域（Logo + 艺术标题）"""
        header_frame = ttk.Frame(self.main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        header_frame.grid_columnconfigure(1, weight=1)

        # Logo占位区域（左侧）
        self.logo_frame = ttk.Frame(header_frame, width=80, height=80)
        self.logo_frame.grid(row=0, column=0, padx=(10, 20))
        self.logo_frame.grid_propagate(False)

        # 尝试加载Logo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "logo.png")
            if os.path.exists(logo_path):
                logo_img = Image.open(logo_path)
                logo_img = logo_img.resize((70, 70), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_img)
                logo_label = ttk.Label(self.logo_frame, image=self.logo_photo)
                logo_label.place(relx=0.5, rely=0.5, anchor="center")
            else:
                # 显示占位符
                placeholder = tk.Label(
                    self.logo_frame,
                    text="🎯",
                    font=(self.font_family, 36),
                    bg="#f0f0f0",
                )
                placeholder.place(relx=0.5, rely=0.5, anchor="center")
        except Exception as e:
            print(f"Logo加载失败: {e}")
            placeholder = tk.Label(
                self.logo_frame, text="🎯", font=(self.font_family, 36)
            )
            placeholder.place(relx=0.5, rely=0.5, anchor="center")

        # 艺术标题（中间）- 使用配置文件中的字体和颜色
        self.title_label = ttk.Label(
            header_frame,
            text="DLC：支持语义客制化的智能养老摄像头",
            font=self.fonts["header"],
            foreground=self.title_color,  # 从配置文件读取颜色
        )
        self.title_label.grid(row=0, column=1, sticky="w")

    def _create_video_frame(self) -> None:
        """创建视频显示区域（左侧）"""
        # 视频区域容器
        self.video_frame = ttk.Frame(self.content_frame, padding="5")
        self.video_frame.pack(side=tk.LEFT, fill=tk.BOTH)

        # 视频预览标签
        video_title = ttk.Label(
            self.video_frame, text="📹 实时视频预览", font=self.fonts["title"]
        )
        video_title.pack(anchor="w", pady=(0, 5))

        # 视频画布 - 使用固定尺寸
        self.video_canvas = tk.Canvas(
            self.video_frame,
            bg="#2b2b2b",
            highlightthickness=2,
            highlightbackground="#4a4a4a",
            width=self.VIDEO_CANVAS_WIDTH,
            height=self.VIDEO_CANVAS_HEIGHT,
        )
        self.video_canvas.pack(padx=5, pady=5)

        # 占位提示文字（初始居中）
        self.placeholder_text = self.video_canvas.create_text(
            self.VIDEO_CANVAS_WIDTH // 2,
            self.VIDEO_CANVAS_HEIGHT // 2,
            text="等待视频输入...\n\n点击下方「开始检测」按钮选择视频源",
            font=(self.font_family, 16, "bold"),
            fill="#888888",
            justify="center",
        )

        # 重播按钮（初始隐藏）
        self.replay_button = None

    def _create_alert_frame(self) -> None:
        """创建警报面板（右侧）"""
        # 警报区域容器
        self.alert_frame = ttk.Frame(self.content_frame, padding="5")
        self.alert_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(10, 0))

        # 警报标题
        alert_title = ttk.Label(
            self.alert_frame, text="🚨 警报信息", font=self.fonts["title"]
        )
        alert_title.pack(anchor="w", pady=(0, 5))

        # 警报画布 - 与视频画布同高
        self.alert_canvas = tk.Canvas(
            self.alert_frame,
            bg="#1a1a2e",
            highlightthickness=3,
            highlightbackground="#3498db",  # 蓝色边框（正常状态）
            width=self.ALERT_PANEL_WIDTH,
            height=self.VIDEO_CANVAS_HEIGHT,
        )
        self.alert_canvas.pack(padx=5, pady=5)

        # 警报标题（顶部居中）
        self.alert_title = self.alert_canvas.create_text(
            self.ALERT_PANEL_WIDTH // 2,
            25,
            text="警报信息",
            font=(self.font_family, 18, "bold"),
            fill="#3498db",
            justify="center",
        )

        # 分隔线
        self.alert_canvas.create_line(
            10, 50, self.ALERT_PANEL_WIDTH - 10, 50, fill="#4a4a4a", width=1
        )

        # 警报内容文字（从顶部开始，左对齐）
        self.alert_text = self.alert_canvas.create_text(
            15,
            65,
            text="暂无警报记录",
            font=(self.font_family, 11, "bold"),
            fill="#3498db",  # 蓝色文字
            justify="left",
            anchor="nw",  # 左上角对齐
            width=self.ALERT_PANEL_WIDTH - 30,  # 文字换行宽度
        )

    def _create_progress_bar(self) -> None:
        """创建进度条区域"""
        progress_frame = ttk.Frame(self.main_frame)
        progress_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 10))
        progress_frame.grid_columnconfigure(1, weight=1)

        # 当前时间标签
        self.time_current_label = ttk.Label(
            progress_frame, text="00:00", font=self.fonts["small"]
        )
        self.time_current_label.grid(row=0, column=0, padx=(0, 10))

        # 进度条
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Scale(
            progress_frame,
            from_=0,
            to=100,
            orient=tk.HORIZONTAL,
            variable=self.progress_var,
            command=self._on_progress_change,
        )
        self.progress_bar.grid(row=0, column=1, sticky="ew")

        # 总时间标签
        self.time_total_label = ttk.Label(
            progress_frame, text="00:00", font=self.fonts["small"]
        )
        self.time_total_label.grid(row=0, column=2, padx=(10, 0))

        # 倍速选择
        ttk.Label(progress_frame, text="倍速:", font=self.fonts["small"]).grid(
            row=0, column=3, padx=(20, 5)
        )
        self.speed_var = tk.StringVar(value="1.0")
        speed_combo = ttk.Combobox(
            progress_frame,
            textvariable=self.speed_var,
            values=["0.25", "0.5", "1.0", "1.5", "2.0"],
            state="readonly",
            width=6,
        )
        speed_combo.grid(row=0, column=4)
        speed_combo.bind("<<ComboboxSelected>>", self._on_speed_change)

    def _create_control_buttons(self) -> None:
        """创建控制按钮"""
        control_frame = ttk.Frame(self.main_frame)
        control_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 10))
        control_frame.grid_columnconfigure(0, weight=1)
        control_frame.grid_columnconfigure(2, weight=1)

        button_container = ttk.Frame(control_frame)
        button_container.grid(row=0, column=1)

        self.btn_start = ttk.Button(
            button_container,
            text="▶ 开始检测",
            width=15,
            command=self._on_start_detection,
            style="Action.TButton",
        )
        self.btn_start.pack(side="left", padx=5)

        self.btn_pause = ttk.Button(
            button_container,
            text="⏸ 暂停",
            width=15,
            command=self._on_pause,
            style="Action.TButton",
        )
        self.btn_pause.pack(side="left", padx=5)

        self.btn_stop = ttk.Button(
            button_container,
            text="⏹ 停止",
            width=15,
            command=self._on_stop,
            style="Action.TButton",
        )
        self.btn_stop.pack(side="left", padx=5)

        self.btn_settings = ttk.Button(
            button_container,
            text="⚙ 设置",
            width=15,
            command=self._on_settings,
            style="Action.TButton",
        )
        self.btn_settings.pack(side="left", padx=5)

    def _bind_events(self) -> None:
        """绑定事件处理器"""
        self.root.bind("<Configure>", self._on_window_resize)
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _update_video_layout(self, window_width: int, window_height: int) -> None:
        """更新视频画布布局 - 保持固定尺寸"""
        # 使用固定的视频画布尺寸
        canvas_width = self.VIDEO_CANVAS_WIDTH
        canvas_height = self.VIDEO_CANVAS_HEIGHT

        self.video_canvas.config(width=canvas_width, height=canvas_height)

        # 更新占位文字位置
        if hasattr(self, "placeholder_text") and self.placeholder_text:
            self.video_canvas.coords(
                self.placeholder_text,
                canvas_width // 2,
                canvas_height // 2,
            )

    def _ensure_initial_geometry(self) -> None:
        """确保窗口以正确的初始尺寸显示"""
        if not self._resize_state["initialized"]:
            self._resize_state["lock"] = True
            center_x = int((self.screen_width - self.target_width) / 2)
            center_y = int((self.screen_height - self.target_height) / 2)
            geometry = f"{self.target_width}x{self.target_height}+{center_x}+{center_y}"
            self.root.geometry(geometry)
            self.root.update_idletasks()

            actual_width = self.root.winfo_width()
            actual_height = self.root.winfo_height()

            self._resize_state.update(
                {
                    "width": actual_width,
                    "height": actual_height,
                    "initialized": True,
                }
            )

            self._update_video_layout(actual_width, actual_height)
            self._resize_state["lock"] = False

    def _on_window_resize(self, event: tk.Event) -> None:
        """窗口缩放事件处理器"""
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

        desired_height = int(new_width / self.aspect_ratio)
        desired_width = int(new_height * self.aspect_ratio)

        width_delta = abs(new_width - self._resize_state["width"])
        height_delta = abs(new_height - self._resize_state["height"])

        if width_delta >= height_delta:
            target_width = new_width
            target_height = max(200, desired_height)
        else:
            target_height = new_height
            target_width = max(320, desired_width)

        self._resize_state["lock"] = True
        self.root.geometry(f"{target_width}x{target_height}")
        self._resize_state["lock"] = False

        self._resize_state["width"] = target_width
        self._resize_state["height"] = target_height
        self._update_video_layout(target_width, target_height)

    # ========== 视频源选择 ==========

    def _on_start_detection(self) -> None:
        """开始检测按钮回调 - 弹出选择对话框"""
        if self.is_playing and not self.is_paused:
            messagebox.showinfo("提示", "视频流已在播放中")
            return

        if self.is_paused:
            self.is_paused = False
            self.btn_pause.config(text="⏸ 暂停")
            print("恢复播放...")
            return

        # 弹出选择对话框：摄像头 or 本地视频
        self._show_source_selection_dialog()

    def _show_source_selection_dialog(self) -> None:
        """显示视频源选择对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("选择视频源")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 设置对话框大小和位置（加宽以容纳按钮文字）
        dialog_width = 450
        dialog_height = 250
        self._center_window(dialog, dialog_width, dialog_height)

        # 内容框架
        content_frame = ttk.Frame(dialog, padding=30)
        content_frame.pack(fill=tk.BOTH, expand=True)

        # 标题
        ttk.Label(
            content_frame, text="请选择视频输入源", font=self.fonts["title"]
        ).pack(pady=(0, 25))

        # 按钮框架
        button_frame = ttk.Frame(content_frame)
        button_frame.pack(fill=tk.X, pady=10)

        # 摄像头按钮（宽度较小）
        def on_camera():
            dialog.destroy()
            self._start_camera_stream()

        camera_btn = ttk.Button(
            button_frame,
            text="📷 摄像头",
            command=on_camera,
            width=12,
            style="Action.TButton",
        )
        camera_btn.pack(side=tk.LEFT, padx=10, expand=True)

        # 本地视频按钮（宽度较大）
        def on_local_video():
            dialog.destroy()
            self._select_local_video()

        video_btn = ttk.Button(
            button_frame,
            text="📁 本地视频上传",
            command=on_local_video,
            width=18,
            style="Action.TButton",
        )
        video_btn.pack(side=tk.LEFT, padx=10, expand=True)

        # 取消按钮
        cancel_btn = ttk.Button(
            content_frame, text="取消", command=dialog.destroy, width=12
        )
        cancel_btn.pack(pady=(20, 0))

        # 绑定ESC键关闭
        dialog.bind("<Escape>", lambda e: dialog.destroy())

    def _select_local_video(self) -> None:
        """选择本地视频文件"""
        file_path = filedialog.askopenfilename(
            title="选择视频文件",
            filetypes=[
                ("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm"),
                ("MP4文件", "*.mp4"),
                ("AVI文件", "*.avi"),
            ],
        )

        if file_path:
            self.current_video_path = file_path
            self.is_local_video = True
            self._start_local_video_stream(file_path)

    def _start_camera_stream(self) -> None:
        """启动摄像头视频流"""
        try:
            self.is_local_video = False
            self.video_finished = False

            # 隐藏重播按钮
            self._hide_replay_button()

            if self.video_capture is not None:
                self.video_capture.release()

            camera_index = int(
                self.app_config.get("camera", {}).get("camera_index", "0")
            )
            print(f"正在打开摄像头 {camera_index}...")
            self.video_capture = cv2.VideoCapture(camera_index)
            self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            if not self.video_capture or not self.video_capture.isOpened():
                messagebox.showerror("错误", "无法打开摄像头，请检查摄像头连接")
                self.video_capture = None
                return

            self.is_playing = True
            self.is_paused = False

            # 清除占位文字
            self.video_canvas.delete("all")
            self.placeholder_text = None

            self._update_video_frame()
            print("✓ 摄像头已启动")

        except Exception as e:
            messagebox.showerror("错误", f"启动摄像头失败:\n{str(e)}")
            print(f"启动摄像头错误: {e}")
            self.is_playing = False

    def _start_local_video_stream(self, video_path: str) -> None:
        """启动本地视频流"""
        try:
            self.is_local_video = True
            self.video_finished = False

            # 隐藏重播按钮
            self._hide_replay_button()

            if self.video_capture is not None:
                self.video_capture.release()

            print(f"正在打开视频: {video_path}")
            self.video_capture = cv2.VideoCapture(video_path)

            if not self.video_capture or not self.video_capture.isOpened():
                messagebox.showerror("错误", f"无法打开视频文件:\n{video_path}")
                self.video_capture = None
                return

            # 获取视频信息
            self.video_total_frames = int(
                self.video_capture.get(cv2.CAP_PROP_FRAME_COUNT)
            )
            self.video_fps = self.video_capture.get(cv2.CAP_PROP_FPS)
            if self.video_fps <= 0:
                self.video_fps = 30.0

            total_seconds = self.video_total_frames / self.video_fps
            self.time_total_label.config(text=self._format_time(total_seconds))
            self.progress_var.set(0)
            self.time_current_label.config(text="00:00")

            self.is_playing = True
            self.is_paused = False
            self.current_frame_pos = 0

            # 清除占位文字
            self.video_canvas.delete("all")
            self.placeholder_text = None

            self._update_video_frame()
            print(
                f"✓ 本地视频已启动: {self.video_total_frames}帧, {self.video_fps:.1f}fps"
            )

        except Exception as e:
            messagebox.showerror("错误", f"启动视频失败:\n{str(e)}")
            print(f"启动视频错误: {e}")
            self.is_playing = False

    def _on_pause(self) -> None:
        """暂停按钮回调"""
        if not self.is_playing:
            messagebox.showinfo("提示", "当前没有视频在播放")
            return

        if self.is_paused:
            self.is_paused = False
            self.btn_pause.config(text="⏸ 暂停")
            print("恢复播放...")
        else:
            self.is_paused = True
            self.btn_pause.config(text="▶ 继续")
            print("暂停播放...")

    def _on_stop(self) -> None:
        """停止按钮回调"""
        if not self.is_playing and not self.video_finished:
            messagebox.showinfo("提示", "当前没有视频在播放")
            return

        print("停止视频流...")
        self._stop_video_stream()

    def _on_settings(self) -> None:
        """设置按钮回调"""
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("DLC检测系统 - 设置")

        settings_width = 1000
        settings_height = 666
        self._center_window(self.settings_window, settings_width, settings_height)

        try:
            icon_path = os.path.join(os.path.dirname(__file__), "kawaii_icon.png")
            icon = Image.open(icon_path)
            icon = icon.resize((64, 64), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(icon)
            self.settings_window.wm_iconphoto(True, photo)
            self._settings_icon_photo = photo
        except Exception as e:
            print(f"⚠️  设置窗口图标加载失败: {e}")

        self.settings_panel = SettingsPanel(self.settings_window, self.app_config)
        
        # 注册场景变化回调（用于检测器热重载）
        self.settings_panel.set_scenarios_changed_callback(self._reload_detector_scenarios)

        # 启动场景变化监听器
        if self.config_updater:
            self.settings_panel.start_config_monitor(
                callback=self._on_scene_config_change,
                interval=500,  # 每500ms检查一次
                print_changes=True,  # 打印变化信息
                print_full_config=False,  # 不打印完整配置
            )

        def on_settings_close():
            # 停止监听器
            if self.settings_panel:
                self.settings_panel.stop_config_monitor()
            self.settings_window.destroy()
            self.settings_window = None
            self.settings_panel = None

        self.settings_window.protocol("WM_DELETE_WINDOW", on_settings_close)

    def _stop_video_stream(self) -> None:
        """停止视频流"""
        try:
            self.is_playing = False
            self.is_paused = False
            self.video_finished = False
            self.btn_pause.config(text="⏸ 暂停")

            if self.update_id is not None:
                self.root.after_cancel(self.update_id)
                self.update_id = None

            if self.video_capture is not None:
                self.video_capture.release()
                self.video_capture = None

            # 隐藏重播按钮
            self._hide_replay_button()

            # 清空画布并显示占位文字
            self.video_canvas.delete("all")
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            self.placeholder_text = self.video_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="等待视频输入...\n\n点击下方「开始检测」按钮选择视频源",
                font=(self.font_family, 16, "bold"),
                fill="#888888",
                justify="center",
            )

            # 重置进度条
            self.progress_var.set(0)
            self.time_current_label.config(text="00:00")
            self.time_total_label.config(text="00:00")

            print("✓ 视频流已停止")

        except Exception as e:
            print(f"停止视频流错误: {e}")

    def _update_video_frame(self) -> None:
        """更新视频帧"""
        if not self.is_playing or self.video_capture is None:
            return

        try:
            if not self.is_paused:
                ret, frame = self.video_capture.read()

                if ret:
                    # BGR → RGB 转换
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # CLIP检测（如果有detector）
                    if hasattr(self, "detector") and self.detector:
                        import time

                        current_time = time.time()
                        if (
                            current_time - self.last_detect_time
                            >= self.extract_interval
                        ):
                            self.last_detect_time = current_time
                            try:
                                result = self.detector.detect(frame_rgb, current_time)
                                if result.get("detected", False):
                                    print(
                                        f"⚠️  检测到: {result['scenario_name']} (置信度: {result['confidence']:.2%})"
                                    )
                                    # 1. 触发警报管理器（保存帧、日志等）
                                    if (
                                        hasattr(self, "alert_manager")
                                        and self.alert_manager
                                    ):
                                        self.alert_manager.trigger_alert(
                                            result, frame_rgb
                                        )
                                    # 2. 更新 GUI 警报显示面板
                                    self.trigger_alert_with_result(result)
                            except Exception as e:
                                print(f"检测错误: {e}")

                    # 更新进度条（仅本地视频）
                    if self.is_local_video and self.video_total_frames > 0:
                        self.current_frame_pos = int(
                            self.video_capture.get(cv2.CAP_PROP_POS_FRAMES)
                        )
                        progress = (
                            self.current_frame_pos / self.video_total_frames
                        ) * 100
                        self.progress_var.set(progress)

                        current_seconds = self.current_frame_pos / self.video_fps
                        self.time_current_label.config(
                            text=self._format_time(current_seconds)
                        )

                    # 获取画布尺寸
                    canvas_width = self.video_canvas.winfo_width()
                    canvas_height = self.video_canvas.winfo_height()

                    # 调整帧大小
                    frame_resized = self._resize_frame(
                        frame_rgb, canvas_width, canvas_height
                    )

                    # 转换为PIL图像 → ImageTk
                    image = Image.fromarray(frame_resized)
                    photo = ImageTk.PhotoImage(image=image)

                    # 显示图像
                    self.video_canvas.delete("all")
                    self.video_canvas.create_image(
                        canvas_width // 2,
                        canvas_height // 2,
                        image=photo,
                        anchor=tk.CENTER,
                    )
                    self.video_canvas.image = photo

                else:
                    # 视频结束或读取失败
                    if self.is_local_video:
                        print("本地视频播放完毕")
                        self._on_video_finished()
                        return
                    else:
                        print("摄像头流读取失败")
                        self._stop_video_stream()
                        messagebox.showwarning("警告", "视频流连接中断")
                        return

            # 计算下一帧延时（考虑倍速）
            self.playback_speed = float(self.speed_var.get())
            delay = (
                int(1000 / (self.video_fps * self.playback_speed))
                if self.is_local_video
                else 17
            )
            delay = max(1, delay)  # 最小1ms

            self.update_id = self.root.after(delay, self._update_video_frame)

        except Exception as e:
            print(f"更新视频帧错误: {e}")
            self._stop_video_stream()
            messagebox.showerror("错误", f"视频播放出错:\n{str(e)}")

    def _on_video_finished(self) -> None:
        """视频播放完毕处理"""
        self.is_playing = False
        self.video_finished = True

        if self.update_id is not None:
            self.root.after_cancel(self.update_id)
            self.update_id = None

        # 检查是否循环播放
        if self.app_config.get("video", {}).get("loop_play", False):
            print("循环播放...")
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.is_playing = True
            self.video_finished = False
            self._update_video_frame()
        else:
            # 显示重播按钮
            self._show_replay_button()

    def _show_replay_button(self) -> None:
        """显示重播按钮"""
        canvas_width = self.video_canvas.winfo_width()
        canvas_height = self.video_canvas.winfo_height()

        # 创建重播按钮 - 深蓝灰色半透明底色，黑色文字
        # 注意：Tkinter不支持真正的透明度，使用深蓝灰色模拟
        self.replay_button = tk.Button(
            self.video_canvas,
            text="🔄 重新播放",
            font=self.fonts["replay"],
            bg="#4a5568",  # 深蓝灰色
            fg="#1a1a1a",  # 黑色文字
            activebackground="#5a6578",  # 悬停时稍亮
            activeforeground="#1a1a1a",  # 悬停时黑色文字
            relief=tk.FLAT,
            cursor="hand2",
            padx=20,
            pady=10,
            command=self._on_replay,
        )

        # 放置在画布中央
        self.video_canvas.create_window(
            canvas_width // 2,
            canvas_height // 2,
            window=self.replay_button,
            tags="replay_btn",
        )

    def _hide_replay_button(self) -> None:
        """隐藏重播按钮"""
        if self.replay_button:
            self.replay_button.destroy()
            self.replay_button = None
        self.video_canvas.delete("replay_btn")

    def _on_replay(self) -> None:
        """重播按钮回调"""
        if self.current_video_path and self.is_local_video:
            self._start_local_video_stream(self.current_video_path)

    def _on_progress_change(self, value) -> None:
        """进度条拖动回调"""
        if self.is_local_video and self.video_capture and self.video_total_frames > 0:
            progress = float(value)
            target_frame = int((progress / 100) * self.video_total_frames)
            self.video_capture.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

            current_seconds = target_frame / self.video_fps
            self.time_current_label.config(text=self._format_time(current_seconds))

    def _on_speed_change(self, event=None) -> None:
        """倍速改变回调"""
        self.playback_speed = float(self.speed_var.get())
        print(f"播放倍速: {self.playback_speed}x")

    def _format_time(self, seconds: float) -> str:
        """格式化时间为 MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def _resize_frame(
        self, frame: np.ndarray, canvas_width: int, canvas_height: int
    ) -> np.ndarray:
        """
        调整视频帧大小以适应画布，保持宽高比

        Args:
            frame: 原始视频帧
            canvas_width: 画布宽度
            canvas_height: 画布高度

        Returns:
            调整后的视频帧
        """
        frame_height, frame_width = frame.shape[:2]

        # 计算缩放比例
        width_ratio = canvas_width / frame_width
        height_ratio = canvas_height / frame_height
        scale_ratio = min(width_ratio, height_ratio)

        # 计算新尺寸
        new_width = int(frame_width * scale_ratio)
        new_height = int(frame_height * scale_ratio)

        # 调整大小
        resized_frame = cv2.resize(
            frame, (new_width, new_height), interpolation=cv2.INTER_AREA
        )

        # 创建黑色背景
        output = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)

        # 计算居中位置
        y_offset = (canvas_height - new_height) // 2
        x_offset = (canvas_width - new_width) // 2

        # 将调整后的帧放置在中心
        output[y_offset : y_offset + new_height, x_offset : x_offset + new_width] = (
            resized_frame
        )

        return output

    def _on_window_close(self) -> None:
        """窗口关闭事件处理器"""
        try:
            # 停止视频流
            self._stop_video_stream()

            # 关闭窗口
            self.root.quit()
            self.root.destroy()
        finally:
            sys.exit(0)

    def set_video_stream(self, video_stream):
        """设置视频流（从main.py传入）"""
        self.video_stream = video_stream
        # 设置抽帧间隔
        if video_stream and hasattr(video_stream, "extract_interval"):
            self.extract_interval = video_stream.extract_interval
            print(f"✓ 设置检测间隔: {self.extract_interval}秒/帧")

    def set_detector(self, detector):
        """设置检测器（从main.py传入）"""
        self.detector = detector

    def set_alert_manager(self, alert_manager):
        """设置警报管理器（从main.py传入）"""
        self.alert_manager = alert_manager

    def _on_scene_config_change(self, old_config: Dict, new_config: Dict) -> None:
        """
        场景配置变化时的回调函数（增量更新配置文件 + 热重载检测器）

        Args:
            old_config: 旧配置
            new_config: 新配置
        """
        # 检查选中场景是否变化
        old_scenes = set(old_config.get("selected_scenes", []))
        new_scenes = set(new_config.get("selected_scenes", []))

        if old_scenes != new_scenes:
            # 获取所有可用场景
            if self.settings_panel:
                all_scenes = self.settings_panel.get_all_scene_types()

                # 优先使用 settings_panel 中复用的 config_updater
                config_updater = self.settings_panel.get_config_updater()
                if config_updater is None:
                    config_updater = self.config_updater
                
                # 增量更新配置文件（只修改 enabled 字段）
                if config_updater:
                    config_updater.update_scenarios(
                        all_scenes=all_scenes, selected_scenes=sorted(new_scenes)
                    )
                
                # 通知检测器重新加载场景配置（热重载）
                self._reload_detector_scenarios()

    def _reload_detector_scenarios(self) -> None:
        """
        通知检测器热重载场景配置
        
        当用户通过 GUI 修改场景配置后，检测器需要重新加载
        以反映最新的场景定义和阈值设置
        """
        if hasattr(self, 'detector') and self.detector is not None:
            try:
                # 调用检测器的热重载方法
                if hasattr(self.detector, 'reload_scenarios'):
                    success = self.detector.reload_scenarios()
                    if success:
                        print("✅ 检测器场景配置已热重载")
                    else:
                        print("⚠️  检测器场景配置热重载失败")
            except Exception as e:
                print(f"⚠️  热重载检测器失败: {e}")

    # ==================== 自动启动方法（终端命令模式） ====================

    def set_auto_start_camera(self, camera_index: int = 0) -> None:
        """
        设置自动启动摄像头模式（终端配置）

        Args:
            camera_index: 摄像头索引
        """
        self._auto_start_mode = "camera"
        self._auto_start_camera_index = camera_index
        print(f"✓ 设置自动启动摄像头模式，索引: {camera_index}")

    def set_auto_start_video(self, video_path: str) -> None:
        """
        设置自动启动视频模式（终端配置）

        Args:
            video_path: 视频文件路径
        """
        self._auto_start_mode = "video"
        self._auto_start_video_path = video_path
        print(f"✓ 设置自动启动视频模式，路径: {video_path}")

    def _execute_auto_start(self) -> None:
        """执行自动启动（在GUI初始化完成后调用）"""
        if self._auto_start_mode == "camera":
            print(f"🎬 自动启动摄像头 (索引: {self._auto_start_camera_index})...")
            # 更新配置中的摄像头索引
            self.app_config["camera"]["camera_index"] = str(
                self._auto_start_camera_index
            )
            # 直接启动摄像头，不弹对话框
            self._start_camera_stream()

        elif self._auto_start_mode == "video" and self._auto_start_video_path:
            print(f"🎬 自动启动视频: {self._auto_start_video_path}...")
            # 直接启动视频，不弹对话框
            self.current_video_path = self._auto_start_video_path
            self.is_local_video = True
            self._start_local_video_stream(self._auto_start_video_path)

    # ==================== 警报相关方法 ====================

    def trigger_alert_with_result(self, result: dict) -> None:
        """
        根据检测结果触发警报，累积显示

        Args:
            result: 检测结果字典，包含 scenario_name, confidence, alert_level 等
        """
        import time

        # 添加时间戳
        alert_record = {
            "time": time.strftime("%H:%M:%S"),
            "scenario_name": result.get("scenario_name", "未知"),
            "confidence": result.get("confidence", 0),
            "alert_level": result.get("alert_level", "medium"),
        }

        # 添加到历史记录（最新的在前面）
        self.alert_history.insert(0, alert_record)

        # 限制历史记录数量（最多保留最新10条）
        if len(self.alert_history) > 10:
            self.alert_history = self.alert_history[:10]

        self.is_alert_active = True
        self._update_alert_display()
        self._start_alert_flash()

    def _delayed_clear_alert(self) -> None:
        """延迟清除警报（已禁用）"""
        pass  # 不再自动清除

    def trigger_alert(self, message: str = "检测到异常，请及时处理！") -> None:
        """
        触发警报 - 显示红色闪烁效果（简单消息版本）

        Args:
            message: 警报信息
        """
        if not self.is_alert_active:
            self.is_alert_active = True
            self.alert_message = message
            self.alert_result = None  # 没有详细结果
            self._update_alert_display()
            self._start_alert_flash()

    def clear_alert(self) -> None:
        """清除警报 - 恢复蓝色正常状态"""
        if self.is_alert_active:
            self.is_alert_active = False
            self._stop_alert_flash()
            self._update_alert_display()

    def _update_alert_display(self) -> None:
        """更新警报显示内容（显示历史记录）"""
        if self.is_alert_active and self.alert_history:
            # 更新标题颜色为红色
            self.alert_canvas.itemconfig(self.alert_title, fill="#e74c3c")

            # 构建警报历史文本
            lines = []

            # 显示最近的警报（最多显示4条）
            for i, record in enumerate(self.alert_history[:4]):
                if i > 0:
                    lines.append("")  # 警报之间空一行
                lines.append(f"警报类型: {record['scenario_name']}")
                lines.append(f"检测时间: {record['time']}")
                lines.append(f"可能性: {record['confidence']:.1%}")

            # 如果有更多记录
            if len(self.alert_history) > 4:
                lines.append("")
                lines.append(f"... 还有 {len(self.alert_history) - 4} 条记录")

            alert_text = "\n".join(lines)

            # 警报状态 - 红色
            self.alert_canvas.itemconfig(
                self.alert_text, text=alert_text, fill="#e74c3c"  # 红色文字
            )
        else:
            # 正常状态 - 蓝色
            self.alert_canvas.itemconfig(self.alert_title, fill="#3498db")
            self.alert_canvas.itemconfig(
                self.alert_text, text="暂无警报记录", fill="#3498db"  # 蓝色文字
            )
            self.alert_canvas.config(highlightbackground="#3498db")  # 蓝色边框

    def _start_alert_flash(self) -> None:
        """开始警报闪烁"""
        self._do_alert_flash()

    def _do_alert_flash(self) -> None:
        """执行警报闪烁效果"""
        if not self.is_alert_active:
            return

        # 切换闪烁状态
        self.alert_flash_state = not self.alert_flash_state

        if self.alert_flash_state:
            # 高亮状态 - 明亮红色
            self.alert_canvas.config(highlightbackground="#ff4444")
            self.alert_canvas.config(bg="#2d1f1f")  # 微红背景
        else:
            # 暗淡状态 - 深红色
            self.alert_canvas.config(highlightbackground="#992222")
            self.alert_canvas.config(bg="#1a1a2e")  # 正常背景

        # 500ms后再次调用（闪烁频率）
        self.alert_flash_id = self.root.after(500, self._do_alert_flash)

    def _stop_alert_flash(self) -> None:
        """停止警报闪烁"""
        if self.alert_flash_id:
            self.root.after_cancel(self.alert_flash_id)
            self.alert_flash_id = None
        self.alert_flash_state = False
        # 恢复正常背景
        self.alert_canvas.config(bg="#1a1a2e")

    def run(self) -> None:
        """运行主窗口"""
        # 如果设置了自动启动模式，延迟执行（等待GUI完全初始化）
        if self._auto_start_mode:
            self.root.after(500, self._execute_auto_start)

        self.root.mainloop()


def main() -> None:
    """程序入口"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
