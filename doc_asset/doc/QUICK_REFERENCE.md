# DLC项目快速参考手册

## 常用命令

### Git操作
```bash
# 创建个人开发分支
git checkout -b [姓名拼音]_dev

# 查看当前分支
git branch

# 从main分支同步更新
git checkout main
git pull origin main
git checkout [姓名拼音]_dev
git merge main

# 提交代码
git add .
git commit -m "feat(module): description"
git push origin [姓名拼音]_dev

# 创建Pull Request
在GitHub网页上操作
```

### Python环境
```bash
# 创建虚拟环境
python -m venv venv
# 或者，我更建议用conda管理
conda create -n dlc python=3.10


# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
# 或者，我更建议用conda管理
conda activate dlc


# 安装依赖
pip install -r requirements.txt

# 退出虚拟环境
deactivate
```

### 项目运行

原信息已经过时，现建议参见[README](../../README.md)中的信息。

## 联系方式

- **项目负责人**: 金抑扬 (JYY)
- **GitHub仓库**: https://github.com/Melatonin-Amos/DLC-Detector-with-Language-Customization

---

**最后更新**: 2025年10月19日
