# DLC-Detector-with-Language-Customization
这是我们 [工程学导论（ME1221）](https://oc.sjtu.edu.cn/courses/84663) 课程项目的版本管理仓库，本项目旨在实现一个基于CLIP的支持语义客制化的智能养老摄像头模块的硬件支持性开发、后端VLM开发以及前端开发。技术上，我们使用大规模语义预训练的CLIP模型，采用ViT作为视觉编码器，Vanilla Transformer作为语义编码器，zero-shot地进行场景识别，从而实现高度个性化的智能功能。

![DLC全栈技术流程图](./doc_asset/image/DLC.png)

***

## 写在前面：环境配置与基础构建

### 第一步：构建VSCode与Python (Conda)开发环境

请参考[课件](./doc_asset/doc/Python的安装与使用.pptx)完成环境（VSCode + Python（Conda））的配置，若中途遇到问题（比如和C++的编译器发生奇怪的冲突），建议不要着急，描述清楚问题后询问AI。此处感谢[魏煊老师](https://www.acem.sjtu.edu.cn/faculty/weixuan.html)的课程课件，请仅用于参考，勿进行二次传播。

有关python语法，我相信开发相关同学不需要太多学习，若有需要，可以参考[官方文档](https://docs.python.org/zh-cn/3/)以及[菜鸟教程](https://www.runoob.com/python3/python3-tutorial.html)。

### 第二步：完成Github学生认证并开始使用

请参考[这个教程](https://zhuanlan.zhihu.com/p/688730361)完成Github学生认证，之后就会获得Github Copilot的免费使用资格。看起来有些麻烦，但是做完之后能够长久提高你的coding生产力，AI写代码确实是很高效的。值得注意的是，申请很可能不能一遍过，可以针对性再上网搜索不过的原因（比如针对“你为什么不在学校”的问题需要用浏览器功能改定位经纬度之类），相信你遇到的问题总有人遇到过并写过分享。要是实在不行可以在[水源社区有关帖子](https://shuiyuan.sjtu.edu.cn/t/topic/405088)下礼貌询问。

在获得学生权益包之后，就可以在VSCode中下载copilot相关插件，并且开始使用代理模式生成啦。有关可能遇到的Claude不对中国IP开放的问题，可以参考[这个帖子](https://www.xiaohongshu.com/explore/68d10aca000000000b03dcc2?app_platform=android&ignoreEngage=true&app_version=9.3.0&share_from_user_hidden=true&xsec_source=app_share&type=normal&xsec_token=CBCVGWu2SEszJUjiL-Lm3k5EuMaxULXqDBvZOYVc2o-mY=&author_share=1&xhsshare=WeixinSession&shareRedId=ODw5NTc6Oko2NzUyOTgwNjY2OTo3PkdA&apptime=1760021884&share_id=b95fbc0175974ad986e575235df49c27&share_channel=wechat)。有关工程问题，我建议使用Claude Sonnet 4.5，试验下有最好的工程代码表现。

### 第三步：学习Git和Github的使用方法

因为版本管理是码类学生绝对逃不开的一个重要软实力，建议花一个下午的时间沉下心来学习[这个教程](https://www.runoob.com/git/git-tutorial.html)，并且跟着敲一遍，之后就可以直接使用，不会的时候问AI了。
