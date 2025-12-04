#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字体安装脚本

功能：
1. 自动检测当前操作系统
2. 安装 GUI 所需的中文字体
3. 验证字体安装是否成功

支持的系统：
- Windows: 通常无需安装，系统自带微软雅黑
- Linux (Ubuntu/Debian): 安装 Noto CJK 和文泉驿字体
- Linux (CentOS/RHEL/Fedora): 安装 Noto CJK 字体
- macOS: 通常无需安装，系统自带苹方字体

使用方法：
    python scripts/install_fonts.py

    # 仅检查字体（不安装）
    python scripts/install_fonts.py --check

    # 强制安装（即使字体已存在）
    python scripts/install_fonts.py --force
"""

import os
import sys
import platform
import subprocess
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_platform_info():
    """获取平台信息"""
    system = platform.system().lower()
    
    if system == "windows":
        return "windows", None
    elif system == "darwin":
        return "macos", None
    else:
        # Linux - 检测发行版
        try:
            with open("/etc/os-release", "r") as f:
                content = f.read().lower()
                if "ubuntu" in content or "debian" in content:
                    return "linux", "debian"
                elif "centos" in content or "rhel" in content or "fedora" in content:
                    return "linux", "rhel"
                elif "arch" in content:
                    return "linux", "arch"
        except FileNotFoundError:
            pass
        return "linux", "debian"  # 默认使用 Debian 系列命令


def check_fonts_available():
    """检查所需字体是否可用"""
    try:
        import tkinter as tk
        from tkinter import font as tkfont
        
        root = tk.Tk()
        root.withdraw()
        available = set(tkfont.families())
        root.destroy()
        
        system, _ = get_platform_info()
        
        # 定义各平台需要检查的字体
        required_fonts = {
            "windows": ["Microsoft YaHei", "SimHei"],
            "linux": ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "WenQuanYi Micro Hei"],
            "macos": ["PingFang SC", "Heiti SC"],
        }
        
        fonts_to_check = required_fonts.get(system, [])
        found_fonts = []
        missing_fonts = []
        
        for font in fonts_to_check:
            if font in available:
                found_fonts.append(font)
            else:
                missing_fonts.append(font)
        
        return {
            "system": system,
            "found": found_fonts,
            "missing": missing_fonts,
            "all_available": available,
        }
    except ImportError:
        print("⚠️  无法导入 tkinter，无法检查字体")
        return None


def install_fonts_linux_debian():
    """在 Debian/Ubuntu 系统上安装字体"""
    print("\n📦 安装 Linux (Debian/Ubuntu) 中文字体...")
    
    packages = [
        "fonts-noto-cjk",           # Google Noto CJK 字体
        "fonts-noto-cjk-extra",     # Noto CJK 额外字体
        "fonts-wqy-zenhei",         # 文泉驿正黑
        "fonts-wqy-microhei",       # 文泉驿微米黑
    ]
    
    try:
        # 更新包列表
        print("  更新软件包列表...")
        subprocess.run(["sudo", "apt-get", "update", "-y"], check=True)
        
        # 安装字体包
        for pkg in packages:
            print(f"  安装 {pkg}...")
            subprocess.run(["sudo", "apt-get", "install", "-y", pkg], check=True)
        
        # 刷新字体缓存
        print("  刷新字体缓存...")
        subprocess.run(["fc-cache", "-fv"], check=True)
        
        print("\n✅ 字体安装完成！")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 安装失败: {e}")
        print("\n手动安装命令：")
        print("  sudo apt-get update")
        print(f"  sudo apt-get install -y {' '.join(packages)}")
        print("  fc-cache -fv")
        return False


def install_fonts_linux_rhel():
    """在 CentOS/RHEL/Fedora 系统上安装字体"""
    print("\n📦 安装 Linux (RHEL/CentOS/Fedora) 中文字体...")
    
    packages = [
        "google-noto-sans-cjk-fonts",   # Google Noto CJK 字体
        "google-noto-serif-cjk-fonts",  # Noto Serif CJK 字体
        "wqy-zenhei-fonts",             # 文泉驿正黑
    ]
    
    # 检测使用 dnf 还是 yum
    pkg_manager = "dnf" if os.path.exists("/usr/bin/dnf") else "yum"
    
    try:
        for pkg in packages:
            print(f"  安装 {pkg}...")
            subprocess.run(["sudo", pkg_manager, "install", "-y", pkg], check=True)
        
        # 刷新字体缓存
        print("  刷新字体缓存...")
        subprocess.run(["fc-cache", "-fv"], check=True)
        
        print("\n✅ 字体安装完成！")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 安装失败: {e}")
        print("\n手动安装命令：")
        print(f"  sudo {pkg_manager} install -y {' '.join(packages)}")
        print("  fc-cache -fv")
        return False


def install_fonts_linux_arch():
    """在 Arch Linux 系统上安装字体"""
    print("\n📦 安装 Linux (Arch) 中文字体...")
    
    packages = [
        "noto-fonts-cjk",           # Google Noto CJK 字体
        "wqy-zenhei",               # 文泉驿正黑
        "wqy-microhei",             # 文泉驿微米黑
    ]
    
    try:
        for pkg in packages:
            print(f"  安装 {pkg}...")
            subprocess.run(["sudo", "pacman", "-S", "--noconfirm", pkg], check=True)
        
        # 刷新字体缓存
        print("  刷新字体缓存...")
        subprocess.run(["fc-cache", "-fv"], check=True)
        
        print("\n✅ 字体安装完成！")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 安装失败: {e}")
        print("\n手动安装命令：")
        print(f"  sudo pacman -S {' '.join(packages)}")
        print("  fc-cache -fv")
        return False


def install_fonts_macos():
    """在 macOS 上检查/安装字体"""
    print("\n🍎 检查 macOS 字体...")
    print("  macOS 通常自带苹方字体（PingFang SC），无需额外安装。")
    print("  如果中文显示异常，可以尝试：")
    print("  1. 打开「字体册」应用")
    print("  2. 检查「苹方」或「PingFang」字体是否已安装")
    print("  3. 如未安装，可从 Apple 官网下载字体包")
    return True


def install_fonts_windows():
    """在 Windows 上检查字体"""
    print("\n🪟 检查 Windows 字体...")
    print("  Windows 通常自带微软雅黑（Microsoft YaHei），无需额外安装。")
    print("  如果中文显示异常，可以尝试：")
    print("  1. 打开「设置」→「个性化」→「字体」")
    print("  2. 搜索「微软雅黑」或「Microsoft YaHei」")
    print("  3. 如未安装，可从 Microsoft 官网下载")
    return True


def install_fonts(force: bool = False):
    """根据系统类型安装字体"""
    system, distro = get_platform_info()
    
    print(f"🖥️  检测到系统: {system}" + (f" ({distro})" if distro else ""))
    
    # 检查是否已安装
    if not force:
        result = check_fonts_available()
        if result and result["found"]:
            print(f"\n✅ 已找到可用字体: {', '.join(result['found'])}")
            if not result["missing"]:
                print("   所有推荐字体都已安装，无需额外操作。")
                return True
            else:
                print(f"⚠️  未找到字体: {', '.join(result['missing'])}")
                print("   将尝试安装...")
    
    # 根据系统安装
    if system == "windows":
        return install_fonts_windows()
    elif system == "macos":
        return install_fonts_macos()
    elif system == "linux":
        if distro == "debian":
            return install_fonts_linux_debian()
        elif distro == "rhel":
            return install_fonts_linux_rhel()
        elif distro == "arch":
            return install_fonts_linux_arch()
        else:
            print("\n⚠️  未知的 Linux 发行版，尝试使用 apt-get...")
            return install_fonts_linux_debian()
    else:
        print(f"\n❌ 不支持的操作系统: {system}")
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="安装 DLC 检测系统 GUI 所需的中文字体"
    )
    parser.add_argument(
        "--check", "-c",
        action="store_true",
        help="仅检查字体，不安装"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="强制安装，即使字体已存在"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🔤 DLC 检测系统 - 字体安装工具")
    print("=" * 50)
    
    if args.check:
        result = check_fonts_available()
        if result:
            print(f"\n系统: {result['system']}")
            print(f"已找到字体: {result['found'] or '无'}")
            print(f"未找到字体: {result['missing'] or '无'}")
            
            if result["found"]:
                print("\n✅ GUI 应该可以正常显示中文")
            else:
                print("\n⚠️  建议运行安装脚本: python scripts/install_fonts.py")
    else:
        success = install_fonts(force=args.force)
        
        if success:
            print("\n" + "=" * 50)
            print("🎉 字体配置完成！")
            print("   请重新启动程序以应用字体设置。")
            print("=" * 50)
        else:
            print("\n" + "=" * 50)
            print("⚠️  字体安装可能未完成")
            print("   请查看上方的手动安装说明。")
            print("=" * 50)
            sys.exit(1)


if __name__ == "__main__":
    main()
