# DLC-Detector-with-Language-Customization

这是上海交通大学电子信息与电气工程学部（中的计算机学院、自动化与感知学院）的一群大学一年级学生在 [工程学导论（ME1221）](https://oc.sjtu.edu.cn/courses/84663) 课程项目的版本管理仓库，本项目旨在实现一个**基于CLIPs的支持语义客制化的智能养老摄像头模块**的硬件支持性开发、后端VLM开发以及前端开发。技术上，我们使用大规模语义预训练的[CLIP](https://arxiv.org/abs/2103.00020)模型，采用ViT作为视觉编码器，Vanilla Transformer作为语义编码器，进行了zero-shot地进行场景识别，从而实现高度个性化的智能功能。此外，我们使用了SoTA的VLM模型[FG-CLIP 2](https://360cvgroup.github.io/FG-CLIP/)便于在更高难度、算力资源更加充足的非边缘计算情境下应用我们的DLC，我们强烈推荐您在资源不受限的情况下使用**FG-CLIP 2**。



![DLC全栈技术流程图](doc_asset/image/DLCupd.png)

FG-CLIP 2使用了优化的模型架构和更大的参数量达成更高的准确率：

![FG-CLIP2 架构图](doc_asset/image/framework.png)

***

## 快速开始

您可以运行下面的一系列终端代码从而快速地进行环境配置。

首先,请您fork本项目仓库后将项目clone到本地，然后在您期望的项目文件夹中打开终端：

```bash
git clone <repo-url>
cd DLC-Detector-with-Language-Customization
```

接着，配置环境，我们推荐使用[conda](https://anaconda.org/anaconda/conda)进行环境的管理，您也可以使用虚拟环境。

```bash
# 方式一：利用conda创建新环境
conda create -n dlc python=3.10 -y
conda activate dlc


# 方式二：创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows
```
接着，安装依赖：

```bash
pip install -r requirements.txt

# (Optional)设置Gemini API密钥（用于使用CLIP时的中文翻译）
export GEMINI_API_KEY="your_api_key_here"
```

接着，就可以运行我们的项目。值得注意的是，首次运行时会下载CLIP权重文件，可能用时较长；此外，不同的系统在外置摄像头管理上稍有差别，您可以多次尝试不同的`camera.index`（通过argparse传参），从而找到合适您使用场景的摄像头。若您已经确定了所用的摄像头的`index`，可以在[配置文件](config/camera/default.yaml)中修改默认摄像头索引，修改后即可以简单地使用`python main.py mode=camera`运行项目程序。

```bash
# 输入模式一：使用摄像头检测实时视频流中的关键帧（使用原CLIP模型）
python main.py mode=camera camera.index=0 # 也有可能为1/2，请您进行尝试

# 输入模式二：使用既有的检测视频/摄像头视频，检测其中的关键帧
python main.py mode=video video_path=<your_video_path> 
```

若您需要使用FG-CLIP 2模型，可以使用argparse加入`--config-name=config_fgclip`，其他操作同上，如：

```bash
python main.py --config-name=config_fgclip mode=camera camera.index=2
```

详细对比和使用说明请参考 [FG-CLIP集成指南](docs/FG_CLIP_GUIDE.md)。

假如您需要对于报错信息进行调试，可以采用debug模式运行：

```bash
# 打印完整配置信息
python main.py mode=camera debug=true

# 查看更多日志
python main.py mode=camera alert.log.level=DEBUG
```

TODO: 完善后续用于开源的README文件