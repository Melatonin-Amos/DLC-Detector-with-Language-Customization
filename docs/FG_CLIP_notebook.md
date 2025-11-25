# FG-CLIP2 原理介绍

本`.ipynb`文件为金抑扬的个人理解笔记，**最终开源时不作上传**。

![FG-CLIP2架构](../doc_asset/image/framework.png)

**FG-CLIP 2** 是 360 AI Research 团队提出的一种支持**中英双语**、专注于**细粒度（Fine-Grained）**理解的VLM。它旨在解决传统 CLIP 类模型在处理细节属性、空间关系和长文本描述时的不足。该模型基于 Google 最新的 **SigLIP 2** 架构进行改进，采用了独特的“两阶段”训练策略，并引入了专门的细粒度损失函数。

以下是关于其预训练模式、损失函数数学原理以及迁移预测方式的详细介绍。

---

### 一、 预训练模式 (Pre-training Strategy)

FG-CLIP 2 的核心训练理念是**“先全局，后局部”**的分层学习框架。为了让模型既懂大意（Global），又懂细节（Local），训练被划分为两个阶段。

#### 1. 基础架构 (Backbone)
*   **视觉编码器 (Image Encoder):** 采用 [**SigLIP 2**](https://arxiv.org/abs/2502.14786) (ViT-B/L/So400M)。
    *   *改进点：* 引入了**数据自适应分辨率 (Data-Adaptive Resolution)** 策略，根据批次内的最大图片大小动态选择分辨率（如 576, 784, 1024 等），避免了传统缩放带来的形变。
    *   *聚合层：* 使用 MAP (Masked Attention Pooling) 头来聚合特征。
*   **文本编码器 (Text Encoder):**
    *   *改进点：* 将最大输入长度从 64 扩展到 **196** 个 Token，以容纳长文本。
    *   *Tokenizer:* 使用多语言 [Gemma Tokenizer](https://arxiv.org/abs/2507.01006) (256K 词表)，这是其支持强大的中英双语能力的基础。

#### 2. 第一阶段：全局对齐 (Global Alignment)
*   **目标：** 让模型建立基础的图文匹配能力，理解画面的整体语义。
*   **数据：** 这种阶段使用大规模图文对（Image-Text Pairs）。
*   **关键策略：** **双重标题策略 (Dual-Caption Strategy)**。
    *   每张图片不仅使用原始的**短标题 (Short Caption)**，还利用大模型 (LMMs) 生成详细的**长标题 (Long Caption)**。
    *   这种混合训练让模型既能捕捉简洁的语义标签，又能理解复杂的描述性语言。

#### 3. 第二阶段：细粒度学习 (Fine-Grained Learning)
*   **目标：** 在保持全局理解的基础上，强制模型去区分“非常相似但有细微差别”的物体或描述（例如区分“红色的塑料椅子”和“红色的木头椅子”）。
*   **数据：** 引入**区域级 (Region-level)** 数据。
    *   使用 FineHARD 数据集（包含 1200 万图片和 4000 万个边界框）。
    *   每个区域（Bounding Box）都有对应的细粒度描述。
    *   **难负样本 (Hard Negatives):** 这是一个关键点。对于每个正样本描述，系统会生成 10 个“难负样本”（例如改动颜色、数量、动作，但句式结构不变的句子），强迫模型学会“找茬”。

---

### 二、 损失函数详解 (Loss Functions)

在第二阶段，模型同时优化五个损失函数。这是理解 FG-CLIP 2 为什么能做“细粒度”理解的核心。

总损失公式如下：
$$ \mathcal{L} = \lambda_1 \mathcal{L}_{Global} + \lambda_2 \mathcal{L}_{FGV} + \lambda_3 \mathcal{L}_{FGT} + \lambda_4 \mathcal{L}_{CMR} + \lambda_5 \mathcal{L}_{TIC} $$

我们逐项拆解这些数学形式及其含义：

#### 1. 全局对齐损失 ($\mathcal{L}_{Global}$)
这是继承自 SigLIP 的核心损失，用于整图和整段文本的匹配。
*   **形式：** **Sigmoid Loss** (而非 CLIP 传统的 Softmax)。
*   **数学含义：**
    $$ \mathcal{L}_{Global} = - \sum_{(i,j)} \log \sigma(t \cdot I_i \cdot T_j) \cdot z_{ij} + \log(1 - \sigma(t \cdot I_i \cdot T_j)) \cdot (1 - z_{ij}) $$
    其中，$z_{ij}=1$ 表示正样本对，$z_{ij}=-1$ 表示负样本对。
*   **通俗解释：** 传统的 CLIP Softmax 是在“一大堆图片里选出最匹配的那张”。而 SigLIP 的 Sigmoid 策略是**把每一对图文都看作独立的二分类问题**（是匹配？还是不匹配？）。这使得模型在处理大规模数据时更高效，且对负样本的定义更灵活。

#### 2. 细粒度视觉损失 ($\mathcal{L}_{FGV}$) - Fine-Grained Visual
*   **目的：** 让图片中的**局部区域**（Region）与描述该区域的文本对齐。
*   **计算方式：**
    1.  利用 **RoIAlign** (Region of Interest Align) 技术，从图像特征图中“抠”出特定边界框（Bounding Box）内的特征。
    2.  计算这些区域特征与对应短语文本特征的对比学习损失。
*   **作用：** 强迫模型不仅看全图，还要盯着特定的框看，解决了“视觉定位”问题。

#### 3. 细粒度文本损失 ($\mathcal{L}_{FGT}$) - Fine-Grained Textual
*   **目的：** 区分文本中的细微差别。
*   **形式：** 基于难负样本的二分类损失。
*   **操作：** 1 个正样本（正确的描述） vs 10 个合成的难负样本（例如把“两只猫”改成“三只猫”）。模型必须给正样本打高分，给负样本打低分。

#### 4. 跨模态排序损失 ($\mathcal{L}_{CMR}$) - Cross-modal Rank Loss
*   **目的：** 这是一个更严格的约束，要求正样本和难负样本之间必须拉开一个**安全距离（Margin）**。
*   **数学形式：**
    $$ \mathcal{L}_{CMR} = \max (0, S(I, T_k) - S(I, T) + \tau_k) $$
    *   $S(I, T)$：图像 $I$ 和正确文本 $T$ 的相似度（正样本得分）。
    *   $S(I, T_k)$：图像 $I$ 和难负样本文本 $T_k$ 的相似度（负样本得分）。
    *   $\tau_k$：**动态阈值 (Margin)**。
*   **全局阈值同步：** 论文中通过 All-Reduce 操作在所有 GPU 间同步这个 $\tau_k$，计算方式基于上一轮训练的平均相似度差值。
*   **含义：** “做对还不够，还要错得离谱”。它强制正样本的得分必须比负样本高出至少 $\tau_k$ 这么多，否则就要惩罚模型。

#### 5. 文本模态内对比损失 ($\mathcal{L}_{TIC}$) - Textual Intra-modal Contrastive (创新点)
*   **痛点：** 现有的文本编码器往往把含义相近的句子（如“一只狗”和“一只小狗”）编码得几乎一模一样（相似度 > 0.99）。这导致视觉模型很难区分它们。
*   **数学形式：**
    $$ \mathcal{L}_{TIC} = - \sum_{i=1}^{N} \log \frac{1}{\sum_{T_m \in \mathcal{T}_i} \exp(S(T_i, T_m))} $$
*   **机制：**
    1.  **自发掘难负样本：** 在文本模态内部，计算句子间的相似度。
    2.  **过滤：** 过滤掉相似度 > 0.95 的（认为是完全同义，不惩罚）。
    3.  **Top-10 惩罚：** 选取剩下最相似的 10 个句子作为负样本，强迫编码器把它们“推开”。
*   **含义：** **“锐化”文本空间**。强制模型把语义相似但不完全相同的句子在特征空间里分得更开，从而赋予模型更强的辨别力。

---

### 三、 迁移使用与预测计算 (Transfer & Prediction)

FG-CLIP 2 训练完成后，可以用于多种下游任务。其预测时的计算方式根据任务类型分为“全局检索”和“密集预测”两类。

#### 1. 零样本分类与检索 (Zero-Shot Classification / Retrieval)
这与标准 CLIP 用法一致，属于**全局对齐**应用。
*   **输入：** 一张整图 $I$ 和一组候选文本 $T = \{t_1, t_2, ..., t_N\}$（例如类别名称“猫”、“狗”...）。
*   **计算：**
    1.  提取整图特征 $V_{global}$。
    2.  提取所有文本特征 $E_{text}$。
    3.  **点积相似度：** $Score = V_{global} \cdot E_{text}^T$。
    4.  取最大值对应的类别或文本。

#### 2. 开放词汇目标检测 (Open-Vocabulary Object Detection, OVD)
这是 FG-CLIP 2 的强项，属于**密集/局部预测**。论文提出了一种**“融合校准” (Fusion Strategy)** 策略，通常结合一个基础检测器（如 LLMDet）。

*   **流程：**
    1.  **检测器生成：** 基础检测器（LLMDet）先生成一系列候选框（Bounding Boxes, $B$）和基础置信度（$Conf_{det}$）。
    2.  **FG-CLIP 2 评分 (Recalibration)：**
        *   对每个候选框 $B_i$，使用 FG-CLIP 2 的视觉编码器 + **RoIAlign** 提取该区域的局部视觉特征 $V_{region}$。
        *   将候选类别名称（如 "red helmet"）编码为文本特征 $E_{text}$。
        *   计算对齐相似度：$Sim = V_{region} \cdot E_{text}$。
        *   对相似度进行 Softmax 归一化，得到 $P_{align}$。
    3.  **融合计算 (Geometric Averaging)：**
        最终分数是检测器置信度和对齐分数的几何平均：
        $$ Score_{final} = (Conf_{det})^\alpha \cdot (P_{align})^\beta $$
*   **意义：** 这种计算方式利用 FG-CLIP 2 强大的细粒度识别能力，去“修正”或“确认”基础检测器的结果，能够有效剔除误检（例如检测器框出了一块红色，但不知道是头盔还是帽子，FG-CLIP 2 可以通过文本相似度来确认）。

#### 3. 边界框分类 (Bounding Box Classification)
论文为此提出了一个新的 Benchmark (BoxClass-CN)。
*   **计算：** 给定一个 Ground Truth 框，使用 FG-CLIP 2 提取该框的特征，直接与成百上千个类别文本计算相似度，取 Top-1。这纯粹考察模型分辨“这个框里到底是什么”的能力，而不考察“框不框得准”。

### 总结
FG-CLIP 2 的精髓在于：
1.  **架构上**用了 SigLIP 2 和长文本编码器。
2.  **训练上**通过 RoIAlign 和难负样本挖掘，实现了从“整图”到“局部”的跨越。
3.  **数学上**通过 $\mathcal{L}_{CMR}$ 和 $\mathcal{L}_{TIC}$，强制模型在特征空间里把“似是而非”的东西强行拉开距离，解决了多模态模型常见的“语义模糊”问题。
