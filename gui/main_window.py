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
from tkinter import ttk, messagebox
from typing import Dict, Optional
from PIL import Image, ImageTk
import cv2
import numpy as np
from settings_panel import SettingsPanel


class MainWindow:
    """DLC检测系统主窗口类"""

    # 类常量
    VIDEO_RATIO = 16 / 9  # 视频显示比例
    SCREEN_RATIO = 0.7  # 窗口占屏幕比例

    def __init__(self) -> None:  # 没有返回值
        """初始化主窗口"""
        # 面向对象：带self的都是实例变量，不是针对类的而言的
        # 创建主窗口
        self.root = tk.Tk()
        self.root.title("主窗口 - 实时视频")

        # 获取屏幕尺寸
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()

        # 计算窗口尺寸
        self.target_width = int(
            self.screen_width * self.SCREEN_RATIO
        )  # 长乘比例缩放系数
        self.target_height = int(
            self.screen_height * self.SCREEN_RATIO
        )  # 宽乘比例缩放系数
        self.aspect_ratio = self.target_width / self.target_height  # 屏幕长宽比

        # 缩放状态跟踪（创建了一个字典跟踪调整时的状态）
        self._resize_state: Dict[str, any] = {  # 键一定是字符串，值可以任意
            "width": self.target_width,
            "height": self.target_height,
            "lock": False,
            "initialized": False,
        }

        # 设置窗口引用
        self.settings_window: Optional[tk.Toplevel] = None

        # 视频流相关变量
        self.video_capture: Optional[cv2.VideoCapture] = None
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.rtsp_url: str = ""
        self.update_id: Optional[str] = None  # 用于存储after的返回ID

        # 初始化GUI组件，在init时自动调用
        self._setup_window()
        self._setup_icon()
        self._create_widgets()
        self._bind_events()

        # 确保初始几何形状（after_idle是时序控制，所有待处理事件都执行完毕后才会调用_ensure_initial_geometry)
        self.root.after_idle(self._ensure_initial_geometry)

    def _setup_window(self) -> None:
        """配置窗口基本属性"""
        # 计算居中位置
        center_x = int((self.screen_width - self.target_width) / 2)
        center_y = int((self.screen_height - self.target_height) / 2)

        # 设置窗口大小和位置
        geometry = f"{self.target_width}x{self.target_height}+{center_x}+{center_y}"  # 告诉tk长、宽、偏移量
        self.root.geometry(geometry)

        # 允许缩放并设置最小尺寸
        self.root.resizable(True, True)
        min_height = int(800 / self.aspect_ratio)
        self.root.minsize(800, min_height)

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

    def _center_window(self, window: tk.Toplevel, width: int, height: int) -> None:
        """
        将窗口居中显示在屏幕上

        Args:
            window: 要居中的窗口
            width: 窗口宽度
            height: 窗口高度
        """
        # 获取屏幕尺寸
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()

        # 计算居中位置
        center_x = int((screen_width - width) / 2)
        center_y = int((screen_height - height) / 2)

        # 设置窗口位置
        window.geometry(f"{width}x{height}+{center_x}+{center_y}")

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
        if self.is_playing and not self.is_paused:
            messagebox.showinfo("提示", "视频流已在播放中")
            return

        # 如果是暂停状态，则恢复播放
        if self.is_paused:
            self.is_paused = False
            print("恢复播放...")
            return

        # 弹出选择对话框：RTSP流 或 本地摄像头
        choice_dialog = tk.Toplevel(self.root)
        choice_dialog.title("选择视频源")
        choice_dialog.resizable(False, False)

        # 设置窗口大小并居中显示
        dialog_width = 500
        dialog_height = 250
        self._center_window(choice_dialog, dialog_width, dialog_height)

        # 设置为模态窗口
        choice_dialog.transient(self.root)
        choice_dialog.grab_set()

        # 创建选择框架
        frame = ttk.Frame(choice_dialog, padding="30")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="请选择视频源类型:", font=("Arial", 14, "bold")).pack(
            pady=(10, 30)
        )

        # 按钮容器
        button_frame = ttk.Frame(frame)
        button_frame.pack(expand=True, pady=(0, 20))

        def on_camera():
            choice_dialog.destroy()
            self.rtsp_url = "0"  # 使用摄像头ID
            self._start_video_stream()

        def on_rtsp():
            choice_dialog.destroy()
            # 简单对话框获取RTSP URL
            from tkinter import simpledialog

            self.rtsp_url = simpledialog.askstring(
                "RTSP设置",
                "请输入RTSP流地址:",
                initialvalue="rtsp://admin:password@192.168.1.100:554/stream",
            )
            if self.rtsp_url:
                self._start_video_stream()
            else:
                messagebox.showwarning("警告", "未设置RTSP地址")

        ttk.Button(
            button_frame, text="📷 本地摄像头", command=on_camera, width=22, padding=10
        ).pack(side=tk.LEFT, padx=15)

        ttk.Button(
            button_frame, text="📡 RTSP网络流", command=on_rtsp, width=22, padding=10
        ).pack(side=tk.LEFT, padx=15)

    def _on_pause(self) -> None:
        """暂停按钮回调"""
        if not self.is_playing:
            messagebox.showinfo("提示", "当前没有视频在播放")
            return

        if self.is_paused:
            # 恢复播放
            self.is_paused = False
            print("恢复播放...")
        else:
            # 暂停播放
            self.is_paused = True
            print("暂停播放...")

    def _on_stop(self) -> None:
        """停止按钮回调"""
        if not self.is_playing:
            messagebox.showinfo("提示", "当前没有视频在播放")
            return

        print("停止视频流...")
        self._stop_video_stream()

    def _on_settings(self) -> None:
        """设置按钮回调"""
        # 如果设置窗口已经打开，则聚焦到该窗口
        if self.settings_window is not None and self.settings_window.winfo_exists():
            self.settings_window.lift()
            self.settings_window.focus_force()
            return

        # 创建新的设置窗口
        self.settings_window = tk.Toplevel(self.root)
        self.settings_window.title("DLC检测系统 - 设置")

        # 设置窗口尺寸
        settings_width = 1000
        settings_height = 666

        # 计算屏幕中央位置
        screen_width = self.settings_window.winfo_screenwidth()
        screen_height = self.settings_window.winfo_screenheight()
        center_x = int((screen_width - settings_width) / 2)
        center_y = int((screen_height - settings_height) / 2)

        # 设置窗口大小和位置（居中显示）
        self.settings_window.geometry(
            f"{settings_width}x{settings_height}+{center_x}+{center_y}"
        )

        # 设置窗口图标（如果有的话）
        try:
            icon = Image.open("gui/kawaii_icon.png")
            photo = ImageTk.PhotoImage(icon)
            self.settings_window.wm_iconphoto(True, photo)
        except Exception as e:
            print(f"无法加载设置窗口图标: {e}")

        # 创建设置面板
        settings_panel = SettingsPanel(self.settings_window)

        # 窗口关闭时清理引用
        def on_settings_close():
            self.settings_window.destroy()
            self.settings_window = None

        self.settings_window.protocol("WM_DELETE_WINDOW", on_settings_close)

    def _start_video_stream(self) -> None:
        """
        启动视频流

        流程：
        1. OpenCV打开摄像头/RTSP流 (cv2.VideoCapture)
        2. 读取视频帧
        3. BGR → RGB 转换 (cv2.cvtColor)
        4. 转换为 PIL.Image → ImageTk.PhotoImage
        5. Tkinter Canvas 显示图像
        """
        try:
            # 释放之前的视频捕获对象
            if self.video_capture is not None:
                self.video_capture.release()

            # 判断是摄像头还是RTSP流
            if self.rtsp_url == "0":
                # 本地摄像头
                print("正在打开本地摄像头...")
                self.video_capture = cv2.VideoCapture(0)  # 0 表示默认摄像头
            else:
                # RTSP网络流
                print(f"正在连接RTSP流: {self.rtsp_url}")
                self.video_capture = cv2.VideoCapture(self.rtsp_url)

            # 设置缓冲区大小，减少延迟
            self.video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)

            # 检查是否成功打开
            if not self.video_capture.isOpened():
                source_type = "摄像头" if self.rtsp_url == "0" else "RTSP流"
                messagebox.showerror(
                    "错误", f"无法连接到{source_type}:\n{self.rtsp_url}"
                )
                self.video_capture = None
                return

            # 标记为播放状态
            self.is_playing = True
            self.is_paused = False

            # 清除占位文字
            self.video_canvas.delete(self.placeholder_text)

            # 开始更新视频帧
            self._update_video_frame()

            source_type = "本地摄像头" if self.rtsp_url == "0" else "RTSP流"
            print(f"{source_type}已启动")

        except Exception as e:
            messagebox.showerror("错误", f"启动视频流失败:\n{str(e)}")
            print(f"启动视频流错误: {e}")
            self.is_playing = False

    def _stop_video_stream(self) -> None:
        """停止视频流"""
        try:
            self.is_playing = False
            self.is_paused = False

            # 取消定时更新
            if self.update_id is not None:
                self.root.after_cancel(self.update_id)
                self.update_id = None

            # 释放视频捕获对象
            if self.video_capture is not None:
                self.video_capture.release()
                self.video_capture = None

            # 清空画布
            self.video_canvas.delete("all")

            # 重新显示占位文字
            canvas_width = self.video_canvas.winfo_width()
            canvas_height = self.video_canvas.winfo_height()
            self.placeholder_text = self.video_canvas.create_text(
                canvas_width // 2,
                canvas_height // 2,
                text="等待视频输入...\n\n点击下方按钮开始检测",
                font=("Arial", 16),
                fill="#888888",
                justify="center",
            )

            print("视频流已停止")

        except Exception as e:
            print(f"停止视频流错误: {e}")

    def _update_video_frame(self) -> None:
        """
        更新视频帧 - 按照流程图实现

        流程：
        ┌──────────────────┐
        │ 1. 读取视频帧      │ ← ret, frame = video_capture.read()
        └────────┬─────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ 2. BGR → RGB 转换   │ ← cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        └────────┬─────────────┘
                 │
                 ▼
        ┌──────────────────────────┐
        │ 3. 调整大小（保持宽高比） │ ← _resize_frame()
        └────────┬─────────────────┘
                 │
                 ▼
        ┌────────────────────────────────┐
        │ 4. 转换为 PIL.Image → ImageTk │ ← Image.fromarray() → ImageTk.PhotoImage()
        └────────┬───────────────────────┘
                 │
                 ▼
        ┌────────────────────────┐
        │ 5. Canvas 显示图像      │ ← canvas.create_image()
        └────────────────────────┘
        """
        if not self.is_playing or self.video_capture is None:
            return

        try:
            # 如果暂停，则不读取新帧，但继续调度
            if not self.is_paused:
                # ========== 步骤1: 读取视频帧 ==========
                ret, frame = self.video_capture.read()

                if ret:
                    # ========== 步骤2: BGR → RGB 转换 ==========
                    # OpenCV默认使用BGR格式，需要转换为RGB供PIL使用
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # 获取画布尺寸
                    canvas_width = self.video_canvas.winfo_width()
                    canvas_height = self.video_canvas.winfo_height()

                    # ========== 步骤3: 调整帧大小以适应画布 ==========
                    frame_resized = self._resize_frame(
                        frame_rgb, canvas_width, canvas_height
                    )

                    # ========== 步骤4: 转换为PIL图像 → ImageTk ==========
                    # PIL.Image.fromarray() 将numpy数组转换为PIL图像
                    image = Image.fromarray(frame_resized)
                    # ImageTk.PhotoImage() 转换为Tkinter可用的图像格式
                    photo = ImageTk.PhotoImage(image=image)

                    # ========== 步骤5: Tkinter Canvas 显示图像 ==========
                    # 清空画布
                    self.video_canvas.delete("all")
                    # 在画布中心显示图像
                    self.video_canvas.create_image(
                        canvas_width // 2,
                        canvas_height // 2,
                        image=photo,
                        anchor=tk.CENTER,
                    )

                    # 保持引用，防止被Python垃圾回收
                    self.video_canvas.image = photo

                else:
                    # 读取失败，可能是流断开
                    print("视频流读取失败，尝试重新连接...")
                    self._stop_video_stream()
                    messagebox.showwarning("警告", "视频流连接中断")
                    return

            # 继续调度下一帧更新（约30fps，33ms一帧）
            self.update_id = self.root.after(33, self._update_video_frame)

        except Exception as e:
            print(f"更新视频帧错误: {e}")
            self._stop_video_stream()
            messagebox.showerror("错误", f"视频播放出错:\n{str(e)}")

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

    def run(self) -> None:
        """运行主窗口"""
        self.root.mainloop()


def main() -> None:
    """程序入口"""
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
