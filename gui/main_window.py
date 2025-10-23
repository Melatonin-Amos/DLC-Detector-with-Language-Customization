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

import tkinter as tk
# 创建主窗口
root = tk.Tk()
root.title("主窗口 - 实时视频预览与检测")

# 获取屏幕宽高
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# 设置窗口大小为屏幕的 50%
width = int(screen_width * 0.5) 
height = int(screen_height * 0.5)

# 计算居中位置
x = int((screen_width - width) / 2)
y = int((screen_height - height) / 2)

# 设置窗口大小和位置
root.geometry(f"{width}x{height}+{x}+{y}")
#锁定长宽比
root.resizable(False, False)
# 改一个可爱滴图标
root.iconbitmap('kawaii_icon.ico')

root.mainloop()


